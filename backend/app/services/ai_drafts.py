# Borradores del asistente para un incidente (spec 012): el resumen técnico y el mensaje al cliente. Flujo: se arman los HECHOS reales
# del incidente → el LLM local redacta con un prompt versionado → se verifica el texto (términos del glosario, horas y duración que
# coincidan con los reales) → si la IA no respondió o su texto no pasa, queda el TEXTO BASE determinista para que la persona lo edite
# → la persona aprueba o descarta (principio 6). Las funciones sin base de datos (hechos, verificaciones, textos base) las usa también
# ai/eval/run_eval_borradores.py para medir los prompts con 10 incidentes de prueba.
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.archivos import read_cached
from app.db import release_connection
from app.integrations import ollama
from app.models.ai_draft import AiDraft
from app.models.incident import Incident
from app.models.user import User
from app.services import audit
from app.services.assistant_gate import normalize
from app.services.incident_flow import IncidentFlowError
from app.services.messages import TEMPLATE
from app.services import redaccion
from app.services.sla import BOGOTA

ASSETS = Path(__file__).resolve().parent.parent / "assets"
PROMPT_VERSION = "v1"
KINDS = ("resumen", "mensaje_cliente")
PROMPTS = {"resumen": f"borrador_resumen.{PROMPT_VERSION}.md", "mensaje_cliente": f"borrador_mensaje_cliente.{PROMPT_VERSION}.md"}
ORDER = {
    "resumen": "Redacta el resumen técnico de este incidente.",
    "mensaje_cliente": "Redacta el mensaje para el cliente sobre esta falla.",
}
HOUR = re.compile(r"\b([01]?\d|2[0-3]):([0-5]\d)\b")
MINUTES = re.compile(r"\b(\d+)\s*minutos?\b")


class DraftError(Exception):
    """No se puede aplicar la acción sobre el borrador (estado, texto con jerga u horas que no coinciden)."""


@dataclass(frozen=True)
class Facts:
    """Lo que el Hub sabe del incidente, y lo único que el LLM puede afirmar."""

    cliente: str
    servicio: str
    prioridad: str
    titulo: str
    origen: str  # alerta | manual
    inicio: datetime
    mitigacion: datetime
    cierre: datetime | None = None
    causa: str | None = None
    version_de: str | None = None
    version_a: str | None = None
    eventos: tuple[tuple[str, str, str], ...] = field(default_factory=tuple)  # (HH:MM, tipo, mensaje)


def _utc(valor: datetime) -> datetime:
    return valor.replace(tzinfo=timezone.utc) if valor.tzinfo is None else valor


def hhmm(valor: datetime) -> str:
    """Hora de Colombia al minuto (igual que el mensaje determinista de la spec 009)."""
    return _utc(valor).astimezone(BOGOTA).strftime("%H:%M")


def _to_minute(valor: datetime) -> datetime:
    return _utc(valor).astimezone(BOGOTA).replace(second=0, microsecond=0)


def duration_minutes(h: Facts) -> int:
    """Minutos entre las horas que se muestran (14:00 → 14:07 son 7), para que el texto no se contradiga."""
    return int((_to_minute(h.mitigacion) - _to_minute(h.inicio)).total_seconds() // 60)


def duration_text(minutos: int) -> str:
    if minutos < 1:
        return "menos de 1 minuto"
    return "1 minuto" if minutos == 1 else f"{minutos} minutos"


def facts_for(incident: Incident) -> Facts:
    """Hechos reales de un incidente ya mitigado; falla si todavía no lo está."""
    if incident.mitigated_at is None:
        raise IncidentFlowError("Los borradores se generan cuando el incidente está mitigado.")
    servicio = incident.service
    cliente = servicio.project.client.name if servicio.project is not None and servicio.project.client is not None else "el cliente"
    # Spec 020: las notas del equipo pueden traer una clave pegada; se tapa antes de dársela al modelo
    eventos = tuple((hhmm(e.created_at), e.type, redaccion.redact((e.message or "")[:200])[0]) for e in incident.events if e.created_at is not None)
    return Facts(
        cliente=cliente, servicio=servicio.name, prioridad=incident.priority, titulo=incident.title, origen=incident.source,
        inicio=incident.started_at, mitigacion=incident.mitigated_at, cierre=incident.closed_at, causa=(redaccion.redact(incident.root_cause)[0] if incident.root_cause else None),
        version_de=incident.rollback_from_version, version_a=incident.rollback_to_version, eventos=eventos,
    )


def model_input(h: Facts, kind: str) -> str:
    """Los HECHOS como líneas «clave: valor». El mensaje al cliente recibe solo lo que el cliente puede conocer."""
    inicio, fin, total = hhmm(h.inicio), hhmm(h.mitigacion), duration_text(duration_minutes(h))
    if kind == "mensaje_cliente":
        return f"hora en que se detectó la falla: {inicio}\nhora en que el servicio volvió a funcionar: {fin}\ntiempo total: {total}"
    lineas = [
        f"cliente: {h.cliente}", f"servicio: {h.servicio}", f"prioridad: {h.prioridad}", f"título: {h.titulo}",
        f"origen: {'alerta del monitoreo' if h.origen == 'alerta' else 'abierto a mano'}",
        f"inicio de la falla: {inicio}", f"servicio recuperado: {fin}", f"tiempo total: {total}",
        f"causa raíz: {h.causa or 'sin registrar'}",
    ]
    if h.version_de and h.version_a:
        lineas.append(f"acción: rollback de la versión {h.version_de} a la {h.version_a}")
    else:
        lineas.append("acción: sin rollback registrado")
    if h.cierre is not None:
        lineas.append(f"cierre del incidente: {hhmm(h.cierre)}")
    lineas += [f"evento {hora} ({tipo}): {mensaje}" for hora, tipo, mensaje in h.eventos if mensaje][:8]
    return "\n".join(lineas)


# ---------- Textos base (la IA no respondió o su texto no pasó las verificaciones) ----------


def base_text(h: Facts, kind: str) -> str:
    """Texto de partida del borrador (mensaje al cliente o resumen) armado solo con los hechos del incidente."""
    inicio, fin, total = hhmm(h.inicio), hhmm(h.mitigacion), duration_text(duration_minutes(h))
    if kind == "mensaje_cliente":
        return TEMPLATE.format(hora=inicio, hora_fin=fin, duracion=total)
    accion = f"Se hizo rollback de la versión {h.version_de} a la {h.version_a}." if h.version_de and h.version_a else "No hay rollback registrado."
    return (
        f"{h.servicio} ({h.cliente}) tuvo una falla {h.prioridad} desde las {inicio} hasta las {fin} ({total}); "
        f"se abrió {'por una alerta del monitoreo' if h.origen == 'alerta' else 'a mano'}. "
        f"Causa raíz: {h.causa or 'sin registrar'}. {accion} Pendiente: confirmar la causa y revisar el mensaje al cliente."
    )


# ---------- Verificaciones ----------


def _normalize_terms(texto: str) -> list[str]:
    return [normalize(t) for t in texto.splitlines() if t.strip() and not t.lstrip().startswith("#")]


def _terms() -> list[str]:
    return read_cached(ASSETS / "terminos_prohibidos.txt", _normalize_terms)


def forbidden_terms_in(texto: str) -> list[str]:
    """Términos técnicos del glosario que aparecen en el texto (palabras completas) y versiones sueltas como «v2»."""
    normal = f" {normalize(texto)} "
    encontrados = [t for t in _terms() if f" {t} " in normal]
    encontrados += re.findall(r"\bv\d+\b", normal.strip())
    return sorted(set(encontrados))


def mismatched_times(texto: str, h: Facts, kind: str) -> list[str]:
    """Horas (y minutos totales, en el mensaje al cliente) del texto que no son las del incidente."""
    if kind == "mensaje_cliente":
        validas = {hhmm(h.inicio), hhmm(h.mitigacion)}
    else:
        validas = {hhmm(h.inicio), hhmm(h.mitigacion)} | ({hhmm(h.cierre)} if h.cierre else set()) | {hora for hora, _, _ in h.eventos}
    malas = [f"{int(a):02d}:{b}" for a, b in HOUR.findall(texto) if f"{int(a):02d}:{b}" not in validas]
    if kind == "mensaje_cliente":
        total = duration_minutes(h)
        malas += [f"{n} minutos" for n in MINUTES.findall(texto) if int(n) != total]
    return malas


def check(texto: str, h: Facts, kind: str) -> dict:
    """Resultado de las verificaciones: lo que el texto trae de más. El resumen interno puede usar jerga; el mensaje al cliente, no."""
    return {
        "terminos_prohibidos": forbidden_terms_in(texto) if kind == "mensaje_cliente" else [],
        "horas_que_no_coinciden": mismatched_times(texto, h, kind),
    }


def _clean(comprobacion: dict) -> bool:
    return not comprobacion["terminos_prohibidos"] and not comprobacion["horas_que_no_coinciden"]


def draft_text(h: Facts, kind: str, transport=None) -> dict:
    """Texto del borrador y de dónde salió: {texto, source, checks, latency_ms, model, prompt_version}. Sin base de datos, para evaluar."""
    prompt = (ASSETS / PROMPTS[kind]).read_text(encoding="utf-8").strip()
    sistema = f"{prompt}\n\nDATOS:\n{model_input(h, kind)}"
    inicio = time.monotonic()
    generado = ollama.chat(sistema, ORDER[kind], transport=transport)
    latencia = int((time.monotonic() - inicio) * 1000)
    comprobacion = check(generado, h, kind) if generado else {"terminos_prohibidos": [], "horas_que_no_coinciden": []}
    if generado and _clean(comprobacion):
        return {"texto": generado.strip(), "source": "llm", "checks": {**comprobacion, "motivo_texto_base": None},
                "latency_ms": latencia, "model": settings.ollama_model, "prompt_version": PROMPT_VERSION}
    motivo = "La IA no respondió a tiempo." if not generado else "El texto de la IA no pasó las verificaciones (términos técnicos u horas que no coinciden)."
    return {"texto": base_text(h, kind), "source": "plantilla", "checks": {**comprobacion, "motivo_texto_base": motivo, "texto_rechazado": generado},
            "latency_ms": latencia if generado is not None else None, "model": settings.ollama_model if generado else None,
            "prompt_version": PROMPT_VERSION if generado else None}


# ---------- Con base de datos ----------


def generate(db: Session, incident: Incident, kinds: tuple[str, ...] = KINDS, transport=None) -> list[AiDraft]:
    """Genera los borradores pedidos; los borradores anteriores sin aprobar del mismo tipo se descartan. Hace commit."""
    h = facts_for(incident)
    incident_id = incident.id   # antes de soltar la conexión: ese paso caduca los objetos cargados
    # Primero se redacta todo (cada texto espera a Ollama hasta un minuto) sin una conexión tomada, y después se escribe (auditoría BE-02)
    release_connection(db)
    redactados = {kind: draft_text(h, kind, transport=transport) for kind in kinds}
    nuevos: list[AiDraft] = []
    for kind in kinds:
        for anterior in db.scalars(select(AiDraft).where(AiDraft.incident_id == incident_id, AiDraft.kind == kind, AiDraft.status == "borrador_ia")):
            anterior.status = "descartado"
        r = redactados[kind]
        borrador = AiDraft(
            incident_id=incident_id, kind=kind, status="borrador_ia", source=r["source"], model=r["model"], prompt_version=r["prompt_version"],
            generated_text=r["texto"], checks=r["checks"], latency_ms=r["latency_ms"],
        )
        db.add(borrador)
        nuevos.append(borrador)
    db.commit()
    for b in nuevos:
        db.refresh(b)
    return nuevos


def approve(db: Session, borrador: AiDraft, user: User, texto: str | None, ip: str | None = None) -> AiDraft:
    """Aprueba el borrador (con el texto que la persona editó). El mensaje al cliente no puede traer jerga ni horas que no coincidan."""
    if borrador.status != "borrador_ia":
        raise DraftError("Este borrador ya no está pendiente de aprobación.")
    final = (texto if texto is not None else borrador.generated_text).strip()
    if not final:
        raise DraftError("El texto no puede quedar vacío.")
    if borrador.kind == "mensaje_cliente":
        h = facts_for(db.get(Incident, borrador.incident_id))
        comprobacion = check(final, h, "mensaje_cliente")
        if comprobacion["terminos_prohibidos"]:
            raise DraftError(f"El mensaje al cliente usa términos técnicos que el cliente no debe ver: {', '.join(comprobacion['terminos_prohibidos'])}.")
        if comprobacion["horas_que_no_coinciden"]:
            raise DraftError(f"El mensaje trae horas o tiempos que no son los del incidente: {', '.join(comprobacion['horas_que_no_coinciden'])}.")
    borrador.status = "aprobado"
    borrador.final_text = final
    borrador.approved_by_id = user.id
    borrador.approved_at = datetime.now(timezone.utc)
    audit.record(
        db, user, "ai_draft.aprobar", "ai_draft", borrador.id,
        {"incidente": borrador.incident_id, "tipo": borrador.kind, "fuente": borrador.source, "editado": final != borrador.generated_text}, ip,
    )
    db.commit()
    db.refresh(borrador)
    return borrador


def discard(db: Session, borrador: AiDraft, user: User, ip: str | None = None) -> AiDraft:
    """Descarta un borrador pendiente y lo deja en la bitácora."""
    if borrador.status != "borrador_ia":
        raise DraftError("Este borrador ya no está pendiente de aprobación.")
    borrador.status = "descartado"
    audit.record(db, user, "ai_draft.descartar", "ai_draft", borrador.id, {"incidente": borrador.incident_id, "tipo": borrador.kind}, ip)
    db.commit()
    db.refresh(borrador)
    return borrador


def approved_message(db: Session, incident_id: int) -> str | None:
    """El último mensaje al cliente aprobado de un incidente: lo único de la IA que llega al portal del cliente."""
    return db.scalar(
        select(AiDraft.final_text)
        .where(AiDraft.incident_id == incident_id, AiDraft.kind == "mensaje_cliente", AiDraft.status == "aprobado")
        .order_by(AiDraft.approved_at.desc(), AiDraft.id.desc())
        .limit(1)
    )

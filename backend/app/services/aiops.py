# Diagnóstico con IA local (spec 019, T05; AIOps del módulo 4): reúne evidencia REAL de un incidente (métricas de Prometheus, registros de Loki y lo que la
# persona aporte), se la da a la IA local para que proponga hipótesis y un borrador de runbook, y VERIFICA el texto antes de mostrarlo:
#   · cada cita [E#] debe existir en la evidencia (el modelo no puede inventar fuentes) y, si hay evidencia además del incidente, debe citar al menos una
#   · no puede proponer cambiar el clúster a mano (principios 3 y 5: todo entra por Git y el rollback va por el Hub)
# Si la IA no responde o su texto no pasa, queda un texto base determinista con la evidencia y el runbook que corresponde. Es un borrador (`ai_drafts`, tipo
# `diagnostico`) que una persona edita y aprueba (principio 6); nada se ejecuta. Los datos de clientes no salen del laboratorio: Ollama corre local.
import re
import time
from dataclasses import dataclass
from datetime import timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.integrations import loki, ollama, prometheus
from app.models.ai_draft import AiDraft
from app.models.incident import Incident
from app.services.ai_drafts import ASSETS, hhmm
from app.services import redaccion

PROMPT_VERSION = "v1"
PROMPT = f"diagnostico.{PROMPT_VERSION}.md"
ORDEN = "Propón hipótesis de diagnóstico y un borrador de runbook con la evidencia."
MARCA = "Hipótesis sin confirmar."
MAX_APORTADA = 8
# El diagnóstico (hipótesis, comprobaciones y pasos) es más largo que una respuesta del asistente: 350 tokens lo cortaban a media frase
MAX_TOKENS = 700
MAX_LARGO_APORTADA = 300
CITA = re.compile(r"\[E(\d+)\]")
# Cambios a mano en el clúster, en contenedores o en la base: no se proponen nunca
PROHIBIDOS = re.compile(
    r"\b(kubectl\s+(apply|delete|edit|patch|scale|rollout|replace|set|drain|cordon|exec)|docker\s+(rm|run|exec|stop|kill|restart)|helm\s+(install|upgrade|uninstall)|rm\s+-rf|drop\s+table|psql|escal\w+\s+(temporal|manual)\w*)\b",
    re.IGNORECASE,
)
RUNBOOKS = {"caida": "runbooks/caida-del-sitio.md", "rollback": "runbooks/rollback.md", "saturacion": "runbooks/saturacion.md", "latencia": "runbooks/latencia.md"}


@dataclass(frozen=True)
class Evidencia:
    id: str  # E1, E2…
    tipo: str  # incidente | métrica | registro | aportada
    texto: str


def _cliente(namespace: str) -> str:
    return namespace.removeprefix("cliente-")


def _metricas(namespace: str, clave: str, transport=None) -> list[tuple[str, str]]:
    """(descripción, valor) de lo que Prometheus sabe del namespace ahora; lo que no tenga datos se omite."""
    pods = f'namespace="{namespace}",container!="",container!="POD"'
    consultas = [
        ("disponibilidad del sondeo del /health en los últimos 15 min (1 = siempre sano)", f'avg_over_time(probe_success{{job="sitios",namespace="{namespace}"}}[15m])', "{:.2f}"),
        ("duración media del sondeo del /health en segundos", f'avg(probe_duration_seconds{{job="sitios",namespace="{namespace}"}})', "{:.3f}"),
        ("uso de CPU frente al límite del Pod más cargado (1 = al límite)", f"max(sum by (pod) (rate(container_cpu_usage_seconds_total{{{pods}}}[5m])) / sum by (pod) (container_spec_cpu_quota{{{pods}}} / container_spec_cpu_period{{{pods}}}))", "{:.2f}"),
        ("uso de memoria frente al límite del Pod más cargado (1 = al límite)", f"max(sum by (pod) (container_memory_working_set_bytes{{{pods}}}) / (sum by (pod) (container_spec_memory_limit_bytes{{{pods}}}) > 0))", "{:.2f}"),
        ("reinicios por falta de memoria (OOM) en la última hora", f"sum(increase(container_oom_events_total{{{pods}}}[1h]))", "{:.0f}"),
        ("proporción de respuestas 5xx de Traefik en 5 min", f'sum(rate(traefik_service_requests_total{{service=~"{namespace}-.*",code=~"5.."}}[5m])) / clamp_min(sum(rate(traefik_service_requests_total{{service=~"{namespace}-.*"}}[5m])), 0.001)', "{:.2f}"),
    ]
    salida = []
    for descripcion, promql, formato in consultas:
        valor = prometheus.query(promql, clave, transport)
        if valor is not None:
            salida.append((descripcion, formato.format(valor)))
    return salida


def reunir_evidencia(incident: Incident, aportada: list[str] | None = None, transport_prometheus=None, transport_loki=None) -> list[Evidencia]:
    """E1 siempre es el propio incidente; después las métricas, los registros y lo que la persona aportó (p. ej. datos sintéticos de práctica)."""
    namespace = incident.service.namespace
    textos: list[tuple[str, str]] = [
        ("incidente", f"incidente {incident.priority} «{incident.title}» del servicio {incident.service.name}, abierto {'por una alerta' if incident.source == 'alerta' else 'a mano'} a las {hhmm(incident.started_at)}")
    ]
    if incident.rollback_from_version and incident.rollback_to_version:
        textos.append(("incidente", f"se hizo rollback de la versión {incident.rollback_from_version} a la {incident.rollback_to_version}"))
    textos += [("métrica", f"{descripcion}: {valor}") for descripcion, valor in _metricas(namespace, str(incident.id), transport_prometheus)]
    inicio = incident.started_at if incident.started_at.tzinfo else incident.started_at.replace(tzinfo=timezone.utc)
    desde, hasta = int((inicio.timestamp() - 300) * 1e9), int(time.time() * 1e9)
    textos += [("registro", linea) for linea in loki.lineas(namespace, desde, hasta, transport_loki)[-10:]]
    textos += [("aportada", t.strip()[:MAX_LARGO_APORTADA]) for t in (aportada or [])[:MAX_APORTADA] if t.strip()]
    # Spec 020: un registro o una nota con una clave no viaja al modelo ni se guarda en el borrador
    return [Evidencia(f"E{i}", tipo, redaccion.redactar(texto)[0]) for i, (tipo, texto) in enumerate(textos, start=1)]


def datos_para_el_modelo(evidencia: list[Evidencia]) -> str:
    return "\n".join(f"[{e.id}] ({e.tipo}) {e.texto}" for e in evidencia)


def runbook_sugerido(incident: Incident, evidencia: list[Evidencia]) -> str:
    """Runbook que corresponde según lo que se ve (determinista, sin IA): rollback si lo hubo, saturación si CPU/memoria van al límite, latencia si el sondeo tarda."""
    juntos = " ".join(e.texto for e in evidencia)
    if incident.rollback_from_version:
        return RUNBOOKS["rollback"]
    for descripcion, clave in (("uso de CPU", "saturacion"), ("uso de memoria", "saturacion")):
        m = re.search(rf"{descripcion}[^:]*: ([0-9.]+)", juntos)
        if m and float(m.group(1)) >= 0.9:
            return RUNBOOKS[clave]
    m = re.search(r"duración media del sondeo[^:]*: ([0-9.]+)", juntos)
    if m and float(m.group(1)) >= 1.0:
        return RUNBOOKS["latencia"]
    return RUNBOOKS["caida"]


def texto_base(incident: Incident, evidencia: list[Evidencia]) -> str:
    runbook = runbook_sugerido(incident, evidencia)
    lineas = [f"- [{e.id}] {e.texto}" for e in evidencia]
    return (
        f"{MARCA} La IA no propuso un diagnóstico, así que este es solo el resumen de la evidencia reunida:\n" + "\n".join(lineas)
        + f"\n\nSiguiente paso: seguir el runbook {runbook} (síntoma, diagnóstico, acción y verificación) y registrar la causa raíz en el incidente."
    )


def verificar(texto: str, evidencia: list[Evidencia]) -> dict:
    """Lo que el texto trae de más: citas a evidencia que no existe, falta de citas y propuestas de cambios a mano."""
    ids = {e.id for e in evidencia}
    citadas = {f"E{n}" for n in CITA.findall(texto)}
    return {
        "citas_inexistentes": sorted(citadas - ids, key=lambda c: int(c[1:])),
        "sin_citas": len(evidencia) > 1 and not citadas,
        "comandos_prohibidos": sorted({m.group(0).lower() for m in PROHIBIDOS.finditer(texto)}),
    }


def _limpio(comprobacion: dict) -> bool:
    return not comprobacion["citas_inexistentes"] and not comprobacion["sin_citas"] and not comprobacion["comandos_prohibidos"]


def redactar(incident: Incident, evidencia: list[Evidencia], transport=None) -> dict:
    """Texto del diagnóstico y de dónde salió: {texto, source, checks, latency_ms, model, prompt_version}."""
    sistema = f"{(ASSETS / PROMPT).read_text(encoding='utf-8').strip()}\n\nEVIDENCIA:\n{datos_para_el_modelo(evidencia)}"
    inicio = time.monotonic()
    generado = ollama.chat(sistema, ORDEN, transport=transport, max_tokens=MAX_TOKENS)
    latencia = int((time.monotonic() - inicio) * 1000)
    evidencias = [{"id": e.id, "tipo": e.tipo, "texto": e.texto} for e in evidencia]
    vacio = {"citas_inexistentes": [], "sin_citas": False, "comandos_prohibidos": []}
    comprobacion = verificar(generado, evidencia) if generado else vacio
    if generado and _limpio(comprobacion):
        texto = generado.strip()
        if not texto.startswith(MARCA):
            texto = f"{MARCA} {texto}"
        return {"texto": texto, "source": "llm", "checks": {**comprobacion, "evidencia": evidencias, "motivo_texto_base": None},
                "latency_ms": latencia, "model": settings.ollama_model, "prompt_version": PROMPT_VERSION}
    motivo = "La IA no respondió a tiempo." if not generado else "El texto de la IA no pasó las verificaciones (citas que no existen, sin citas o cambios a mano)."
    return {"texto": texto_base(incident, evidencia), "source": "plantilla",
            "checks": {**comprobacion, "evidencia": evidencias, "motivo_texto_base": motivo, "texto_rechazado": generado},
            "latency_ms": latencia if generado is not None else None, "model": settings.ollama_model if generado else None,
            "prompt_version": PROMPT_VERSION if generado else None}


def diagnosticar(db: Session, incident: Incident, aportada: list[str] | None = None, transport_prometheus=None, transport_loki=None, transport=None) -> AiDraft:
    """Crea el borrador de diagnóstico (el anterior sin aprobar se descarta). Funciona con el incidente abierto. Hace commit."""
    evidencia = reunir_evidencia(incident, aportada, transport_prometheus, transport_loki)
    for anterior in db.scalars(select(AiDraft).where(AiDraft.incident_id == incident.id, AiDraft.kind == "diagnostico", AiDraft.status == "borrador_ia")):
        anterior.status = "descartado"
    r = redactar(incident, evidencia, transport=transport)
    borrador = AiDraft(
        incident_id=incident.id, kind="diagnostico", status="borrador_ia", source=r["source"], model=r["model"], prompt_version=r["prompt_version"],
        generated_text=r["texto"], checks=r["checks"], latency_ms=r["latency_ms"],
    )
    db.add(borrador)
    db.commit()
    db.refresh(borrador)
    return borrador

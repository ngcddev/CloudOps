# Datos de los reportes mensuales (spec 013). Dos funciones puras sobre la base: `operativo` (toda la agencia, para mejorar el proceso y decidir
# precios) y `ejecutivo` (un cliente, una página, en el lenguaje del glosario). Usan las MISMAS funciones de services/kpi.py que los tableros de
# la spec 010, así que las cifras coinciden (CA-5). Devuelven diccionarios simples (JSON) que se guardan congelados en `reports.data`.
import math
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.client import Client
from app.models.deployment import Deployment
from app.models.incident import Incident
from app.models.project import Project
from app.models.service import Service
from app.models.user import User
from app.services import ai_drafts, kpi
from app.services.sla import BOGOTA

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
# Un reporte ejecutivo cabe en una página (CA-2): se listan hasta este número de fallas y el resto se resume en una línea
MAX_INCIDENTES_LISTADOS = 5

# Frases para el cliente, del glosario (docs/glosario.md): ningún término técnico
TEXTO_DISPONIBLE = "Su sitio se mantuvo disponible dentro del objetivo acordado."
TEXTO_POR_DEBAJO = "Este mes su sitio estuvo disponible menos de lo acordado; le explicamos qué pasó y qué mejoramos."
TEXTO_SIN_DATOS = "Todavía no tenemos datos de su sitio este mes."
TEXTO_SIN_FALLAS = "No tuvimos fallas que afectaran su sitio este mes."
TEXTO_FALLA_GENERICO = "Se detectó una falla temporal y se activó el proceso de recuperación."
TEXTO_SIN_SOLICITUDES = "Este mes no abrió solicitudes."


def sin_nan(valor):
    """Convierte NaN e infinitos en None, recursivamente. Prometheus devuelve NaN (p. ej. la latencia p95 de un sitio sin tráfico) y NaN no
    es JSON válido: SQLite lo guarda, PostgreSQL lo rechaza («invalid input syntax for type json»). «Sin datos» es lo honesto."""
    if isinstance(valor, float) and not math.isfinite(valor):
        return None
    if isinstance(valor, dict):
        return {k: sin_nan(v) for k, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [sin_nan(v) for v in valor]
    return valor


def etiqueta_mes(month: str) -> str:
    """«2026-10» → «octubre de 2026»."""
    anio, mes = month.split("-")
    return f"{MESES[int(mes) - 1]} de {anio}"


def mes_anterior(month: str) -> str:
    anio, mes = (int(p) for p in month.split("-"))
    return f"{anio - 1}-12" if mes == 1 else f"{anio}-{mes - 1:02d}"


def _utc(valor: datetime) -> datetime:
    return valor.replace(tzinfo=timezone.utc) if valor.tzinfo is None else valor


def _kpi_del_cliente(db: Session, client: Client, month: str) -> dict:
    """Los KPI de un cliente en un mes: exactamente las funciones que usa el tablero de la agencia (spec 010)."""
    disponibilidad = sin_nan(kpi.disponibilidad_del_mes(db, client.id, month))
    return {
        "disponibilidad": disponibilidad,
        # Sin dato de disponibilidad no se dice que cumple ni que incumple el objetivo
        "cumple_objetivo": None if disponibilidad is None else kpi.cumple_objetivo(db, client.id, month, disponibilidad=disponibilidad),
        "latencia_p95": kpi.latencia_p95_del_mes(db, client.id, month),
        "sla": kpi.cumplimiento_sla(db, client.id, month),
        "mttr": kpi.mttr_del_mes(db, client.id, month),
        "solicitudes_abiertas": kpi.solicitudes_abiertas(db, client.id, month),
        "solicitudes_cerradas": kpi.solicitudes_cerradas(db, client.id, month),
        "horas": kpi.horas_por_cliente(db, client.id, month),
        "costo": kpi.costo_por_cliente(db, client.id, month),
    }


def _clientes(db: Session) -> list[Client]:
    return list(db.scalars(select(Client).options(selectinload(Client.projects).selectinload(Project.services)).order_by(Client.id)).all())


def _promedio(valores: list[float | None]) -> float | None:
    presentes = [v for v in valores if v is not None]
    return round(sum(presentes) / len(presentes), 2) if presentes else None


def _incidentes_del_mes(db: Session, client_id: int, month: str) -> list[Incident]:
    inicio, fin = kpi.month_bounds(month)
    return list(
        db.scalars(
            select(Incident)
            .join(Service, Incident.service_id == Service.id)
            .join(Project, Service.project_id == Project.id)
            .where(Project.client_id == client_id, Incident.started_at >= inicio, Incident.started_at < fin)
            .order_by(Incident.started_at, Incident.id)
        ).all()
    )


def operativo(db: Session, month: str) -> dict:
    """Reporte operativo: KPI de cada cliente en el mes y en el anterior (para comparar), totales y carga de los técnicos."""
    previo = mes_anterior(month)
    filas = []
    for client in _clientes(db):
        service = client.main_service
        plan = service.plan if service is not None else None
        filas.append(
            {
                "client_id": client.id,
                "cliente": client.name,
                "plan": plan.name if plan is not None else None,
                "slo": float(plan.slo_availability) if plan is not None else None,
                "incidentes": len(_incidentes_del_mes(db, client.id, month)),
                **_kpi_del_cliente(db, client, month),
                "mes_anterior": _kpi_del_cliente(db, client, previo),
            }
        )
    tecnicos = [
        {"nombre": u.name, "horas": kpi.horas_del_tecnico(db, u.id, month), "carga": kpi.carga_tecnico(db, u.id, month)}
        for u in db.scalars(select(User).where(User.role == "agencia").order_by(User.id)).all()
    ]
    return sin_nan({
        "kind": "operativo",
        "month": month,
        "etiqueta_mes": etiqueta_mes(month),
        "mes_anterior": previo,
        "etiqueta_mes_anterior": etiqueta_mes(previo),
        "clientes": filas,
        "totales": {
            "solicitudes_abiertas": sum(f["solicitudes_abiertas"] for f in filas),
            "solicitudes_cerradas": sum(f["solicitudes_cerradas"] for f in filas),
            "horas": round(sum(f["horas"] for f in filas), 2),
            "costo": round(sum(f["costo"] for f in filas), 2),
            "incidentes": sum(f["incidentes"] for f in filas),
            # Promedio simple de los clientes que tienen dato: un cliente sin tickets cerrados no cuenta como 0 %
            "sla_promedio": _promedio([f["sla"] for f in filas]),
            "mttr_promedio": _promedio([f["mttr"] for f in filas]),
        },
        "tecnicos": tecnicos,
        "generado": datetime.now(timezone.utc).isoformat(),
    })


def _texto_duracion(incidente: Incident) -> str:
    fin = incidente.mitigated_at or incidente.closed_at
    if fin is None:
        return "en atención"
    minutos = int((_utc(fin) - _utc(incidente.started_at)).total_seconds() // 60)
    return ai_drafts.duracion_texto(minutos)


def ejecutivo(db: Session, client_id: int, month: str) -> dict:
    """Reporte ejecutivo del cliente: una página, sin jerga. Lee de los mismos KPI que su portal y usa solo textos aprobados por una persona."""
    client = db.scalar(select(Client).options(selectinload(Client.projects).selectinload(Project.services)).where(Client.id == client_id))
    if client is None:
        raise LookupError("El cliente no existe.")
    service = client.main_service
    plan = service.plan if service is not None else None
    disponibilidad = sin_nan(kpi.disponibilidad_del_mes(db, client.id, month))
    cumple = None if disponibilidad is None else kpi.cumple_objetivo(db, client.id, month)
    if disponibilidad is None or cumple is None:
        texto_disponibilidad = TEXTO_SIN_DATOS
    else:
        texto_disponibilidad = TEXTO_DISPONIBLE if cumple else TEXTO_POR_DEBAJO

    incidentes = _incidentes_del_mes(db, client.id, month)
    listados = []
    for incidente in incidentes[:MAX_INCIDENTES_LISTADOS]:
        listados.append(
            {
                "cuando": _utc(incidente.started_at).astimezone(BOGOTA).strftime("%d/%m %H:%M"),
                "duracion": _texto_duracion(incidente),
                # Solo el mensaje que una persona aprobó (spec 012); si no hay, la frase genérica del glosario
                "texto": ai_drafts.mensaje_aprobado(db, incidente.id) or TEXTO_FALLA_GENERICO,
            }
        )
    inicio, fin = kpi.month_bounds(month)
    # Solo las actualizaciones que pidió el cliente (source = cambio); un rollback es una recuperación, no una actualización
    n_publicadas = len(
        db.scalars(
            select(Deployment.id)
            .join(Service, Deployment.service_id == Service.id)
            .join(Project, Service.project_id == Project.id)
            .where(Project.client_id == client.id, Deployment.source == "cambio", Deployment.created_at >= inicio, Deployment.created_at < fin)
        ).all()
    )
    abiertas, cerradas = kpi.solicitudes_abiertas(db, client.id, month), kpi.solicitudes_cerradas(db, client.id, month)
    mttr = kpi.mttr_del_mes(db, client.id, month)
    return sin_nan({
        "kind": "ejecutivo",
        "month": month,
        "etiqueta_mes": etiqueta_mes(month),
        "cliente": {"id": client.id, "nombre": client.name},
        "sitio": service.name if service is not None else None,
        "plan": plan.name if plan is not None else None,
        "disponibilidad": {
            "valor": disponibilidad,
            "objetivo": float(plan.slo_availability) if plan is not None else None,
            "cumple": cumple,
            "texto": texto_disponibilidad,
        },
        "fallas": {
            "total": len(incidentes),
            "listadas": listados,
            "sin_listar": max(0, len(incidentes) - MAX_INCIDENTES_LISTADOS),
            "texto": TEXTO_SIN_FALLAS if not incidentes else None,
            # Con una sola falla el promedio repite (y redondeado, contradice) la duración de esa falla: solo se muestra con varias
            "tiempo_de_recuperacion_promedio": ai_drafts.duracion_texto(int(round(mttr))) if mttr is not None and len(incidentes) > 1 else None,
        },
        "actualizaciones": {
            "publicadas": n_publicadas,
            "texto": f"Publicamos {n_publicadas} {'actualización' if n_publicadas == 1 else 'actualizaciones'} de su sitio." if n_publicadas else "Este mes no hubo actualizaciones de su sitio.",
        },
        "solicitudes": {
            "abiertas": abiertas,
            "atendidas": cerradas,
            "texto": TEXTO_SIN_SOLICITUDES if (abiertas + cerradas) == 0 else f"Recibimos {abiertas + cerradas} {'solicitud' if abiertas + cerradas == 1 else 'solicitudes'} y atendimos {cerradas}.",
        },
        "generado": datetime.now(timezone.utc).isoformat(),
    })

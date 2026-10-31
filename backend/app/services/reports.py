# Datos de los reportes mensuales (spec 013): el operativo de la agencia y el ejecutivo de cada cliente.
# Los KPI salen de services/kpi.py, las mismas funciones del dashboard (spec 010), para que coincidan (CA-5).
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.ai_draft import AiDraft
from app.models.client import Client
from app.models.deployment import Deployment
from app.models.incident import Incident
from app.models.project import Project
from app.models.service import Service
from app.models.user import User
from app.services import kpi
from app.services.sla import BOGOTA

# Textos del cliente, tomados de docs/glosario.md (principio 8): el ejecutivo no lleva jerga (CA-3)
TEXTOS = {
    "disponibilidad_dentro": "Su sitio se mantuvo disponible dentro del objetivo acordado.",
    "disponibilidad_debajo": (
        "Este mes su sitio estuvo disponible menos de lo acordado; le explicamos qué pasó y qué mejoramos."
    ),
    "sin_datos": "Todavía no tenemos datos de su sitio este mes.",
    "sin_fallas": "No tuvimos fallas que afectaran su sitio este mes.",
    "falla_sin_mensaje": "Se detectó una falla temporal y se activó el proceso de recuperación.",
    "tiempo_recuperacion": "Tiempo que tardamos en recuperar su sitio.",
    "publicacion": "Publicamos la actualización que usted solicitó.",
    "sin_publicaciones": "Este mes no hubo actualizaciones de su sitio.",
    "sin_solicitudes": "Este mes no abrió solicitudes.",
}

MESES = (
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
)


def previous_month(month: str) -> str:
    """Mes anterior a `YYYY-MM` (enero → diciembre del año anterior)."""
    year, number = (int(part) for part in month.split("-"))
    return f"{year - 1}-12" if number == 1 else f"{year}-{number - 1:02d}"


def _average(values: list[float | None]) -> float | None:
    """Promedio de los clientes con dato; None si ninguno tiene (nunca un 0 inventado)."""
    present = [value for value in values if value is not None]
    return round(sum(present) / len(present), 2) if present else None


def _totals(rows: list[dict]) -> dict:
    """Total de la agencia: suma lo que se cuenta y promedia lo que es porcentaje o tiempo."""
    return {
        "open_tickets": sum(row["open_tickets"] for row in rows),
        "closed_tickets": sum(row["closed_tickets"] for row in rows),
        "hours": round(sum(row["hours"] for row in rows), 2),
        "cost": round(sum(row["cost"] for row in rows), 2),
        "availability": _average([row["availability"] for row in rows]),
        "sla_compliance": _average([row["sla_compliance"] for row in rows]),
        "mttr": _average([row["mttr"] for row in rows]),
    }


def _technicians(db: Session, month: str) -> list[dict]:
    """Carga de cada técnico de la agencia en el mes, igual que el panel."""
    return [
        {
            "user_id": user.id,
            "name": user.name,
            "hours": kpi.horas_del_tecnico(db, user.id, month),
            "load": kpi.carga_tecnico(db, user.id, month),
        }
        for user in db.scalars(select(User).where(User.role == "agencia").order_by(User.id)).all()
    ]


def operational(db: Session, month: str) -> dict:
    """Reporte operativo del mes: KPI de cada cliente y de la agencia, con el mes anterior al lado (CA-1)."""
    before = previous_month(month)
    clients = db.scalars(
        select(Client).options(selectinload(Client.projects).selectinload(Project.services)).order_by(Client.id)
    ).all()
    rows = []
    for client in clients:
        current = kpi.client_month_kpis(db, client, month)
        previous = kpi.client_month_kpis(db, client, before)
        rows.append(
            {
                "client_id": client.id,
                "client_name": client.name,
                "service_name": current["service_name"],
                "current": current,
                "previous": previous,
            }
        )
    params = kpi.kpi_params()
    return {
        "kind": "operativo",
        "month": month,
        "previous_month": before,
        "currency": params["currency"],
        "hourly_cost": params["hourly_cost"],
        "clients": rows,
        "totals": {
            "current": _totals([row["current"] for row in rows]),
            "previous": _totals([row["previous"] for row in rows]),
        },
        "technicians": _technicians(db, month),
    }


def month_label(month: str) -> str:
    """`2026-10` → «octubre de 2026»."""
    year, number = (int(part) for part in month.split("-"))
    return f"{MESES[number - 1]} de {year}"


def _local(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(BOGOTA)


def _plural(count: int, singular: str, plural: str) -> str:
    return f"{count} {singular if count == 1 else plural}"


def _availability(db: Session, client_id: int, month: str) -> dict:
    value = kpi.disponibilidad_del_mes(db, client_id, month)
    meets = kpi.cumple_objetivo(db, client_id, month)
    objective = kpi.objetivo_disponibilidad(db, client_id)
    if value is None or meets is None:
        text = TEXTOS["sin_datos"]
    else:
        text = TEXTOS["disponibilidad_dentro"] if meets else TEXTOS["disponibilidad_debajo"]
    return {
        "value": value,
        "objective": float(objective) if objective is not None else None,
        "meets_objective": meets,
        "text": text,
    }


def _incidents(db: Session, client_id: int, month: str) -> dict:
    """Fallas del mes con el mensaje que la agencia aprobó (spec 012) o, si no hay, la frase del glosario.

    No se usa el título del incidente: puede venir de una alerta con texto técnico.
    """
    start, end = kpi.month_bounds(month)
    incidents = db.scalars(
        select(Incident)
        .join(Service, Incident.service_id == Service.id)
        .join(Project, Service.project_id == Project.id)
        .where(Project.client_id == client_id, Incident.started_at >= start, Incident.started_at < end)
        .order_by(Incident.started_at, Incident.id)
    ).all()
    approved: dict[int, str] = {}
    if incidents:
        rows = db.execute(
            select(AiDraft.incident_id, AiDraft.final_text)
            .where(
                AiDraft.incident_id.in_([incident.id for incident in incidents]),
                AiDraft.kind == "mensaje_cliente",
                AiDraft.status == "aprobado",
            )
            .order_by(AiDraft.approved_at)
        )
        approved = {incident_id: text for incident_id, text in rows}
    items = [
        {
            "date": _local(incident.started_at).strftime("%d/%m/%Y"),
            "time": _local(incident.started_at).strftime("%H:%M"),
            "text": approved.get(incident.id) or TEXTOS["falla_sin_mensaje"],
        }
        for incident in incidents
    ]
    mttr = kpi.mttr_del_mes(db, client_id, month)
    return {
        "count": len(items),
        "items": items,
        "text": TEXTOS["sin_fallas"] if not items else f"Este mes tuvimos {_plural(len(items), 'falla', 'fallas')}.",
        "recovery_text": (
            f"{TEXTOS['tiempo_recuperacion']} {round(mttr)} min." if mttr is not None else None
        ),
    }


def _changes(db: Session, client_id: int, month: str) -> dict:
    """Actualizaciones publicadas del mes (cambios aprobados; las recuperaciones no cuentan como cambio)."""
    start, end = kpi.month_bounds(month)
    deployments = db.scalars(
        select(Deployment)
        .join(Service, Deployment.service_id == Service.id)
        .join(Project, Service.project_id == Project.id)
        .where(
            Project.client_id == client_id,
            Deployment.source == "cambio",
            Deployment.created_at >= start,
            Deployment.created_at < end,
        )
        .order_by(Deployment.created_at, Deployment.id)
    ).all()
    items = [
        {"date": _local(deployment.created_at).strftime("%d/%m/%Y"), "text": TEXTOS["publicacion"]}
        for deployment in deployments
    ]
    return {
        "count": len(items),
        "items": items,
        "text": (
            TEXTOS["sin_publicaciones"]
            if not items
            else f"Este mes publicamos {_plural(len(items), 'actualización', 'actualizaciones')} de su sitio."
        ),
    }


def _tickets(db: Session, client_id: int, month: str) -> dict:
    opened = len(kpi.tickets_del_cliente(db, client_id, month))
    attended = kpi.solicitudes_cerradas(db, client_id, month)
    if opened == 0:
        text = TEXTOS["sin_solicitudes"]
    else:
        text = (
            f"Este mes abrió {_plural(opened, 'solicitud', 'solicitudes')} y atendimos "
            f"{_plural(attended, 'solicitud', 'solicitudes')}."
        )
    return {"opened": opened, "attended": attended, "text": text}


def executive(db: Session, client_id: int, month: str) -> dict:
    """Reporte ejecutivo del cliente en una página: todo en lenguaje de negocio (CA-2, CA-3)."""
    client = db.scalar(
        select(Client)
        .options(selectinload(Client.projects).selectinload(Project.services).selectinload(Service.plan))
        .where(Client.id == client_id)
    )
    if client is None:
        raise ValueError("El cliente no existe.")
    service = client.main_service
    return {
        "kind": "ejecutivo",
        "month": month,
        "month_label": month_label(month),
        "client_id": client.id,
        "client_name": client.name,
        "service_name": service.name if service is not None else None,
        "plan_name": service.plan.name if service is not None and service.plan is not None else None,
        "availability": _availability(db, client.id, month),
        "incidents": _incidents(db, client.id, month),
        "changes": _changes(db, client.id, month),
        "tickets": _tickets(db, client.id, month),
    }


def client_texts(report: dict) -> list[str]:
    """Todos los textos que ve el cliente en un ejecutivo, para revisarlos contra el glosario (CA-3)."""
    texts = [report["availability"]["text"], report["incidents"]["text"], report["changes"]["text"]]
    texts += [report["tickets"]["text"]]
    texts += [item["text"] for item in report["incidents"]["items"] + report["changes"]["items"]]
    if report["incidents"]["recovery_text"]:
        texts.append(report["incidents"]["recovery_text"])
    return texts

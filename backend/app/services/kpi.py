# KPIs del mes para el panel de la agencia y el portal del cliente (spec 010, T03-T11).
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.incident import Incident
from app.models.project import Project
from app.models.service import Service
from app.models.ticket import Ticket
from app.models.work_log import WorkLog
from app.services.sla import BOGOTA

# Carpeta donde el seed escribe los JSON de datos (misma convención que backend/app/seed.py).
SEED_DIR = Path(os.getenv("SEED_DIR") or Path(__file__).resolve().parents[2] / "seed")

# Valores de trabajo mientras la spec 000 no cierra los precios y la capacidad (docs/kpi.md, T01).
KPI_DEFAULTS = {
    "hourly_cost": 25000,
    "technician_monthly_hours": 120,
    "currency": "COP",
    "at_risk_ratio": 0.8,
}


def kpi_params() -> dict:
    """Lee los parámetros de KPI de `seed/kpi_params.json`; si no existe usa los de trabajo."""
    try:
        data = json.loads((SEED_DIR / "kpi_params.json").read_text(encoding="utf-8"))
        return {**KPI_DEFAULTS, **data}
    except (OSError, ValueError):
        return dict(KPI_DEFAULTS)

# Estados con solución: la solicitud respondió y resolvió (o cerró) su caso; ya no sigue abierta.
ESTADOS_TERMINADOS = {"resuelto", "cerrado"}


def _as_utc(value: datetime | None) -> datetime | None:
    """SQLite devuelve las fechas sin zona; se guardan siempre en UTC, así que se les pone."""
    if value is None or value.tzinfo is not None:
        return value
    return value.replace(tzinfo=timezone.utc)


def month_bounds(month: str) -> tuple[datetime, datetime]:
    """Rango [inicio, fin) del mes `YYYY-MM` en America/Bogota, convertido a UTC para la base de datos.

    El mes arranca a las 00:00 hora de Colombia (06:00 UTC) y termina el primer día del mes siguiente.
    """
    anio, mes = (int(part) for part in month.split("-"))
    inicio_local = datetime(anio, mes, 1, tzinfo=BOGOTA)
    if mes == 12:
        fin_local = datetime(anio + 1, 1, 1, tzinfo=BOGOTA)
    else:
        fin_local = datetime(anio, mes + 1, 1, tzinfo=BOGOTA)
    inicio = _as_utc(inicio_local)
    fin = _as_utc(fin_local)
    assert inicio is not None and fin is not None
    return inicio, fin


def tickets_del_cliente(db: Session, client_id: int, month: str) -> list[Ticket]:
    """Solicitudes del cliente creado en el mes, del más viejo al más reciente."""
    inicio, fin = month_bounds(month)
    return list(
        db.scalars(
            select(Ticket)
            .join(Ticket.service)
            .join(Service.project)
            .join(Project.client)
            .where(Client.id == client_id, Ticket.created_at >= inicio, Ticket.created_at < fin)
            .order_by(Ticket.created_at, Ticket.id)
        ).all()
    )


def solicitudes_abiertas(db: Session, client_id: int, month: str | None = None) -> int:
    """Solicitudes del mes que siguen abiertas (no cerraron su caso)."""
    tickets = tickets_del_cliente(db, client_id, month or _mes_actual())
    return sum(1 for ticket in tickets if ticket.status not in ESTADOS_TERMINADOS)


def solicitudes_cerradas(db: Session, client_id: int, month: str | None = None) -> int:
    """Solicitudes del mes que cerraron su caso (tuvieron solución registrada)."""
    tickets = tickets_del_cliente(db, client_id, month or _mes_actual())
    return sum(1 for ticket in tickets if ticket.status in ESTADOS_TERMINADOS)


def horas_por_cliente(db: Session, client_id: int, month: str | None = None) -> float:
    """Horas registradas (Σ `work_logs.hours`) de las solicitudes del cliente en el mes."""
    tickets = tickets_del_cliente(db, client_id, month or _mes_actual())
    total = 0.0
    for ticket in tickets:
        for work_log in ticket.work_logs:
            total += float(work_log.hours)
    return total


def costo_por_cliente(db: Session, client_id: int, month: str | None = None) -> float:
    """Costo del mes del cliente: horas registradas × `hourly_cost` (docs/kpi.md, T01)."""
    return horas_por_cliente(db, client_id, month) * float(kpi_params()["hourly_cost"])


def horas_del_tecnico(db: Session, user_id: int, month: str | None = None) -> float:
    """Horas registradas por un técnico en el mes: Σ `work_logs.hours` de sus tickets creados en el mes."""
    inicio, fin = month_bounds(month or _mes_actual())
    total = db.scalar(
        select(func.sum(WorkLog.hours))
        .join(Ticket, WorkLog.ticket_id == Ticket.id)
        .where(WorkLog.user_id == user_id, Ticket.created_at >= inicio, Ticket.created_at < fin)
    )
    return float(total or 0)


def carga_tecnico(db: Session, user_id: int, month: str | None = None) -> float:
    """Carga del técnico del mes: horas registradas ÷ horas disponibles del mes (`technician_monthly_hours`)."""
    return horas_del_tecnico(db, user_id, month) / float(kpi_params()["technician_monthly_hours"])


def mttr_del_mes(db: Session, client_id: int, month: str | None = None) -> float | None:
    """MTTR del mes: promedio (solución − inicio) en minutos de los incidentes mitigados/cerrados.

    Sin incidentes mitigados en el mes devuelve `None` (CA-9): no se reporta un MTTR de 0 inventado.
    """
    inicio, fin = month_bounds(month or _mes_actual())
    incidents = db.scalars(
        select(Incident)
        .join(Incident.service)
        .join(Service.project)
        .join(Project.client)
        .where(
            Client.id == client_id,
            Incident.started_at >= inicio,
            Incident.started_at < fin,
            Incident.status.in_(["mitigado", "cerrado"]),
        )
    ).all()
    if not incidents:
        return None
    minutos = []
    for incident in incidents:
        solucion = _as_utc(incident.mitigated_at) or _as_utc(incident.closed_at)
        inicio_at = _as_utc(incident.started_at)
        if solucion is None or inicio_at is None:
            continue
        minutos.append((solucion - inicio_at).total_seconds() / 60)
    if not minutos:
        return None
    return round(sum(minutos) / len(minutos), 2)


def cumplimiento_sla(db: Session, client_id: int, month: str | None = None) -> float | None:
    """Porcentaje de las solicitudes cerradas dentro de su plazo de solución: (dentro / terminados) × 100.

    Con ninguna solicitud terminada en el mes devuelve `None` («sin datos»): no se reporta un 100 % inventado.
    """
    tickets = tickets_del_cliente(db, client_id, month or _mes_actual())
    terminados = [
        ticket
        for ticket in tickets
        if ticket.status in ESTADOS_TERMINADOS and (ticket.resolved_at is not None or ticket.closed_at is not None)
    ]
    if not terminados:
        return None
    dentro = sum(
        1
        for ticket in terminados
        if (solucion := _as_utc(ticket.resolved_at or ticket.closed_at)) is not None
        and ticket.resolution_due_at is not None
        and solucion <= _as_utc(ticket.resolution_due_at)
    )
    return round((dentro / len(terminados)) * 100, 2)


def mes_actual() -> str:
    """Mes actual en America/Bogota, con el formato `YYYY-MM` que reciben las consultas."""
    return datetime.now(BOGOTA).strftime("%Y-%m")

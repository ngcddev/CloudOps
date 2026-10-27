# KPIs del mes para el panel de la agencia y el portal del cliente (spec 010, T03-T11).
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.project import Project
from app.models.service import Service
from app.models.ticket import Ticket
from app.services.sla import BOGOTA

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


def _mes_actual() -> str:
    """Mes actual en America/Bogota, con el formato `YYYY-MM` que reciben las consultas."""
    return datetime.now(BOGOTA).strftime("%Y-%m")

# Utilidades de las pruebas de los reportes (spec 013): un mes con trabajo y el anterior, para comparar.
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select

from app.models import Service, Ticket, User, WorkLog
from tests.ai_support import mitigated_incident


def ticket_with_hours(db, namespace: str, created_at: datetime, hours: str, resolved: bool = True) -> Ticket:
    """Solicitud del servicio creada en `created_at`, con horas registradas y resuelta dentro del plazo."""
    service = db.scalar(select(Service).where(Service.namespace == namespace))
    technician = db.scalar(select(User).where(User.role == "agencia").order_by(User.id))
    ticket = Ticket(
        service_id=service.id,
        title="Cambiar el horario del domingo",
        description="El horario del domingo cambió.",
        priority="P3",
        status="resuelto" if resolved else "en_progreso",
        response_due_at=created_at + timedelta(hours=4),
        resolution_due_at=created_at + timedelta(hours=24),
        resolved_at=created_at + timedelta(hours=2) if resolved else None,
        created_at=created_at,
    )
    db.add(ticket)
    db.flush()
    db.add(WorkLog(ticket_id=ticket.id, user_id=technician.id, hours=Decimal(hours), created_at=created_at))
    db.commit()
    return ticket


def busy_october(db):
    """Octubre de 2026 con trabajo en La Sazón (solicitud, horas y una falla mitigada) y septiembre con menos."""
    ticket_with_hours(db, "cliente-restaurante", datetime(2026, 9, 10, 15, tzinfo=timezone.utc), "1.5")
    ticket_with_hours(db, "cliente-restaurante", datetime(2026, 10, 5, 15, tzinfo=timezone.utc), "3")
    ticket_with_hours(db, "cliente-ferreteria", datetime(2026, 10, 7, 15, tzinfo=timezone.utc), "2", resolved=False)
    return mitigated_incident(db)

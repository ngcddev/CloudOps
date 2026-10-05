# Cálculo de fechas límite del SLA para tickets (spec 004, T06).
from datetime import datetime, timedelta, timezone

from app.models.plan import Plan


P1_RESPONSE_MINUTES = 15
P1_RESOLUTION_MINUTES = 240


def due_dates(created_at: datetime, priority: str, plan: Plan) -> tuple[datetime, datetime]:
    """Calcula respuesta y solución de P1 usando reloj continuo 24/7."""
    if priority != "P1":
        raise ValueError("T06 solo calcula fechas para la prioridad P1.")
    if created_at.tzinfo is None or created_at.utcoffset() is None:
        raise ValueError("La fecha de creación debe incluir zona horaria.")

    created_at_utc = created_at.astimezone(timezone.utc)
    response_due_at = created_at_utc + timedelta(minutes=P1_RESPONSE_MINUTES)
    resolution_due_at = created_at_utc + timedelta(minutes=P1_RESOLUTION_MINUTES)
    return response_due_at, resolution_due_at
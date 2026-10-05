# Cálculo de fechas límite y estado del SLA (spec 004, T06-T08).
import re
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from app.models.plan import Plan


P1_RESPONSE_MINUTES = 15
P1_RESOLUTION_MINUTES = 240
SLA_MINUTES = {
    "P1": (15, 240),
    "P2": (60, 480),
    "P3": (240, 1440),
    "P4": (480, 4320),
}
BOGOTA = ZoneInfo("America/Bogota")
DAY_NUMBERS = {"lun": 0, "mar": 1, "mie": 2, "jue": 3, "vie": 4, "sab": 5, "dom": 6}


def due_dates(created_at: datetime, priority: str, plan: Plan) -> tuple[datetime, datetime]:
    """Calcula las fechas límite usando 24/7 o el horario del plan."""
    if priority not in SLA_MINUTES:
        raise ValueError(f"Prioridad inválida: «{priority}».")
    if created_at.tzinfo is None or created_at.utcoffset() is None:
        raise ValueError("La fecha de creación debe incluir zona horaria.")

    created_at_utc = created_at.astimezone(timezone.utc)
    response_minutes, resolution_minutes = SLA_MINUTES[priority]
    if priority == "P1" or plan.support_hours == "24x7":
        return (
            created_at_utc + timedelta(minutes=response_minutes),
            created_at_utc + timedelta(minutes=resolution_minutes),
        )

    schedule = _parse_support_hours(plan.support_hours)
    return (
        _add_business_minutes(created_at_utc, response_minutes, schedule),
        _add_business_minutes(created_at_utc, resolution_minutes, schedule),
    )


def sla_state(ticket, now: datetime | None = None) -> str:
    """Devuelve a_tiempo, en_riesgo o vencido para el plazo activo del ticket."""
    created_at = _require_aware(ticket.created_at, "created_at")
    current = _require_aware(now or datetime.now(timezone.utc), "now")
    if ticket.first_response_at is None:
        due_at = ticket.response_due_at
    else:
        due_at = ticket.resolution_due_at
    if due_at is None:
        raise ValueError("El ticket no tiene una fecha límite para calcular el SLA.")

    created_at = created_at.astimezone(timezone.utc)
    current = current.astimezone(timezone.utc)
    due_at = _require_aware(due_at, "due_at").astimezone(timezone.utc)
    total = due_at - created_at
    elapsed = current - created_at
    if total <= timedelta(0):
        raise ValueError("La fecha límite debe ser posterior a la creación del ticket.")
    if current >= due_at:
        return "vencido"
    if elapsed * 5 >= total * 4:
        return "en_riesgo"
    return "a_tiempo"


def _require_aware(value: datetime | None, field_name: str) -> datetime:
    if value is None or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"La fecha «{field_name}» debe incluir zona horaria.")
    return value


def _parse_support_hours(value: str) -> tuple[set[int], time, time]:
    match = re.fullmatch(
        r"(lun|mar|mie|jue|vie|sab|dom)-(lun|mar|mie|jue|vie|sab|dom) "
        r"(\d{2}):(\d{2})-(\d{2}):(\d{2})",
        value,
    )
    if match is None:
        raise ValueError(f"Horario de atención inválido: «{value}».")

    start_day, end_day, start_hour, start_minute, end_hour, end_minute = match.groups()
    first_day = DAY_NUMBERS[start_day]
    last_day = DAY_NUMBERS[end_day]
    days = {(first_day + offset) % 7 for offset in range((last_day - first_day) % 7 + 1)}
    return days, time(int(start_hour), int(start_minute)), time(int(end_hour), int(end_minute))


def _add_business_minutes(
    created_at_utc: datetime,
    minutes: int,
    schedule: tuple[set[int], time, time],
) -> datetime:
    days, opening, closing = schedule
    local = created_at_utc.astimezone(BOGOTA)
    remaining = float(minutes)

    while True:
        if local.weekday() not in days:
            local = _next_day_at(local, opening)
            continue
        if local.time() < opening or local.time() >= closing:
            local = _next_day_at(local, opening) if local.time() >= closing else local.replace(
                hour=opening.hour, minute=opening.minute, second=0, microsecond=0
            )
            continue

        closing_at = datetime.combine(local.date(), closing, tzinfo=BOGOTA)
        available = (closing_at - local).total_seconds() / 60
        if remaining <= available:
            return (local + timedelta(minutes=remaining)).astimezone(timezone.utc)
        remaining -= available
        local = _next_day_at(local, opening)


def _next_day_at(value: datetime, opening: time) -> datetime:
    next_date = value.date() + timedelta(days=1)
    return datetime.combine(next_date, opening, tzinfo=BOGOTA)
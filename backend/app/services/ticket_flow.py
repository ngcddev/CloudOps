# Transiciones válidas del ciclo de vida de una solicitud (spec 004, T05).
from datetime import datetime, timezone

from app.models.ticket import Ticket


VALID_TRANSITIONS: dict[str, set[str]] = {
    "abierto": {"en_progreso"},
    "en_progreso": {"en_espera", "resuelto"},
    "en_espera": {"en_progreso"},
    "resuelto": {"cerrado"},
    "cerrado": set(),
}


def transition(ticket: Ticket, new_status: str, now: datetime | None = None) -> Ticket:
    """Mueve un ticket a un estado permitido y devuelve el mismo ticket."""
    allowed = VALID_TRANSITIONS.get(ticket.status, set())
    if new_status not in allowed:
        raise ValueError(f"No se permite pasar de «{ticket.status}» a «{new_status}».")

    timestamp = now or datetime.now(timezone.utc)
    ticket.status = new_status
    if new_status == "en_progreso" and ticket.first_response_at is None:
        ticket.first_response_at = timestamp
    if new_status == "resuelto":
        ticket.resolved_at = timestamp
    if new_status == "cerrado":
        ticket.closed_at = timestamp
    return ticket
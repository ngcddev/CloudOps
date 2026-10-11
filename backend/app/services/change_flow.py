# Transiciones válidas de una solicitud de cambio (spec 005, T09):
# pendiente → aprobada → en_validacion → desplegada, o pendiente → rechazada.
from datetime import datetime, timezone

from app.models.change_request import ChangeRequest
from app.models.ticket_event import TicketEvent

VALID_TRANSITIONS: dict[str, set[str]] = {
    "pendiente": {"aprobada", "rechazada"},
    "aprobada": {"en_validacion"},
    "en_validacion": {"desplegada"},
    "desplegada": set(),
    "rechazada": set(),
}


def transition(
    change: ChangeRequest,
    new_status: str,
    actor_id: int | None = None,
    reason: str | None = None,
    now: datetime | None = None,
) -> ChangeRequest:
    """Mueve la solicitud a un estado permitido y devuelve la misma solicitud.

    Fija la hora de cada paso (y quién aprobó). Rechazar exige un motivo.
    """
    allowed = VALID_TRANSITIONS.get(change.status, set())
    if new_status not in allowed:
        raise ValueError(f"No se permite pasar de «{change.status}» a «{new_status}».")

    clean_reason = (reason or "").strip()
    if new_status == "rechazada" and not clean_reason:
        raise ValueError("Debe indicar el motivo del rechazo.")

    timestamp = now or datetime.now(timezone.utc)
    change.status = new_status
    if new_status == "aprobada":
        change.approved_at = timestamp
        change.approved_by_id = actor_id
    elif new_status == "desplegada":
        change.deployed_at = timestamp
    elif new_status == "rechazada":
        change.rejection_reason = clean_reason
    return change


def step_event(
    change: ChangeRequest,
    from_status: str | None,
    actor_id: int | None,
    note: str | None = None,
) -> TicketEvent:
    """Evento del historial de la solicitud que deja constancia de un paso: quién, cuándo y de qué a qué."""
    return TicketEvent(
        ticket_id=change.ticket_id,
        actor_id=actor_id,
        type="cambio",
        from_value=from_status,
        to_value=change.status,
        note=note,
        internal=False,
    )

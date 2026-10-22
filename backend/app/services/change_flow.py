# Transiciones válidas de una solicitud de cambio (spec 005, T09):
# pendiente → aprobada → en_validacion → desplegada, o pendiente → rechazada.
from datetime import datetime, timezone

from app.models.change_request import ChangeRequest

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

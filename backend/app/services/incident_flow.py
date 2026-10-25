# Ciclo de vida de un incidente: abierto → mitigado → cerrado, y la acción de tomarlo (spec 008, T02).
from datetime import datetime, timezone

from app.models.incident import Incident
from app.models.incident_event import IncidentEvent
from app.models.user import User


VALID_TRANSITIONS: dict[str, set[str]] = {
    "abierto": {"mitigado"},
    "mitigado": {"cerrado"},
    "cerrado": set(),
}


class IncidentFlowError(ValueError):
    """La acción no está permitida en el estado actual del incidente (la API responde 409)."""


def _now(now: datetime | None) -> datetime:
    return now or datetime.now(timezone.utc)


def _move(incident: Incident, new_status: str) -> None:
    if new_status not in VALID_TRANSITIONS.get(incident.status, set()):
        raise IncidentFlowError(f"No se permite pasar de «{incident.status}» a «{new_status}».")
    incident.status = new_status


def add_event(incident: Incident, type_: str, message: str | None = None, actor: User | None = None,
              at: datetime | None = None) -> IncidentEvent:
    """Agrega un evento a la línea de tiempo; `actor=None` significa «Sistema»."""
    event = IncidentEvent(type=type_, message=message, actor_id=actor.id if actor is not None else None)
    if at is not None:
        event.created_at = at
    incident.events.append(event)
    return event


def acknowledge(incident: Incident, user: User, now: datetime | None = None) -> Incident:
    """Tomar el incidente: fija la respuesta y el responsable. No es un estado y solo se hace una vez."""
    if incident.acknowledged_at is not None:
        raise IncidentFlowError("El incidente ya fue tomado.")
    if incident.status == "cerrado":
        raise IncidentFlowError("El incidente ya está cerrado.")
    incident.acknowledged_at = _now(now)
    incident.assignee_id = user.id
    return incident


def mitigate(incident: Incident, now: datetime | None = None, by_alert: bool = False) -> Incident:
    """Marca el servicio como recuperado.

    A mano solo vale para los incidentes `manual`: los de alerta los mitiga el aviso `resolved`, con la
    hora real del primer sondeo sano (principio 7).
    """
    if not by_alert and incident.source != "manual":
        raise IncidentFlowError("Un incidente de alerta se mitiga solo cuando el monitoreo ve el sitio sano.")
    _move(incident, "mitigado")
    incident.mitigated_at = _now(now)
    return incident


def close(incident: Incident, root_cause: str | None, now: datetime | None = None) -> Incident:
    """Cierra un incidente mitigado; la causa raíz es obligatoria para que quede la lección."""
    cause = (root_cause or "").strip()
    if not cause:
        raise IncidentFlowError("Para cerrar el incidente hay que escribir la causa raíz.")
    _move(incident, "cerrado")
    incident.root_cause = cause
    incident.closed_at = _now(now)
    return incident

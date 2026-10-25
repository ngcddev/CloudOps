# Convierte los avisos de Alertmanager en incidentes: abrir con `firing` sin duplicar y mitigar con `resolved` (spec 008, T10-T12).
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.models.service import Service
from app.schemas.alertmanager import AlertmanagerAlert
from app.services import audit
from app.services import incident_flow
from app.services.incident_flow import add_event
from app.services.sla import due_dates

logger = logging.getLogger(__name__)

DEFAULT_PRIORITY = "P1"


def _service_for(db: Session, alert: AlertmanagerAlert) -> Service | None:
    """El servicio se ubica por el namespace del sitio caído (`cliente-<c>`)."""
    namespace = alert.labels.get("namespace")
    if not namespace:
        return None
    return db.scalar(select(Service).where(Service.namespace == namespace))


def _open_incident(db: Session, fingerprint: str) -> Incident | None:
    """El incidente abierto de esa falla, si lo hay. Uno ya mitigado no cuenta: la falla volvió."""
    return db.scalar(select(Incident).where(Incident.fingerprint == fingerprint, Incident.status == "abierto"))


def open_from_alert(db: Session, alert: AlertmanagerAlert, confirm_seconds: int) -> tuple[str, int | None]:
    """Abre el incidente de un `firing`: prioridad de la etiqueta, SLA con la hora real y servicio caído.

    Prometheus avisa cuando termina el `for` de la regla, no cuando empezó la caída: la hora de inicio
    es `startsAt − confirm_seconds` (principio 7). Si la falla ya tiene un incidente abierto (Alertmanager
    repite los avisos), no crea otro (CA-3). No hace commit.
    """
    existing = _open_incident(db, alert.fingerprint)
    if existing is not None:
        return "duplicado", existing.id
    service = _service_for(db, alert)
    if service is None:
        logger.warning("Aviso de Alertmanager para un servicio desconocido: %s", alert.labels.get("namespace"))
        return "ignorado", None

    priority = alert.labels.get("priority", DEFAULT_PRIORITY)
    if priority not in {"P1", "P2", "P3", "P4"}:
        priority = DEFAULT_PRIORITY
    started_at: datetime = alert.starts_at - timedelta(seconds=confirm_seconds)
    response_due_at, resolution_due_at = due_dates(started_at, priority, service.plan)
    title = alert.annotations.get("summary") or f"El sitio {service.name} no responde"
    incident = Incident(
        service_id=service.id,
        priority=priority,
        status="abierto",
        source="alerta",
        fingerprint=alert.fingerprint,
        title=title[:200],
        started_at=started_at,
        response_due_at=response_due_at,
        resolution_due_at=resolution_due_at,
    )
    # Dos avisos simultáneos de la misma falla: el índice único parcial deja pasar solo uno, y el otro
    # se trata como repetido sin perder el resto de la transacción
    try:
        with db.begin_nested():
            db.add(incident)
            add_event(incident, "detectado", "El monitoreo detectó que el sitio no responde.", None, at=started_at)
            db.flush()
    except IntegrityError:
        existing = _open_incident(db, alert.fingerprint)
        return "duplicado", existing.id if existing is not None else None
    service.status = "caido"
    audit.record(
        db, None, "crear", "incident", incident.id,
        {"prioridad": priority, "servicio": service.namespace, "origen": "alerta"},
    )
    return "creado", incident.id


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def resolve_from_alert(db: Session, alert: AlertmanagerAlert) -> tuple[str, int | None]:
    """Mitiga el incidente de un `resolved` con la hora real del primer sondeo sano (`endsAt`, CA-6).

    El servicio vuelve a `operativo` si no le queda otro incidente de alerta abierto. No hace commit.
    """
    incident = _open_incident(db, alert.fingerprint)
    if incident is None:
        logger.warning("Aviso resolved de una falla sin incidente abierto: %s", alert.fingerprint)
        return "ignorado", None

    started_at = _as_utc(incident.started_at)
    recovered_at = alert.ends_at if alert.ends_at is not None and alert.ends_at > started_at else datetime.now(timezone.utc)
    incident_flow.mitigate(incident, recovered_at, by_alert=True)
    add_event(incident, "recuperado", "El monitoreo vio el sitio responder de nuevo.", None, at=recovered_at)
    db.flush()
    still_down = db.scalar(
        select(Incident.id).where(
            Incident.service_id == incident.service_id, Incident.source == "alerta", Incident.status == "abierto"
        )
    )
    if still_down is None:
        incident.service.status = "operativo"
    audit.record(db, None, "mitigar", "incident", incident.id, {"origen": "alerta"})
    return "mitigado", incident.id

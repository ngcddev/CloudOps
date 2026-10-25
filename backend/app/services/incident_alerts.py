# Convierte los avisos de Alertmanager en incidentes: abrir con `firing` (spec 008, T10-T12).
import logging
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.models.service import Service
from app.schemas.alertmanager import AlertmanagerAlert
from app.services import audit
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


def open_from_alert(db: Session, alert: AlertmanagerAlert, confirm_seconds: int) -> tuple[str, int | None]:
    """Abre el incidente de un `firing`: prioridad de la etiqueta, SLA con la hora real y servicio caído.

    Prometheus avisa cuando termina el `for` de la regla, no cuando empezó la caída: la hora de inicio
    es `startsAt − confirm_seconds` (principio 7). No hace commit.
    """
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
    db.add(incident)
    add_event(incident, "detectado", "El monitoreo detectó que el sitio no responde.", None, at=started_at)
    service.status = "caido"
    db.flush()
    audit.record(
        db, None, "crear", "incident", incident.id,
        {"prioridad": priority, "servicio": service.namespace, "origen": "alerta"},
    )
    return "creado", incident.id

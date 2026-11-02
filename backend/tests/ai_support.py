# Utilidades de las pruebas del asistente (spec 012): el incidente mitigado de La Sazón, de 14:00 a 14:07.
from datetime import timedelta

from sqlalchemy import select

from app.models import Incident, Service
from tests.rollback_support import T0, open_incident


def mitigated_incident(db, status: str = "mitigado") -> Incident:
    """Incidente de alerta de La Sazón recuperado con rollback de v2 a v1 (14:00 → 14:07 en Colombia)."""
    sazon = db.scalar(select(Service).where(Service.namespace == "cliente-restaurante"))
    incident = open_incident(db, sazon)
    incident.rollback_from_version, incident.rollback_to_version = "v2", "v1"
    incident.rollback_at = T0 + timedelta(minutes=3)
    incident.rollback_confirmed_at = T0 + timedelta(minutes=6)
    incident.mitigated_at = T0 + timedelta(minutes=7, seconds=30)
    incident.status = status
    if status == "cerrado":
        incident.closed_at = T0 + timedelta(minutes=30)
        incident.root_cause = "La versión nueva respondía con error en la página principal."
    db.commit()
    return incident

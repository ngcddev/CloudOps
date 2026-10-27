# Utilidades de las pruebas del rollback (spec 009): un Gitea con el kustomization de La Sazón y un incidente de alerta.
from datetime import datetime, timedelta, timezone

from app.models import Incident

# 14:00 en Colombia (UTC-5)
T0 = datetime(2026, 10, 24, 19, 0, tzinfo=timezone.utc)
RUTA = "clients/restaurante/kustomization.yaml"


def kustomization(tag: str) -> str:
    return (
        "# Cliente restaurante\n"
        "apiVersion: kustomize.config.k8s.io/v1beta1\n"
        "kind: Kustomization\n"
        "namespace: cliente-restaurante\n"
        "images:\n"
        "  - name: gitea.hub.local/forja-digital/plantilla\n"
        "    newName: gitea.hub.local/forja-digital/restaurante\n"
        f"    newTag: {tag}\n"
        "patches:\n"
        "  - target: { kind: Namespace }\n"
    )


def open_incident(db, service, source: str = "alerta", started_at: datetime = T0, status: str = "abierto") -> Incident:
    """Incidente P1 de un servicio; el de alerta deja además el sitio `caido`, como el webhook."""
    incident = Incident(
        service_id=service.id,
        priority="P1",
        status=status,
        source=source,
        title="El sitio no responde",
        fingerprint=f"fp-{service.id}-{started_at.timestamp()}-{status}" if source == "alerta" else None,
        started_at=started_at,
        response_due_at=started_at + timedelta(minutes=15),
        resolution_due_at=started_at + timedelta(hours=4),
    )
    db.add(incident)
    if source == "alerta":
        service.status = "caido"
    db.commit()
    return incident

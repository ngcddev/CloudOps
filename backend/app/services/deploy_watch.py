# Seguimiento de las publicaciones por GitOps (spec 005, T15): consulta a Argo CD y confirma cada
# cambio en validación. El estado se lee de Argo CD, no se infiere (riesgo "Hub y Argo CD
# desincronizados" del plan).
import asyncio
import logging
from collections.abc import Callable
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.argocd import AppStatus, ArgoCDError
from app.models.change_request import ChangeRequest
from app.models.deployment import Deployment
from app.models.service import Service
from app.services.change_flow import step_event, transition

logger = logging.getLogger("hub.deploy_watch")

# Cada cuántos segundos se consulta a Argo CD (plan 005)
INTERVAL_SECONDS = 15


def is_published(status: AppStatus, commit_sha: str | None) -> bool:
    """El cambio está publicado cuando Argo CD aplicó justo ese commit y la aplicación está sana."""
    return (
        status.sync == "Synced"
        and status.health == "Healthy"
        and commit_sha is not None
        and (status.revision or "").lower() == commit_sha.lower()
    )


def check_cycle(db: Session, argocd, now: datetime | None = None) -> list[int]:
    """Una vuelta: refresca sincronización y salud de cada servicio y confirma los cambios listos.

    `argocd` es cualquier objeto con `get_application(nombre) -> AppStatus`. Devuelve los ids de las
    solicitudes que pasaron a `desplegada`. Un fallo con un servicio no frena a los demás.
    """
    timestamp = now or datetime.now(timezone.utc)
    deployed: list[int] = []
    for service in db.scalars(select(Service).order_by(Service.id)).all():
        try:
            status = argocd.get_application(service.namespace)
        except ArgoCDError as error:
            logger.warning("Argo CD no informó de %s: %s", service.namespace, error)
            continue
        service.sync_status = status.sync
        service.health_status = status.health

        pending = db.scalars(
            select(ChangeRequest)
            .where(ChangeRequest.service_id == service.id, ChangeRequest.status == "en_validacion")
            .order_by(ChangeRequest.id)
        ).all()
        for change in pending:
            if not is_published(status, change.gitops_commit_sha):
                continue
            approver = change.approved_by
            transition(change, "desplegada", actor_id=change.approved_by_id, now=timestamp)
            service.current_version = change.to_version
            service.stable_version = change.to_version
            db.add(
                Deployment(
                    service_id=service.id,
                    version=change.to_version,
                    commit_sha=change.gitops_commit_sha,
                    author=approver.name if approver else "Hub",
                    source="cambio",
                    created_at=timestamp,
                )
            )
            db.add(
                step_event(
                    change, "en_validacion", change.approved_by_id,
                    f"Argo CD confirmó {change.to_version}: sincronizado y sano.",
                )
            )
            deployed.append(change.id)
    db.commit()
    return deployed


async def watch_forever(
    session_factory: Callable[[], Session],
    argocd,
    interval: float = INTERVAL_SECONDS,
) -> None:
    """Corre `check_cycle` cada `interval` segundos hasta que se cancele la tarea."""

    def once() -> None:
        with session_factory() as db:
            check_cycle(db, argocd)

    while True:
        try:
            await asyncio.to_thread(once)
        except Exception:  # la vigilancia nunca debe tumbar la API
            logger.exception("Falló una vuelta del seguimiento de Argo CD")
        await asyncio.sleep(interval)

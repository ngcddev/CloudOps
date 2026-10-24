# Seguimiento de las publicaciones por GitOps (spec 005, T15): consulta a Argo CD y confirma cada
# cambio en validación. El estado se lee de Argo CD, no se infiere (riesgo "Hub y Argo CD
# desincronizados" del plan).
import asyncio
import logging
from collections.abc import Callable
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.integrations.argocd import AppStatus, ArgoCDError
from app.integrations.gitea import GiteaError
from app.models.change_request import ChangeRequest
from app.models.deployment import Deployment
from app.models.service import Service
from app.services import audit
from app.services.change_flow import step_event, transition
from app.services.gitops_publish import kustomization_path
from app.services.kustomization import get_tags

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


def validation_expired(change: ChangeRequest, now: datetime) -> bool:
    """True si el cambio lleva más del tiempo de validación esperando a quedar publicado y sano."""
    started = change.approved_at
    if started is None:
        return False
    if started.tzinfo is None:  # SQLite devuelve fechas sin zona
        started = started.replace(tzinfo=timezone.utc)
    return now - started > timedelta(minutes=settings.validation_timeout_minutes)


# Autor que se registra cuando la versión cambió en Git sin pasar por el Hub (spec 005, T25)
MANUAL_AUTHOR = "Cambio manual en Git"
OPEN_STATUSES = ("pendiente", "aprobada", "en_validacion")


def reconcile_version(
    db: Session, service: Service, status: AppStatus, gitea, now: datetime, head: str
) -> bool:
    """Alinea la versión del Hub con la que tiene Git cuando alguien la cambia o revierte a mano.

    Solo actúa si el servicio no tiene un cambio del Hub en curso y Argo CD ya aplicó el último commit
    de la rama (`head`): `Synced` por sí solo habla de la revisión anterior, y fiarse de él anunciaría
    una versión que el clúster todavía no tiene. Devuelve True si cambió la versión.
    """
    if status.sync != "Synced" or (status.revision or "").lower() != head.lower():
        return False
    open_change = db.scalar(
        select(ChangeRequest.id).where(
            ChangeRequest.service_id == service.id, ChangeRequest.status.in_(OPEN_STATUSES)
        )
    )
    if open_change is not None:
        return False
    try:
        file = gitea.get_file(kustomization_path(service.namespace))
    except GiteaError as error:
        logger.warning("No se pudo leer la versión de %s en Git: %s", service.namespace, error)
        return False
    tags = set(get_tags(file.text))
    if len(tags) != 1:
        return False  # web y api con versiones distintas: no se adivina
    tag = tags.pop()
    if tag == service.current_version:
        return False

    # Volver a una versión que el sitio ya tuvo es una restauración; cualquier otra, un cambio
    previous = set(
        db.scalars(select(Deployment.version).where(Deployment.service_id == service.id)).all()
    ) | set(
        db.scalars(select(ChangeRequest.from_version).where(ChangeRequest.service_id == service.id)).all()
    )
    service.current_version = tag
    if status.health == "Healthy":
        service.stable_version = tag
    db.add(
        Deployment(
            service_id=service.id,
            version=tag,
            commit_sha=status.revision,
            author=MANUAL_AUTHOR,
            source="rollback" if tag in previous else "cambio",
            created_at=now,
        )
    )
    return True


def check_cycle(db: Session, argocd, now: datetime | None = None, gitea=None) -> list[int]:
    """Una vuelta: refresca sincronización y salud de cada servicio y confirma los cambios listos.

    `argocd` es cualquier objeto con `get_application(nombre) -> AppStatus`. Devuelve los ids de las
    solicitudes que pasaron a `desplegada`. Un fallo con un servicio no frena a los demás.
    """
    timestamp = now or datetime.now(timezone.utc)
    deployed: list[int] = []
    head = None
    if gitea is not None:
        try:
            head = gitea.head_sha()  # una consulta por vuelta, no una por servicio
        except GiteaError as error:
            logger.warning("No se pudo leer la rama de hub-gitops: %s", error)
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
                if validation_expired(change, timestamp):
                    transition(change, "fallida", actor_id=change.approved_by_id, now=timestamp)
                    logger.warning(
                        "El cambio #%s de %s no quedó publicado a tiempo (sincronización %s, salud %s)",
                        change.id, service.namespace, status.sync, status.health,
                    )
                    # Lo hace el sistema, no una persona (spec 007)
                    audit.record(
                        db, None, "fallar", "change_request", change.id,
                        {"a": change.to_version, "sincronizacion": status.sync, "salud": status.health},
                    )
                    db.add(
                        step_event(
                            change, "en_validacion", change.approved_by_id,
                            "Hubo un problema al publicar la actualización; nuestro equipo lo está revisando.",
                        )
                    )
                continue
            approver = change.approved_by
            transition(change, "desplegada", actor_id=change.approved_by_id, now=timestamp)
            service.current_version = change.to_version
            service.stable_version = change.to_version
            audit.record(
                db, None, "desplegar", "change_request", change.id,
                {"a": change.to_version, "commit": (change.gitops_commit_sha or "")[:7]},
            )
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
                    "Publicamos la actualización que usted solicitó.",
                )
            )
            deployed.append(change.id)
        if head is not None:
            reconcile_version(db, service, status, gitea, timestamp, head)
    db.commit()
    return deployed


async def watch_forever(
    session_factory: Callable[[], Session],
    argocd,
    interval: float = INTERVAL_SECONDS,
    gitea=None,
) -> None:
    """Corre `check_cycle` cada `interval` segundos hasta que se cancele la tarea."""

    def once() -> None:
        with session_factory() as db:
            check_cycle(db, argocd, gitea=gitea)

    while True:
        try:
            await asyncio.to_thread(once)
        except Exception:  # la vigilancia nunca debe tumbar la API
            logger.exception("Falló una vuelta del seguimiento de Argo CD")
        await asyncio.sleep(interval)

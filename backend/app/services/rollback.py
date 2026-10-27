# Reglas del rollback de un incidente: a qué versión se vuelve, si se puede y en qué estado va (spec 009, T02-T08).
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.argocd import AppStatus
from app.models.change_request import ChangeRequest
from app.models.deployment import Deployment
from app.models.incident import Incident
from app.models.service import Service
from app.models.user import User
from app.services.change_flow import step_event, transition

NO_TARGET = "No hay una versión anterior a la que volver."


def running_version(db: Session, service: Service) -> str:
    """Versión que hoy tiene el sitio en Git y en el clúster.

    Un cambio aprobado que espera a Argo CD (`en_validacion`) ya está escrito en Git aunque todavía no
    sea la versión «sana» del Hub: ese es justo el caso de la v2 rota, que nunca llega a `desplegada`.
    """
    pending = db.scalar(
        select(ChangeRequest)
        .where(
            ChangeRequest.service_id == service.id,
            ChangeRequest.status == "en_validacion",
            ChangeRequest.gitops_commit_sha.is_not(None),
        )
        .order_by(ChangeRequest.id.desc())
        .limit(1)
    )
    return pending.to_version if pending is not None else service.current_version


def rollback_target(db: Session, service: Service) -> str | None:
    """Versión a la que se vuelve, o None si no hay a dónde volver (decisión 1 del plan).

    1. Si la última versión estable no es la que corre (la v2 rota nunca estuvo sana), se vuelve a ella.
    2. Si lo son (estuvo sana y se rompió después), se vuelve a la que corría antes en el historial,
       salvo una versión que una restauración posterior ya deshizo: ésa fue la que falló y volver a ella
       repetiría la falla.
    """
    running = running_version(db, service)
    if service.stable_version != running:
        return service.stable_version
    history = db.execute(
        select(Deployment.id, Deployment.version, Deployment.source)
        .where(Deployment.service_id == service.id)
        .order_by(Deployment.id.desc())
    ).all()
    for position, (_, version, _) in enumerate(history):
        if version == running:
            continue
        # `history` va del más nuevo al más viejo: las filas anteriores en la lista son las posteriores en el tiempo
        undone = any(later_source == "rollback" and later_version != version for _, later_version, later_source in history[:position])
        if not undone:
            return version
    return None


def in_progress(incident: Incident) -> bool:
    """Hay un commit de rollback que Argo CD todavía no confirmó."""
    return incident.rollback_commit_sha is not None and incident.rollback_confirmed_at is None


def service_in_progress(db: Session, service_id: int) -> bool:
    """Algún incidente del servicio tiene un rollback sin confirmar (CA-8: uno a la vez por servicio)."""
    return (
        db.scalar(
            select(Incident.id)
            .where(
                Incident.service_id == service_id,
                Incident.rollback_commit_sha.is_not(None),
                Incident.rollback_confirmed_at.is_(None),
            )
            .limit(1)
        )
        is not None
    )


def block_reason(db: Session, incident: Incident) -> str | None:
    """Por qué no se puede pedir el rollback ahora; None si se puede (CA-1, CA-8)."""
    if incident.status != "abierto":
        return "El incidente ya no está abierto."
    if incident.rollback_commit_sha is not None:
        if incident.rollback_confirmed_at is None:
            return "Ya hay un rollback en curso."
        return "El rollback ya se confirmó en Argo CD; si el sitio no responde, revisa la causa o mitiga a mano."
    if service_in_progress(db, incident.service_id):
        return "Ya hay un rollback en curso sobre este servicio."
    if rollback_target(db, incident.service) is None:
        return NO_TARGET
    return None


def plan(db: Session, incident: Incident) -> dict:
    """Lo que ve el técnico antes de confirmar: versión actual, destino y si el botón está activo."""
    if incident.rollback_commit_sha is not None:
        current, target = incident.rollback_from_version, incident.rollback_to_version
    else:
        current = running_version(db, incident.service)
        target = rollback_target(db, incident.service)
    reason = block_reason(db, incident)
    return {
        "current_version": current,
        "target_version": target,
        "can_rollback": reason is None,
        "reason": reason,
    }


def status(incident: Incident, app_status: AppStatus | None) -> str:
    """Avance del rollback: sin_rollback → enviado → sincronizando → recuperado (derivado, no guardado).

    `sincronizando` es que Argo CD ya está en la revisión del commit de rollback pero el sitio aún no
    está sano. Sin respuesta de Argo CD (`app_status=None`) se queda en `enviado`.
    """
    if incident.rollback_commit_sha is None:
        return "sin_rollback"
    if incident.rollback_confirmed_at is not None:
        return "recuperado"
    if app_status is not None and (app_status.revision or "").lower() == incident.rollback_commit_sha.lower():
        return "sincronizando"
    return "enviado"


def fail_pending_change(db: Session, incident: Incident, broken_version: str, actor: User, now: datetime | None = None) -> int | None:
    """El cambio `en_validacion` hacia la versión rota pasa a `fallida` con una nota que remite al incidente (CA-6).

    Si no lo hiciera, su plazo de validación vencería después y lo marcaría fallido sin explicación.
    `fallida` no cuenta como cambio abierto, así que no bloquea cambios posteriores. Devuelve su id.
    """
    change = db.scalar(
        select(ChangeRequest)
        .where(
            ChangeRequest.service_id == incident.service_id,
            ChangeRequest.status == "en_validacion",
            ChangeRequest.to_version == broken_version,
        )
        .order_by(ChangeRequest.id.desc())
        .limit(1)
    )
    if change is None:
        return None
    transition(change, "fallida", actor_id=change.approved_by_id, now=now or datetime.now(timezone.utc))
    # La nota para la agencia remite al incidente; la del cliente usa el glosario («Rollback»)
    db.add(step_event(change, "en_validacion", actor.id, f"Revertido por el incidente #{incident.id}", internal=True))
    db.add(
        step_event(
            change, "en_validacion", actor.id,
            "Se restauró una versión estable para mantener la continuidad.",
        )
    )
    return change.id

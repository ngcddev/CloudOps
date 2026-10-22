# Endpoints de solicitudes de cambio de versión: crear y rechazar (spec 005, T13).
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.change_request import ChangeRequest
from app.models.ticket import Ticket
from app.models.user import User
from app.integrations.gitea import GiteaClient, GiteaError, gitea_from_settings
from app.schemas.change_request import (
    ChangeRequestApprove,
    ChangeRequestCreate,
    ChangeRequestOut,
    ChangeRequestReject,
)
from app.services.change_flow import step_event, transition
from app.services.gitops_publish import (
    NothingToPublish,
    find_existing_publication,
    kustomization_path,
    publish_version,
)

router = APIRouter(prefix="/api/change-requests", tags=["change-requests"])

# Estados en los que un cambio sigue "en curso" y bloquea otro sobre el mismo servicio
OPEN_STATUSES = ("pendiente", "aprobada", "en_validacion")


def get_gitea() -> GiteaClient:
    """Cliente de Gitea con la configuración del entorno (las pruebas lo reemplazan)."""
    try:
        return gitea_from_settings()
    except GiteaError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


def get_change_or_404(db: Session, change_id: int) -> ChangeRequest:
    change = db.get(ChangeRequest, change_id)
    if change is None:
        raise HTTPException(status_code=404, detail="La solicitud de cambio no existe.")
    return change


def require_user(db: Session, user_id: int | None, message: str) -> None:
    if user_id is not None and db.get(User, user_id) is None:
        raise HTTPException(status_code=404, detail=message)


@router.get("", response_model=list[ChangeRequestOut])
def list_change_requests(
    status_filter: str | None = Query(default=None, alias="status"),
    service_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Bandeja de solicitudes de cambio, de la más reciente a la más antigua."""
    query = select(ChangeRequest)
    if status_filter is not None:
        query = query.where(ChangeRequest.status == status_filter)
    if service_id is not None:
        query = query.where(ChangeRequest.service_id == service_id)
    return db.scalars(query.order_by(ChangeRequest.id.desc())).all()


@router.post("", response_model=ChangeRequestOut, status_code=status.HTTP_201_CREATED)
def create_change_request(data: ChangeRequestCreate, db: Session = Depends(get_db)):
    """Registra una solicitud de cambio de versión, vinculada a una solicitud de tipo `cambio`."""
    ticket = db.get(Ticket, data.ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="La solicitud no existe.")
    if ticket.kind != "cambio":
        raise HTTPException(status_code=422, detail="La solicitud debe ser de tipo cambio.")
    require_user(db, data.requested_by_id, "El usuario que pide el cambio no existe.")

    service = ticket.service
    if data.to_version == service.current_version:
        raise HTTPException(status_code=422, detail=f"El sitio ya está en la versión {data.to_version}.")
    in_progress = db.scalar(
        select(ChangeRequest.id).where(
            ChangeRequest.service_id == service.id, ChangeRequest.status.in_(OPEN_STATUSES)
        )
    )
    if in_progress is not None:
        raise HTTPException(status_code=409, detail="Ya hay un cambio en curso para este sitio.")

    change = ChangeRequest(
        ticket_id=ticket.id,
        service_id=service.id,
        from_version=service.current_version,
        to_version=data.to_version,
        status="pendiente",
        requested_by_id=data.requested_by_id,
    )
    db.add(change)
    db.flush()
    db.add(
        step_event(
            change, None, data.requested_by_id,
            f"Recibimos su solicitud para cambiar el sitio de {change.from_version} a {change.to_version}.",
        )
    )
    db.commit()
    db.refresh(change)
    return change


@router.post("/{change_id}/reject", response_model=ChangeRequestOut)
def reject_change_request(change_id: int, data: ChangeRequestReject, db: Session = Depends(get_db)):
    """Rechaza una solicitud pendiente; el motivo es obligatorio."""
    change = get_change_or_404(db, change_id)
    require_user(db, data.actor_id, "El usuario que rechaza no existe.")

    previous = change.status
    try:
        transition(change, "rechazada", reason=data.reason)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    db.add(step_event(change, previous, data.actor_id, data.reason))
    db.commit()
    db.refresh(change)
    return change


@router.post("/{change_id}/approve", response_model=ChangeRequestOut)
def approve_change_request(
    change_id: int,
    data: ChangeRequestApprove,
    db: Session = Depends(get_db),
    gitea: GiteaClient = Depends(get_gitea),
):
    """Aprueba el cambio: escribe la versión en hub-gitops y lo deja en `en_validacion`.

    El Hub solo escribe el tag en Gitea (CA-2); Argo CD aplica el cambio y la tarea periódica
    confirma la publicación. Si Gitea falla, la solicitud sigue pendiente.
    """
    change = get_change_or_404(db, change_id)
    approver = db.get(User, data.actor_id)
    if approver is None:
        raise HTTPException(status_code=404, detail="El usuario que aprueba no existe.")
    if approver.role != "agencia":
        raise HTTPException(status_code=403, detail="Solo la agencia puede aprobar cambios.")
    if change.status != "pendiente":
        raise HTTPException(
            status_code=409,
            detail=f"No se permite pasar de «{change.status}» a «aprobada».",
        )

    try:
        kustomization_path(change.service.namespace)  # namespace que no es de un cliente: no se escribe nada
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    try:
        sha = publish_version(
            gitea,
            change.service.namespace,
            change.to_version,
            change.id,
            approver.name,
            approver.email,
        )
    except NothingToPublish as error:
        # Puede ser una aprobación anterior que escribió en Gitea y no alcanzó a guardarse: se adopta
        try:
            sha = find_existing_publication(gitea, change.service.namespace, change.to_version, change.id)
        except GiteaError as gitea_error:
            raise HTTPException(
                status_code=502, detail=f"No se pudo publicar en Gitea: {gitea_error}"
            ) from gitea_error
        if sha is None:
            raise HTTPException(status_code=409, detail=str(error)) from error
    except GiteaError as error:
        raise HTTPException(status_code=502, detail=f"No se pudo publicar en Gitea: {error}") from error

    # aprobada y en_validacion ocurren en el mismo instante: el commit ya está escrito
    transition(change, "aprobada", actor_id=approver.id)
    db.add(step_event(change, "pendiente", approver.id, "Su solicitud fue aprobada."))
    transition(change, "en_validacion", actor_id=approver.id)
    db.add(
        step_event(
            change, "aprobada", approver.id,
            f"Commit {sha[:7]} en hub-gitops; esperando a que Argo CD sincronice.",
            internal=True,
        )
    )
    change.gitops_commit_sha = sha
    db.commit()
    db.refresh(change)
    return change

# Endpoints de incidentes: abrir a mano, listar, ver, tomar, anotar, mitigar y cerrar (spec 008). Solo agencia.
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.config import settings
from app.integrations.argocd import AppStatus, ArgoCDClient, ArgoCDError, argocd_from_settings
from app.integrations.gitea import GiteaClient, GiteaError
from app.db import get_db
from app.deps import require_agency
from app.models.client import Client
from app.models.incident import Incident
from app.models.incident_event import IncidentEvent
from app.models.project import Project
from app.models.service import Service
from app.models.user import User
from app.routers.change_requests import get_gitea
from app.schemas.incident import (
    ClientMessageOut,
    IncidentCloseIn,
    IncidentCreate,
    IncidentDetail,
    IncidentNoteIn,
    IncidentOut,
    RollbackPlanOut,
)
from app.services import audit
from app.services import incident_alerts, incident_flow, rollback
from app.services.gitops_publish import (
    NothingToPublish,
    find_existing_rollback,
    kustomization_path,
    publish_rollback,
)
from app.services.messages import client_message
from app.services.incident_flow import IncidentFlowError, add_event, mttr_minutes
from app.services.incident_links import build_links, commit_url
from app.services.sla import due_dates, incident_clocks

router = APIRouter(prefix="/api/incidents", tags=["incidentes"], dependencies=[Depends(require_agency)])


def utcnow() -> datetime:
    """Hora actual en UTC; las pruebas la reemplazan para fijar el reloj."""
    return datetime.now(timezone.utc)


def _as_utc(value: datetime | None) -> datetime | None:
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _base_query():
    """Incidentes con su servicio, proyecto, cliente y responsable cargados de una vez (sin N+1)."""
    return select(Incident).options(
        selectinload(Incident.service).selectinload(Service.project).selectinload(Project.client),
        selectinload(Incident.assignee),
    )


def present(incident: Incident, now: datetime | None = None) -> dict:
    """Datos comunes de la lista y el detalle, con el estado de los dos relojes del SLA."""
    response_state, resolution_state = incident_clocks(incident, now or utcnow())
    service = incident.service
    client = service.project.client
    return {
        "id": incident.id,
        "service_id": incident.service_id,
        "client_id": client.id,
        "client_name": client.name,
        "service_name": service.name,
        "namespace": service.namespace,
        "priority": incident.priority,
        "status": incident.status,
        "source": incident.source,
        "title": incident.title,
        "started_at": _as_utc(incident.started_at),
        "acknowledged_at": _as_utc(incident.acknowledged_at),
        "mitigated_at": _as_utc(incident.mitigated_at),
        "closed_at": _as_utc(incident.closed_at),
        "response_due_at": _as_utc(incident.response_due_at),
        "resolution_due_at": _as_utc(incident.resolution_due_at),
        "assignee_id": incident.assignee_id,
        "assignee_name": incident.assignee.name if incident.assignee else None,
        "root_cause": incident.root_cause,
        "response_state": response_state,
        "resolution_state": resolution_state,
        "mttr_minutes": mttr_minutes(incident),
        "created_at": _as_utc(incident.created_at),
    }


@router.post("", response_model=IncidentOut, status_code=status.HTTP_201_CREATED)
def create_incident(
    data: IncidentCreate,
    request: Request,
    db: Session = Depends(get_db),
    actor: User = Depends(require_agency),
):
    """Abre un incidente manual: el reloj del SLA arranca ahora, con la prioridad elegida."""
    service = db.get(Service, data.service_id)
    if service is None:
        raise HTTPException(status_code=404, detail="El servicio no existe.")
    started_at = utcnow()
    response_due_at, resolution_due_at = due_dates(started_at, data.priority, service.plan)
    incident = Incident(
        service_id=service.id,
        priority=data.priority,
        status="abierto",
        source="manual",
        title=data.title,
        started_at=started_at,
        response_due_at=response_due_at,
        resolution_due_at=resolution_due_at,
        created_by_id=actor.id,
    )
    db.add(incident)
    add_event(incident, "detectado", f"Abierto a mano por {actor.name}.", actor, at=started_at)
    db.flush()
    audit.record(
        db, actor, "crear", "incident", incident.id,
        {"prioridad": data.priority, "servicio": service.namespace, "origen": "manual"},
        audit.request_ip(request),
    )
    db.commit()
    return present(db.scalar(_base_query().where(Incident.id == incident.id)))


@router.get("", response_model=list[IncidentOut])
def list_incidents(
    status_filter: str | None = Query(default=None, alias="status"),
    client_id: int | None = Query(default=None),
    priority: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Lista los incidentes, los más recientes primero, con filtros por estado, cliente y prioridad."""
    query = _base_query().join(Incident.service).join(Service.project)
    if status_filter is not None:
        query = query.where(Incident.status == status_filter)
    if client_id is not None:
        query = query.where(Project.client_id == client_id)
    if priority is not None:
        query = query.where(Incident.priority == priority)
    now = utcnow()
    return [present(incident, now) for incident in db.scalars(query.order_by(Incident.id.desc()))]


def _load(db: Session, incident_id: int) -> Incident:
    """Incidente con su línea de tiempo y quién hizo cada evento, o 404."""
    incident = db.scalar(
        _base_query()
        .options(selectinload(Incident.events).selectinload(IncidentEvent.actor), selectinload(Incident.rollback_by))
        .where(Incident.id == incident_id)
    )
    if incident is None:
        raise HTTPException(status_code=404, detail="El incidente no existe.")
    return incident


def get_argocd() -> ArgoCDClient | None:
    """Cliente de Argo CD para ver el avance del rollback; None si no está configurado (las pruebas lo reemplazan)."""
    try:
        return argocd_from_settings()
    except ArgoCDError:
        return None


def _app_status(argocd: ArgoCDClient | None, incident: Incident) -> AppStatus | None:
    """Estado de Argo CD del sitio, solo mientras hay un rollback sin confirmar; un fallo no tumba el detalle."""
    if argocd is None or not rollback.in_progress(incident):
        return None
    try:
        return argocd.get_application(incident.service.namespace)
    except ArgoCDError:
        return None


def present_rollback(incident: Incident, app_status: AppStatus | None) -> dict:
    """Bloque `rollback` del detalle: avance, versiones, quién lo pidió y el commit en Gitea."""
    return {
        "status": rollback.status(incident, app_status),
        "from_version": incident.rollback_from_version,
        "to_version": incident.rollback_to_version,
        "by_name": incident.rollback_by.name if incident.rollback_by else None,
        "at": _as_utc(incident.rollback_at),
        "confirmed_at": _as_utc(incident.rollback_confirmed_at),
        "commit_sha": incident.rollback_commit_sha,
        "commit_url": commit_url(settings.gitea_public_url, settings.gitea_repo, incident.rollback_commit_sha),
    }


def present_detail(
    db: Session, incident: Incident, now: datetime | None = None, app_status: AppStatus | None = None
) -> dict:
    """Detalle del incidente: los datos de la lista, la línea de tiempo en orden, los enlaces y el rollback."""
    data = present(incident, now)
    data.update(build_links(db, incident, settings.grafana_url, settings.gitea_public_url, settings.gitea_repo))
    data["rollback"] = present_rollback(incident, app_status)
    data["events"] = [
        {
            "id": event.id,
            "type": event.type,
            "message": event.message,
            "actor_name": event.actor_name,
            "created_at": _as_utc(event.created_at),
        }
        for event in incident.events
    ]
    return data


@router.get("/{incident_id}", response_model=IncidentDetail)
def get_incident(
    incident_id: int, db: Session = Depends(get_db), argocd: ArgoCDClient | None = Depends(get_argocd)
):
    """Detalle del incidente con su línea de tiempo, el estado de los relojes del SLA y el avance del rollback."""
    incident = _load(db, incident_id)
    return present_detail(db, incident, app_status=_app_status(argocd, incident))


@router.get("/{incident_id}/rollback-plan", response_model=RollbackPlanOut)
def get_rollback_plan(incident_id: int, db: Session = Depends(get_db)):
    """Versión actual, versión a la que se vuelve y si el botón está activo (con la razón si no lo está)."""
    return rollback.plan(db, _load(db, incident_id))


@router.post("/{incident_id}/rollback", response_model=IncidentDetail)
def rollback_incident(
    incident_id: int,
    request: Request,
    db: Session = Depends(get_db),
    gitea: GiteaClient = Depends(get_gitea),
    actor: User = Depends(require_agency),
):
    """Pide el rollback: escribe en hub-gitops el commit que deja el sitio en la última versión estable.

    El Hub no toca el clúster ni acepta el actor en el cuerpo: el commit y la bitácora salen a nombre de
    la sesión, y Argo CD hace el resto (principios 3 y 5). Un solo rollback a la vez por servicio (CA-8).
    """
    # Bloquea la fila del incidente (en PostgreSQL) mientras se decide: dos clics o dos técnicos se turnan
    db.execute(select(Incident.id).where(Incident.id == incident_id).with_for_update())
    incident = _load(db, incident_id)
    reason = rollback.block_reason(db, incident)
    if reason is not None:
        raise HTTPException(status_code=409, detail=reason)
    service = incident.service
    broken_version = rollback.running_version(db, service)
    target = rollback.rollback_target(db, service)
    try:
        kustomization_path(service.namespace)  # namespace que no es de un cliente: no se escribe nada
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    try:
        sha = publish_rollback(gitea, service.namespace, target, incident.id, actor.name, actor.email)
    except NothingToPublish as error:
        # O un rollback anterior que escribió en Gitea y no alcanzó a guardarse (se adopta), o alguien que
        # revirtió a mano: entonces solo falta esperar a Argo CD
        try:
            sha = find_existing_rollback(gitea, service.namespace, target, incident.id)
        except GiteaError as gitea_error:
            raise HTTPException(status_code=502, detail=f"No se pudo escribir en Gitea: {gitea_error}") from gitea_error
        if sha is None:
            raise HTTPException(
                status_code=409,
                detail=f"El repositorio ya tiene la versión {target}; solo falta esperar a que Argo CD sincronice.",
            ) from error
    except GiteaError as error:
        # Incluye la segunda escritura de un doble clic: Gitea la rechaza porque el blob ya cambió
        raise HTTPException(status_code=502, detail=f"No se pudo escribir en Gitea: {error}") from error

    now = utcnow()
    incident.rollback_from_version = broken_version
    incident.rollback_to_version = target
    incident.rollback_commit_sha = sha
    incident.rollback_by_id = actor.id
    incident.rollback_at = now
    add_event(
        incident, "rollback_enviado",
        f"{actor.name} pidió volver de {broken_version} a {target}; commit {sha[:7]} en hub-gitops.",
        actor, at=now,
    )
    failed_change = rollback.fail_pending_change(db, incident, broken_version, actor, now)
    audit.record(
        db, actor, "rollback", "incident", incident.id,
        {"desde": broken_version, "hacia": target, "commit": sha[:7], "cambio_fallido": failed_change},
        audit.request_ip(request),
    )
    db.commit()
    return present_detail(db, _load(db, incident_id), now)


@router.get("/{incident_id}/client-message", response_model=ClientMessageOut)
def get_client_message(incident_id: int, db: Session = Depends(get_db)):
    """Mensaje para el cliente con las horas reales; solo cuando el incidente ya se mitigó y nunca se envía solo."""
    try:
        return {"message": client_message(_load(db, incident_id))}
    except IncidentFlowError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.post("/{incident_id}/acknowledge", response_model=IncidentDetail)
def acknowledge_incident(
    incident_id: int,
    request: Request,
    db: Session = Depends(get_db),
    actor: User = Depends(require_agency),
):
    """Tomar el incidente: cumple el reloj de respuesta y deja al técnico como responsable."""
    incident = _load(db, incident_id)
    now = utcnow()
    try:
        incident_flow.acknowledge(incident, actor, now)
    except IncidentFlowError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    add_event(incident, "tomado", f"Tomado por {actor.name}.", actor, at=now)
    audit.record(db, actor, "tomar", "incident", incident.id, None, audit.request_ip(request))
    db.commit()
    return present_detail(db, _load(db, incident_id), now)


@router.post("/{incident_id}/notes", response_model=IncidentDetail, status_code=status.HTTP_201_CREATED)
def add_note(
    incident_id: int,
    data: IncidentNoteIn,
    db: Session = Depends(get_db),
    actor: User = Depends(require_agency),
):
    """Agrega una nota del técnico a la línea de tiempo (lo que revisó, lo que probó)."""
    incident = _load(db, incident_id)
    if incident.status == "cerrado":
        raise HTTPException(status_code=409, detail="El incidente ya está cerrado.")
    now = utcnow()
    add_event(incident, "nota", data.message, actor, at=now)
    db.commit()
    return present_detail(db, _load(db, incident_id), now)


@router.post("/{incident_id}/mitigate", response_model=IncidentDetail)
def mitigate_incident(
    incident_id: int,
    request: Request,
    db: Session = Depends(get_db),
    actor: User = Depends(require_agency),
):
    """Mitiga a mano un incidente manual, o uno de alerta cuyo rollback ya se confirmó; detiene el reloj de solución."""
    incident = _load(db, incident_id)
    now = utcnow()
    try:
        incident_flow.mitigate(incident, now)
    except IncidentFlowError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    by_rollback = incident.source == "alerta"
    message = (
        f"Mitigado a mano por {actor.name}: el rollback ya se confirmó en Argo CD."
        if by_rollback
        else f"Mitigado a mano por {actor.name}."
    )
    add_event(incident, "recuperado", message, actor, at=now)
    if by_rollback:
        incident_alerts.restore_service(db, incident)  # el sitio vuelve a `operativo` (CA-4)
    audit.record(
        db, actor, "mitigar", "incident", incident.id,
        {"origen": "rollback_confirmado" if by_rollback else "manual"}, audit.request_ip(request),
    )
    db.commit()
    return present_detail(db, _load(db, incident_id), now)


@router.post("/{incident_id}/close", response_model=IncidentDetail)
def close_incident(
    incident_id: int,
    data: IncidentCloseIn,
    request: Request,
    db: Session = Depends(get_db),
    actor: User = Depends(require_agency),
):
    """Cierra un incidente mitigado dejando la causa raíz como lección."""
    incident = _load(db, incident_id)
    now = utcnow()
    try:
        incident_flow.close(incident, data.root_cause, now)
    except IncidentFlowError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    add_event(incident, "cerrado", f"Cerrado por {actor.name}. Causa raíz: {incident.root_cause}", actor, at=now)
    audit.record(db, actor, "cerrar", "incident", incident.id, None, audit.request_ip(request))
    db.commit()
    return present_detail(db, _load(db, incident_id), now)

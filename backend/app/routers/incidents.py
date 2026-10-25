# Endpoints de incidentes: abrir a mano, listar, ver, tomar, anotar, mitigar y cerrar (spec 008). Solo agencia.
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.deps import require_agency
from app.models.client import Client
from app.models.incident import Incident
from app.models.incident_event import IncidentEvent
from app.models.project import Project
from app.models.service import Service
from app.models.user import User
from app.schemas.incident import IncidentCreate, IncidentDetail, IncidentOut
from app.services import audit
from app.services.incident_flow import add_event
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
        .options(selectinload(Incident.events).selectinload(IncidentEvent.actor))
        .where(Incident.id == incident_id)
    )
    if incident is None:
        raise HTTPException(status_code=404, detail="El incidente no existe.")
    return incident


def present_detail(incident: Incident, now: datetime | None = None) -> dict:
    """Detalle del incidente: los datos de la lista más la línea de tiempo en orden."""
    data = present(incident, now)
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
def get_incident(incident_id: int, db: Session = Depends(get_db)):
    """Detalle del incidente con su línea de tiempo y el estado de los relojes del SLA."""
    return present_detail(_load(db, incident_id))

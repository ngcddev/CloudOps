# Endpoints de clientes: crear, listar, ver y editar (spec 001, T06). Con sesión y alcance por cliente (spec 007).
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.deps import client_scope, current_user, require_agency
from app.models.agency import Agency
from app.models.client import Client
from app.models.plan import Plan
from app.models.project import Project
from app.models.service import Service
from app.models.sla_policy import SlaPolicy
from app.models.user import User
from app.schemas.client import (
    ClientCreate,
    ClientDetail,
    ClientOut,
    ClientSummary,
    ClientUpdate,
    ProjectCreate,
    ProjectOut,
    ServiceCreate,
    ServiceOut,
)
from app.schemas.sla_policy import SlaPolicyOut
from app.services import audit

router = APIRouter(prefix="/api/clients", tags=["clientes"])
projects_router = APIRouter(prefix="/api", tags=["proyectos"])


def _get_or_404(db: Session, client_id: int) -> Client:
    client = db.get(Client, client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="El cliente no existe.")
    return client


def _get_visible_or_404(db: Session, client_id: int, user: User) -> Client:
    """Un cliente solo ve el suyo; pedir otro responde igual que si no existiera."""
    scope = client_scope(user)
    if scope is not None and scope != client_id:
        raise HTTPException(status_code=404, detail="El cliente no existe.")
    return _get_or_404(db, client_id)


@router.get("", response_model=list[ClientSummary])
def list_clients(db: Session = Depends(get_db), user: User = Depends(current_user)):
    """Lista los clientes, del más antiguo al más reciente (un cliente solo ve el suyo)."""
    query = select(Client).options(
        selectinload(Client.projects).selectinload(Project.services).selectinload(Service.plan)
    )
    scope = client_scope(user)
    if scope is not None:
        query = query.where(Client.id == scope)
    return db.scalars(query.order_by(Client.id)).all()


@router.post("", response_model=ClientOut, status_code=status.HTTP_201_CREATED)
def create_client(
    data: ClientCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_agency),
):
    """Crea un cliente de la agencia; solo el nombre es obligatorio."""
    client = Client(agency_id=db.scalar(select(Agency.id).order_by(Agency.id)), **data.model_dump())
    db.add(client)
    db.flush()
    audit.record(db, user, "crear", "client", client.id, {"name": client.name}, audit.request_ip(request))
    db.commit()
    db.refresh(client)
    return client


@router.get("/{client_id}", response_model=ClientDetail)
def get_client(client_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    """Detalle de un cliente con sus proyectos, servicios, plan y los tiempos de SLA."""
    detail = ClientDetail.model_validate(_get_visible_or_404(db, client_id, user))
    policies = db.scalars(select(SlaPolicy).order_by(SlaPolicy.priority)).all()
    detail.sla_policies = [SlaPolicyOut.model_validate(policy) for policy in policies]
    return detail


@router.patch("/{client_id}", response_model=ClientOut)
def update_client(
    client_id: int,
    data: ClientUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_agency),
):
    """Edita solo los campos enviados."""
    client = _get_or_404(db, client_id)
    changes = data.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(client, field, value)
    audit.record(db, user, "editar", "client", client.id, {"campos": sorted(changes)}, audit.request_ip(request))
    db.commit()
    db.refresh(client)
    return client


@router.post("/{client_id}/projects", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    client_id: int,
    data: ProjectCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_agency),
):
    """Crea un proyecto perteneciente al cliente indicado."""
    client = _get_or_404(db, client_id)
    project = Project(client_id=client.id, **data.model_dump())
    db.add(project)
    db.flush()
    audit.record(
        db, user, "crear", "project", project.id,
        {"cliente": client.name, "name": project.name}, audit.request_ip(request),
    )
    db.commit()
    db.refresh(project)
    return project


@projects_router.post("/projects/{project_id}/services", response_model=ServiceOut, status_code=status.HTTP_201_CREATED)
def create_service(
    project_id: int,
    data: ServiceCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_agency),
):
    """Crea un servicio y verifica que el plan exista."""
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="El proyecto no existe.")
    plan = db.get(Plan, data.plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="El plan no existe.")
    # Cada sitio tiene su propia dirección y su propio namespace: no se pueden repetir.
    if db.scalar(select(Service).where(Service.host == data.host)) is not None:
        raise HTTPException(status_code=409, detail="Ya existe un servicio con esa dirección (host).")
    if db.scalar(select(Service).where(Service.namespace == data.namespace)) is not None:
        raise HTTPException(status_code=409, detail="Ya existe un servicio con ese namespace.")
    service = Service(project_id=project.id, plan_id=plan.id, **data.model_dump(exclude={"plan_id"}))
    db.add(service)
    db.flush()
    audit.record(
        db, user, "crear", "service", service.id,
        {"name": service.name, "host": service.host, "namespace": service.namespace},
        audit.request_ip(request),
    )
    db.commit()
    db.refresh(service)
    return service

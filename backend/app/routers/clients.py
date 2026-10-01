# Endpoints de clientes: crear, listar, ver y editar (spec 001, T06).
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.client import Client
from app.models.plan import Plan
from app.models.project import Project
from app.models.service import Service
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

router = APIRouter(prefix="/api/clients", tags=["clientes"])
projects_router = APIRouter(prefix="/api", tags=["proyectos"])


def _get_or_404(db: Session, client_id: int) -> Client:
    client = db.get(Client, client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="El cliente no existe.")
    return client


@router.get("", response_model=list[ClientSummary])
def list_clients(db: Session = Depends(get_db)):
    """Lista los clientes, del más antiguo al más reciente."""
    return db.scalars(select(Client).order_by(Client.id)).all()


@router.post("", response_model=ClientOut, status_code=status.HTTP_201_CREATED)
def create_client(data: ClientCreate, db: Session = Depends(get_db)):
    """Crea un cliente; solo el nombre es obligatorio."""
    client = Client(**data.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.get("/{client_id}", response_model=ClientDetail)
def get_client(client_id: int, db: Session = Depends(get_db)):
    """Detalle de un cliente."""
    return _get_or_404(db, client_id)


@router.patch("/{client_id}", response_model=ClientOut)
def update_client(client_id: int, data: ClientUpdate, db: Session = Depends(get_db)):
    """Edita solo los campos enviados."""
    client = _get_or_404(db, client_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(client, field, value)
    db.commit()
    db.refresh(client)
    return client


@router.post("/{client_id}/projects", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(client_id: int, data: ProjectCreate, db: Session = Depends(get_db)):
    """Crea un proyecto perteneciente al cliente indicado."""
    client = _get_or_404(db, client_id)
    project = Project(client_id=client.id, **data.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@projects_router.post("/projects/{project_id}/services", response_model=ServiceOut, status_code=status.HTTP_201_CREATED)
def create_service(project_id: int, data: ServiceCreate, db: Session = Depends(get_db)):
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
    db.commit()
    db.refresh(service)
    return service

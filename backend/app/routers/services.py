# Endpoints del estado de los servicios y su historial de versiones (spec 005, T16).
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.change_request import ChangeRequest
from app.models.client import Client
from app.models.deployment import Deployment
from app.models.project import Project
from app.models.service import Service
from app.routers.change_requests import OPEN_STATUSES
from app.schemas.service_status import DeploymentOut, ServiceStatusOut

router = APIRouter(prefix="/api/services", tags=["services"])


@router.get("/status", response_model=list[ServiceStatusOut])
def services_status(db: Session = Depends(get_db)):
    """Versión activa, sincronización, salud y último autor de cada servicio."""
    rows = db.execute(
        select(Service, Client).join(Project, Service.project_id == Project.id)
        .join(Client, Project.client_id == Client.id).order_by(Service.id)
    ).all()
    result = []
    for service, client in rows:
        last = db.scalar(
            select(Deployment).where(Deployment.service_id == service.id).order_by(Deployment.id.desc()).limit(1)
        )
        open_change = db.scalar(
            select(ChangeRequest)
            .where(ChangeRequest.service_id == service.id, ChangeRequest.status.in_(OPEN_STATUSES))
            .order_by(ChangeRequest.id.desc())
            .limit(1)
        )
        result.append(
            ServiceStatusOut(
                service_id=service.id,
                client_id=client.id,
                client_name=client.name,
                service_name=service.name,
                host=service.host,
                namespace=service.namespace,
                current_version=service.current_version,
                stable_version=service.stable_version,
                sync_status=service.sync_status,
                health_status=service.health_status,
                last_author=last.author if last else None,
                last_change_at=last.created_at if last else None,
                open_change_id=open_change.id if open_change else None,
                open_change_status=open_change.status if open_change else None,
                open_change_to_version=open_change.to_version if open_change else None,
            )
        )
    return result


@router.get("/{service_id}/deployments", response_model=list[DeploymentOut])
def service_deployments(service_id: int, db: Session = Depends(get_db)):
    """Historial de versiones publicadas del servicio, de la más reciente a la más antigua."""
    if db.get(Service, service_id) is None:
        raise HTTPException(status_code=404, detail="El servicio no existe.")
    return db.scalars(
        select(Deployment).where(Deployment.service_id == service_id).order_by(Deployment.id.desc())
    ).all()

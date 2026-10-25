# Endpoints del estado de los servicios y su historial de versiones (spec 005, T16). Solo agencia (spec 007).
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import require_agency
from app.models.change_request import ChangeRequest
from app.models.client import Client
from app.models.deployment import Deployment
from app.models.incident import Incident
from app.models.project import Project
from app.models.security_run import SecurityRun
from app.models.service import Service
from app.routers.change_requests import OPEN_STATUSES
from app.schemas.service_status import DeploymentOut, ServiceStatusOut

router = APIRouter(prefix="/api/services", tags=["services"], dependencies=[Depends(require_agency)])


@router.get("/status", response_model=list[ServiceStatusOut])
def services_status(db: Session = Depends(get_db)):
    """Versión activa, sincronización, salud, último autor y si está caído, de cada servicio."""
    rows = db.execute(
        select(Service, Client).join(Project, Service.project_id == Project.id)
        .join(Client, Project.client_id == Client.id).order_by(Service.id)
    ).all()
    # Dos consultas para todos los servicios, no dos por servicio: el último despliegue de cada uno y su
    # cambio en curso (si hay varios, el más reciente)
    last_by_service = {
        deployment.service_id: deployment
        for deployment in db.scalars(
            select(Deployment).where(
                Deployment.id.in_(select(func.max(Deployment.id)).group_by(Deployment.service_id))
            )
        )
    }
    open_by_service = {
        change.service_id: change
        for change in db.scalars(
            select(ChangeRequest).where(ChangeRequest.status.in_(OPEN_STATUSES)).order_by(ChangeRequest.id)
        )
    }
    # La puerta de seguridad (spec 006): la última corrida de cada versión, en una sola consulta
    latest_runs = {
        (run.service_id, run.version): run
        for run in db.scalars(
            select(SecurityRun).where(
                SecurityRun.id.in_(select(func.max(SecurityRun.id)).group_by(SecurityRun.service_id, SecurityRun.version))
            )
        )
    }
    # Monitoreo (spec 008): servicios con un incidente de alerta abierto, en una sola consulta
    down = set(
        db.scalars(select(Incident.service_id).where(Incident.source == "alerta", Incident.status == "abierto"))
    )
    result = []
    for service, client in rows:
        last = last_by_service.get(service.id)
        run = latest_runs.get((service.id, service.current_version))
        open_change = open_by_service.get(service.id)
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
                security_status=run.status if run else "sin_corrida",
                security_failed_step=run.failed_step if run else None,
                service_status="caido" if service.id in down else "operativo",
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

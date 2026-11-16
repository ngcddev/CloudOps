# Endpoints del estado de los servicios y su historial de versiones (spec 005, T16). Solo agencia (spec 007).
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db, soltar_conexion
from app.deps import require_agency
from app.integrations.gitea import GiteaClient, GiteaError
from app.models.change_request import ChangeRequest
from app.models.client import Client
from app.models.deployment import Deployment
from app.models.incident import Incident
from app.models.project import Project
from app.models.security_run import SecurityRun
from app.models.service import Service
from app.models.user import User
from app.routers.change_requests import OPEN_STATUSES, get_gitea
from app.services import audit, provisioning
from app.schemas.service_status import DeploymentOut, ProvisionOut, ServiceStatusOut

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


@router.post("/{service_id}/provision", response_model=ProvisionOut, status_code=201)
def provision_service(
    service_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_agency),
    gitea: GiteaClient = Depends(get_gitea),
):
    """Da de alta el sitio en GitOps: escribe sus manifiestos en hub-gitops (spec 016).

    El Hub no habla con Kubernetes: Argo CD ve la carpeta nueva y crea el sitio. Exige que la versión
    inicial ya esté publicada en el registro; si la carpeta ya existe responde 409 y no cambia nada.
    """
    service = db.get(Service, service_id)
    if service is None:
        raise HTTPException(status_code=404, detail="El servicio no existe.")
    # Lo que se muestra al terminar se calcula antes (toca el plan y lo demás que el servicio carga de la base) y el servicio se separa de la sesión:
    # así las llamadas a Gitea (hasta 10 s cada una) no sostienen una conexión del pool (auditoría BE-02)
    try:
        files = list(provisioning.render_files(service, service.plan))
    except provisioning.EntradaInvalida as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    ficha = {"id": service.id, "namespace": service.namespace, "host": service.host}
    user_name, user_email = user.name, user.email
    # Se sueltan todos los objetos, no solo el servicio: al deshacer la transacción la sesión caduca los que conserva (proyecto, cliente, usuario) y leerlos
    # de nuevo durante las llamadas a Gitea volvería a tomar una conexión. Lo ya cargado se sigue leyendo, ahora sin base.
    db.expunge_all()
    soltar_conexion(db)
    try:
        missing = provisioning.missing_images(gitea, service)
        if missing:
            raise HTTPException(
                status_code=422,
                detail="Faltan imágenes en el registro: " + ", ".join(missing) + ". Publíquelas con el pipeline y reintente.",
            )
        commits = provisioning.provision(gitea, service, service.plan, user_name, user_email)
    except provisioning.AlreadyProvisioned as error:
        raise HTTPException(status_code=409, detail="El sitio ya está dado de alta en GitOps.") from error
    except provisioning.EntradaInvalida as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except GiteaError as error:
        raise HTTPException(status_code=502, detail=f"No se pudo escribir en Gitea: {error}") from error
    audit.record(
        db, user, "aprovisionar", "service", ficha["id"],
        {"namespace": ficha["namespace"], "commits": [c[:7] for c in commits]}, audit.request_ip(request),
    )
    db.commit()
    return ProvisionOut(service_id=ficha["id"], namespace=ficha["namespace"], host=ficha["host"], files=files, commits=commits)

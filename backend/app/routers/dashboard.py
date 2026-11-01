# Endpoints del panel de la agencia: KPIs por cliente, totales y carga por técnico (spec 010, T07).
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.deps import client_scope, current_user, require_agency
from app.models.ai_draft import AiDraft
from app.models.client import Client
from app.models.incident import Incident
from app.models.project import Project
from app.models.service import Service
from app.models.user import User
from app.schemas.dashboard import (
    AgencyDashboard,
    ClientDashboardKpi,
    ClientIncident,
    ClientKpi,
    ClientSeries,
    SeriesPoint,
    TechnicianLoad,
)
from app.services import kpi

# Mes en formato YYYY-MM: cualquier otro valor responde 422 en vez de romper el cálculo.
MONTH_PATTERN = r"^[0-9]{4}-(0[1-9]|1[0-2])$"

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/agency", response_model=AgencyDashboard)
def dashboard_agency(
    month: str | None = Query(default=None, pattern=MONTH_PATTERN),
    db: Session = Depends(get_db),
    user: User = Depends(require_agency),
) -> AgencyDashboard:
    """Devuelve los KPI por cliente del mes (CA-1, CA-2) con la carga por técnico.

    El `month` es `YYYY-MM` y por omisión es el mes actual en America/Bogota.
    """
    month = month or kpi.mes_actual()
    clients = db.scalars(
        select(Client)
        .options(selectinload(Client.projects).selectinload(Project.services))
        .order_by(Client.id)
    ).all()
    client_kpis = []
    for client in clients:
        service = client.main_service
        client_kpis.append(
            ClientKpi(
                client_id=client.id,
                client_name=client.name,
                service_name=service.name if service is not None else None,
                service_status=service.status if service is not None else "operativo",
                availability=kpi.disponibilidad_del_mes(db, client.id, month),
                cumple_objetivo=kpi.cumple_objetivo(db, client.id, month),
                latency_p95=kpi.latencia_p95_del_mes(db, client.id, month),
                sla_compliance=kpi.cumplimiento_sla(db, client.id, month),
                mttr=kpi.mttr_del_mes(db, client.id, month),
                open_tickets=kpi.solicitudes_abiertas(db, client.id, month),
                closed_tickets=kpi.solicitudes_cerradas(db, client.id, month),
                hours=kpi.horas_por_cliente(db, client.id, month),
                cost=kpi.costo_por_cliente(db, client.id, month),
            )
        )

    technicians = [
        TechnicianLoad(
            user_id=user.id,
            name=user.name,
            hours=kpi.horas_del_tecnico(db, user.id, month),
            load=kpi.carga_tecnico(db, user.id, month),
        )
        for user in db.scalars(select(User).where(User.role == "agencia")).all()
    ]

    return AgencyDashboard(month=month, clients=client_kpis, technicians=technicians)


@router.get("/client/{client_id}", response_model=ClientDashboardKpi)
def dashboard_client(
    client_id: int,
    month: str | None = Query(default=None, pattern=MONTH_PATTERN),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> ClientDashboardKpi:
    """KPI del mes del cliente para su portal: sin costo, horas ni nombres de técnicos (CA-7)."""
    month = month or kpi.mes_actual()
    client = db.get(Client, client_id)
    scope = client_scope(user)
    if client is None or (scope is not None and scope != client_id):
        raise HTTPException(status_code=404, detail="El cliente no existe.")
    service = client.main_service
    return ClientDashboardKpi(
        client_id=client.id,
        client_name=client.name,
        service_name=service.name if service is not None else None,
        service_status=service.status if service is not None else "operativo",
        availability=kpi.disponibilidad_del_mes(db, client.id, month),
        cumple_objetivo=kpi.cumple_objetivo(db, client.id, month),
        slo_availability=(
            float(slo) if (slo := kpi.objetivo_disponibilidad(db, client.id)) is not None else None
        ),
        latency_p95=kpi.latencia_p95_del_mes(db, client.id, month),
        sla_compliance=kpi.cumplimiento_sla(db, client.id, month),
        mttr=kpi.mttr_del_mes(db, client.id, month),
        open_tickets=kpi.solicitudes_abiertas(db, client.id, month),
        closed_tickets=kpi.solicitudes_cerradas(db, client.id, month),
    )


@router.get("/client/{client_id}/incidents", response_model=list[ClientIncident])
def dashboard_client_incidents(
    client_id: int,
    month: str | None = Query(default=None, pattern=MONTH_PATTERN),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> list[ClientIncident]:
    """Fallas del mes del cliente para su portal, sin técnicos ni datos internos (CA-4, CA-7), con el mensaje
    que la agencia aprobó para cada una (spec 012).

    La agencia puede consultar cualquier cliente; un cliente solo el suyo (404 si pide otro).
    """
    month = month or kpi.mes_actual()
    client = db.get(Client, client_id)
    scope = client_scope(user)
    if client is None or (scope is not None and scope != client_id):
        raise HTTPException(status_code=404, detail="El cliente no existe.")
    inicio, fin = kpi.month_bounds(month)
    incidents = db.scalars(
        select(Incident)
        .join(Service, Incident.service_id == Service.id)
        .join(Project, Service.project_id == Project.id)
        .where(
            Project.client_id == client_id,
            Incident.started_at >= inicio,
            Incident.started_at < fin,
        )
        .order_by(Incident.started_at.desc(), Incident.id.desc())
    ).all()
    # Solo el mensaje aprobado llega al cliente; los borradores y el resumen técnico nunca (spec 012, CA-4).
    # Una sola consulta para todas las fallas del mes, sin N+1.
    messages: dict[int, str] = {}
    if incidents:
        approved = db.execute(
            select(AiDraft.incident_id, AiDraft.final_text)
            .where(
                AiDraft.incident_id.in_([incident.id for incident in incidents]),
                AiDraft.kind == "mensaje_cliente",
                AiDraft.status == "aprobado",
            )
            .order_by(AiDraft.approved_at)
        )
        messages = {incident_id: text for incident_id, text in approved}
    return [
        ClientIncident(
            id=incident.id,
            title=incident.title,
            status=incident.status,
            started_at=incident.started_at,
            message=messages.get(incident.id),
        )
        for incident in incidents
    ]


@router.get("/client/{client_id}/series", response_model=ClientSeries)
def dashboard_client_series(
    client_id: int,
    month: str | None = Query(default=None, pattern=MONTH_PATTERN),
    db: Session = Depends(get_db),
    user: User = Depends(require_agency),
) -> ClientSeries:
    """Series del mes cada 5 min para las gráficas del detalle técnico (CA-6, T11).

    Con Prometheus caído devuelve listas vacías y el panel muestra «sin datos» (CA-8).
    """
    month = month or kpi.mes_actual()
    client = db.get(Client, client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="El cliente no existe.")
    slo = kpi.objetivo_disponibilidad(db, client.id)
    return ClientSeries(
        client_id=client.id,
        month=month,
        slo_availability=float(slo) if slo is not None else None,
        availability=[
            SeriesPoint(timestamp=marca, value=valor)
            for marca, valor in kpi.serie_disponibilidad(db, client.id, month) or []
        ],
        latency_p95=[
            SeriesPoint(timestamp=marca, value=valor)
            for marca, valor in kpi.serie_latencia_p95(db, client.id, month) or []
        ],
    )

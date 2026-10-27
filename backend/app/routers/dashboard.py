# Endpoints del panel de la agencia: KPIs por cliente, totales y carga por técnico (spec 010, T07).
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.deps import client_scope, current_user, require_agency
from app.models.client import Client
from app.models.project import Project
from app.models.user import User
from app.schemas.dashboard import AgencyDashboard, ClientDashboardKpi, ClientKpi, TechnicianLoad
from app.services import kpi

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/agency", response_model=AgencyDashboard)
def dashboard_agency(
    month: str | None = Query(default=None),
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
    month: str | None = Query(default=None),
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
        sla_compliance=kpi.cumplimiento_sla(db, client.id, month),
        mttr=kpi.mttr_del_mes(db, client.id, month),
        open_tickets=kpi.solicitudes_abiertas(db, client.id, month),
        closed_tickets=kpi.solicitudes_cerradas(db, client.id, month),
    )

# Endpoints de consulta de planes y tiempos de SLA (spec 001); los datos vienen de seed/.
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.plan import Plan
from app.models.sla_policy import SlaPolicy
from app.schemas.client import PlanOut
from app.schemas.sla_policy import SlaPolicyOut

router = APIRouter(prefix="/api", tags=["catálogo"])


@router.get("/plans", response_model=list[PlanOut])
def list_plans(db: Session = Depends(get_db)):
    """Lista los planes de la agencia."""
    return db.scalars(select(Plan).order_by(Plan.id)).all()


@router.get("/sla-policies", response_model=list[SlaPolicyOut])
def list_sla_policies(db: Session = Depends(get_db)):
    """Lista los tiempos de respuesta y solución por prioridad, de P1 a P4."""
    return db.scalars(select(SlaPolicy).order_by(SlaPolicy.priority)).all()

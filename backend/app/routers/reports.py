# Endpoints de los reportes mensuales: generar un operativo o un ejecutivo, listarlos y verlos (spec 013).
# El cliente solo ve los ejecutivos de su empresa; el operativo (costos, horas, técnicos) es de la agencia.
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.deps import client_scope, current_user, require_agency
from app.models.client import Client
from app.models.report import Report
from app.models.user import User
from app.schemas.report import MONTH_PATTERN, ReportCreate, ReportOut, ReportSummary
from app.services import audit, reports

router = APIRouter(prefix="/api/reports", tags=["reportes"])


def _as_utc(value: datetime | None) -> datetime | None:
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def present(report: Report, with_data: bool = True) -> dict:
    data = {
        "id": report.id,
        "kind": report.kind,
        "client_id": report.client_id,
        "client_name": report.client.name if report.client else None,
        "month": report.month,
        "generated_by_name": report.generated_by.name if report.generated_by else None,
        "created_at": _as_utc(report.created_at),
    }
    if with_data:
        data["data"] = report.data
    return data


def _query():
    return select(Report).options(selectinload(Report.client), selectinload(Report.generated_by))


def _scoped(query, user: User):
    """Lo que puede ver cada rol: la agencia todo; el cliente solo los ejecutivos de su empresa."""
    scope = client_scope(user)
    if scope is None:
        return query
    return query.where(Report.kind == "ejecutivo", Report.client_id == scope)


@router.post("", response_model=ReportOut, status_code=status.HTTP_201_CREATED)
def create_report(
    data: ReportCreate,
    request: Request,
    db: Session = Depends(get_db),
    actor: User = Depends(require_agency),
):
    """Genera el reporte del mes y guarda sus números: no cambian aunque después lleguen datos nuevos."""
    if data.kind == "ejecutivo":
        if db.get(Client, data.client_id) is None:
            raise HTTPException(status_code=404, detail="El cliente no existe.")
        content = reports.executive(db, data.client_id, data.month)
    else:
        content = reports.operational(db, data.month)
    report = Report(
        kind=data.kind, client_id=data.client_id, month=data.month, data=content, generated_by_id=actor.id
    )
    db.add(report)
    db.flush()
    audit.record(
        db, actor, "generar", "report", report.id,
        {"tipo": data.kind, "cliente": data.client_id, "mes": data.month}, audit.request_ip(request),
    )
    db.commit()
    db.refresh(report)
    return present(report)


@router.get("", response_model=list[ReportSummary])
def list_reports(
    kind: str | None = Query(default=None),
    client_id: int | None = Query(default=None),
    month: str | None = Query(default=None, pattern=MONTH_PATTERN),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    """Reportes generados, los más recientes primero, con filtros por tipo, cliente y mes."""
    query = _scoped(_query(), user)
    if kind is not None:
        query = query.where(Report.kind == kind)
    if client_id is not None:
        query = query.where(Report.client_id == client_id)
    if month is not None:
        query = query.where(Report.month == month)
    return [present(report, with_data=False) for report in db.scalars(query.order_by(Report.id.desc()))]


@router.get("/{report_id}", response_model=ReportOut)
def get_report(report_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    """Un reporte con sus datos; para el cliente, uno que no es suyo «no existe» (404, no 403)."""
    report = db.scalar(_scoped(_query(), user).where(Report.id == report_id))
    if report is None:
        raise HTTPException(status_code=404, detail="El reporte no existe.")
    return present(report)

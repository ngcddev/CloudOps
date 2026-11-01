# Endpoints de los reportes mensuales: generar un operativo o un ejecutivo (spec 013).
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import require_agency
from app.models.client import Client
from app.models.report import Report
from app.models.user import User
from app.schemas.report import ReportCreate, ReportOut
from app.services import audit, reports

router = APIRouter(prefix="/api/reports", tags=["reportes"])


def _as_utc(value: datetime | None) -> datetime | None:
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def present(report: Report) -> dict:
    return {
        "id": report.id,
        "kind": report.kind,
        "client_id": report.client_id,
        "client_name": report.client.name if report.client else None,
        "month": report.month,
        "data": report.data,
        "generated_by_name": report.generated_by.name if report.generated_by else None,
        "created_at": _as_utc(report.created_at),
    }


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

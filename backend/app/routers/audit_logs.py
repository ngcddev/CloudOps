# Consulta de la bitácora de acciones sensibles; solo lectura y solo agencia (spec 007, T15).
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.deps import require_agency
from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogOut

router = APIRouter(prefix="/api/audit-logs", tags=["bitácora"], dependencies=[Depends(require_agency)])

MAX_ROWS = 200


@router.get("", response_model=list[AuditLogOut])
def list_audit_logs(
    user_id: int | None = Query(default=None),
    entity: str | None = Query(default=None),
    action: str | None = Query(default=None),
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Las acciones registradas, de la más reciente a la más antigua (máximo 200)."""
    query = select(AuditLog).options(selectinload(AuditLog.user))
    if user_id is not None:
        query = query.where(AuditLog.user_id == user_id)
    if entity is not None:
        query = query.where(AuditLog.entity == entity)
    if action is not None:
        query = query.where(AuditLog.action == action)
    if from_ is not None:
        query = query.where(AuditLog.created_at >= from_)
    if to is not None:
        query = query.where(AuditLog.created_at <= to)
    logs = db.scalars(query.order_by(AuditLog.id.desc()).limit(MAX_ROWS)).all()
    return [
        AuditLogOut(
            id=log.id,
            user_id=log.user_id,
            user_name=log.user.name if log.user else "Sistema",
            action=log.action,
            entity=log.entity,
            entity_id=log.entity_id,
            details=log.details,
            ip=log.ip,
            created_at=log.created_at,
        )
        for log in logs
    ]

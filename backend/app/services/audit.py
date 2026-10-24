# Registro de acciones sensibles en la bitácora (spec 007, T07).
from fastapi import Request
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User


def record(
    db: Session,
    user: User | None,
    action: str,
    entity: str,
    entity_id: int | None,
    details: dict | None = None,
    ip: str | None = None,
) -> AuditLog:
    """Agrega la fila a la sesión de la acción; no hace commit.

    Así el registro y la acción se guardan juntos: si la acción falla, no queda fila, y viceversa.
    `user=None` significa que la acción la hizo el sistema.
    """
    log = AuditLog(
        user_id=user.id if user is not None else None,
        action=action,
        entity=entity,
        entity_id=entity_id,
        details=details,
        ip=ip,
    )
    db.add(log)
    return log


def request_ip(request: Request) -> str | None:
    """IP de quien hizo la petición (la del proxy si el Ingress la reenvía)."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None

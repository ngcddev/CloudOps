# Esquema de salida de la bitácora (spec 007, T15).
from datetime import datetime

from pydantic import BaseModel


class AuditLogOut(BaseModel):
    id: int
    user_id: int | None
    # "Sistema" cuando la acción la hizo el Hub solo (por ejemplo, confirmar una publicación)
    user_name: str
    action: str
    entity: str
    entity_id: int | None
    details: dict | None
    ip: str | None
    created_at: datetime

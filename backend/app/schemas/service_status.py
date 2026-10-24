# Esquemas del estado de los servicios y su historial de versiones (spec 005, T16).
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ServiceStatusOut(BaseModel):
    service_id: int
    client_id: int
    client_name: str
    service_name: str
    host: str
    namespace: str
    current_version: str
    stable_version: str
    sync_status: str
    health_status: str
    # Quién hizo el último cambio publicado y cuándo; null si el sitio nunca ha cambiado
    last_author: str | None
    last_change_at: datetime | None
    # Cambio en curso (pendiente, aprobada o en validación), si lo hay
    open_change_id: int | None
    open_change_status: str | None
    open_change_to_version: str | None
    # Puerta de seguridad de la versión activa (spec 006): sin_corrida, en_curso, ok o fallo
    security_status: str
    security_failed_step: str | None


class DeploymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    service_id: int
    version: str
    commit_sha: str | None
    author: str
    source: str
    created_at: datetime

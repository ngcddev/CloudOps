# Esquemas de entrada y salida de incidentes (spec 008, T04-T06).
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class IncidentCreate(BaseModel):
    service_id: int
    priority: Literal["P1", "P2", "P3", "P4"]
    title: str = Field(max_length=200)

    @field_validator("title")
    @classmethod
    def _titulo_obligatorio(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El título es obligatorio.")
        return value


class IncidentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    service_id: int
    client_id: int
    client_name: str
    service_name: str
    namespace: str
    priority: str
    status: str
    source: str
    title: str
    started_at: datetime
    acknowledged_at: datetime | None
    mitigated_at: datetime | None
    closed_at: datetime | None
    response_due_at: datetime
    resolution_due_at: datetime
    assignee_id: int | None
    assignee_name: str | None
    root_cause: str | None
    # Estado de cada reloj del SLA: a_tiempo, en_riesgo, vencido o cumplido
    response_state: str
    resolution_state: str
    # Minutos entre el inicio real de la falla y su mitigación (un decimal); nulo mientras siga abierto (spec 009)
    mttr_minutes: float | None
    created_at: datetime


class IncidentEventOut(BaseModel):
    """Un punto de la línea de tiempo: detectado, tomado, nota, recuperado, cerrado o del rollback."""

    id: int
    type: str
    message: str | None
    # Nombre del usuario o «Sistema» si lo registró el monitoreo
    actor_name: str
    created_at: datetime


class LastChangeOut(BaseModel):
    """Última publicación del servicio, para revisar si la falla vino de ahí."""

    version: str
    author: str
    source: str
    deployed_at: datetime
    change_request_id: int | None
    commit_sha: str | None
    commit_url: str | None


class RollbackOut(BaseModel):
    """Rollback del incidente (spec 009): `sin_rollback`, `enviado`, `sincronizando` o `recuperado`."""

    status: Literal["sin_rollback", "enviado", "sincronizando", "recuperado"]
    from_version: str | None
    to_version: str | None
    # Quién lo pidió; nulo si no hay rollback
    by_name: str | None
    at: datetime | None
    confirmed_at: datetime | None
    commit_sha: str | None
    commit_url: str | None


class RollbackPlanOut(BaseModel):
    """Lo que se ve antes de confirmar el rollback: a qué versión se vuelve y si el botón está activo."""

    current_version: str | None
    target_version: str | None
    can_rollback: bool
    # Por qué está deshabilitado; nulo si se puede
    reason: str | None


class ClientMessageOut(BaseModel):
    """Mensaje para el cliente: se copia y la agencia lo envía; el Hub nunca lo manda solo."""

    message: str


class IncidentDetail(IncidentOut):
    events: list[IncidentEventOut]
    # Grafana Explore con los registros del sitio; nulo si no hay GRAFANA_URL
    logs_url: str | None
    last_change: LastChangeOut | None
    rollback: RollbackOut


class IncidentNoteIn(BaseModel):
    message: str = Field(max_length=2000)

    @field_validator("message")
    @classmethod
    def _nota_obligatoria(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("La nota no puede estar vacía.")
        return value


class IncidentCloseIn(BaseModel):
    root_cause: str = Field(max_length=2000)

    @field_validator("root_cause")
    @classmethod
    def _causa_obligatoria(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Para cerrar el incidente hay que escribir la causa raíz.")
        return value

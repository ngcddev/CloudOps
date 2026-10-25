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
    created_at: datetime


class IncidentEventOut(BaseModel):
    """Un punto de la línea de tiempo: detectado, tomado, nota, recuperado o cerrado."""

    id: int
    type: str
    message: str | None
    # Nombre del usuario o «Sistema» si lo registró el monitoreo
    actor_name: str
    created_at: datetime


class IncidentDetail(IncidentOut):
    events: list[IncidentEventOut]


class IncidentNoteIn(BaseModel):
    message: str = Field(max_length=2000)

    @field_validator("message")
    @classmethod
    def _nota_obligatoria(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("La nota no puede estar vacía.")
        return value

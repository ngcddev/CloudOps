# Esquemas de entrada y salida de solicitudes (spec 004, T09).
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TicketCreate(BaseModel):
    service_id: int
    created_by_id: int | None = None
    title: str = Field(max_length=200)
    description: str
    kind: Literal["solicitud", "cambio"] = "solicitud"

    @field_validator("title", "description")
    @classmethod
    def _texto_obligatorio(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El título y la descripción son obligatorios.")
        return value


class TicketEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_id: int | None
    type: str
    from_value: str | None
    to_value: str | None
    note: str | None
    internal: bool
    created_at: datetime


class WorkLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    hours: float
    note: str | None
    created_at: datetime


class TicketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    service_id: int
    created_by_id: int | None
    assignee_id: int | None
    title: str
    description: str
    impact: str | None
    urgency: str | None
    priority: str | None
    status: str
    kind: str
    response_due_at: datetime | None
    resolution_due_at: datetime | None
    first_response_at: datetime | None
    resolved_at: datetime | None
    closed_at: datetime | None
    created_at: datetime


class TicketDetail(TicketOut):
    events: list[TicketEventOut] = Field(default_factory=list)
    work_logs: list[WorkLogOut] = Field(default_factory=list)
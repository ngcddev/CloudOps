# Esquemas del aviso que manda el webhook de Alertmanager (formato version 4) y la respuesta del Hub (spec 008).
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AlertmanagerAlert(BaseModel):
    """Una alerta del aviso. Se ignoran los campos que el Hub no usa."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    status: Literal["firing", "resolved"]
    labels: dict[str, str]
    annotations: dict[str, str] = {}
    starts_at: datetime = Field(alias="startsAt")
    # En un `firing` llega vacío (0001-01-01); en un `resolved` es la hora del primer sondeo sano
    ends_at: datetime | None = Field(default=None, alias="endsAt")
    fingerprint: str = Field(min_length=1, max_length=100)


class AlertmanagerPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    status: Literal["firing", "resolved"]
    alerts: list[AlertmanagerAlert]


class AlertResult(BaseModel):
    """Qué hizo el Hub con cada alerta, para revisarlo en los registros de Alertmanager."""

    fingerprint: str
    # creado, duplicado, mitigado o ignorado
    result: str
    incident_id: int | None = None


class AlertmanagerResponse(BaseModel):
    results: list[AlertResult]

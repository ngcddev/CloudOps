# Esquemas de las solicitudes de cambio: entrada y salida de la API (spec 005, T13).
import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

# Etiqueta de imagen válida de Docker (v1, v1.1, v2.0.3-rc1); misma regla que app.services.kustomization
_VERSION = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}")


class ChangeRequestCreate(BaseModel):
    ticket_id: int
    to_version: str
    requested_by_id: int | None = None

    @field_validator("to_version")
    @classmethod
    def _version_valida(cls, value: str) -> str:
        value = value.strip()
        if not _VERSION.fullmatch(value):
            raise ValueError("La versión destino no es válida (por ejemplo: v1.1).")
        return value


class ChangeRequestReject(BaseModel):
    reason: str
    actor_id: int | None = None

    @field_validator("reason")
    @classmethod
    def _motivo_obligatorio(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Debe indicar el motivo del rechazo.")
        return value


class ChangeRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    service_id: int
    from_version: str
    to_version: str
    status: str
    requested_by_id: int | None
    approved_by_id: int | None
    gitops_commit_sha: str | None
    rejection_reason: str | None
    created_at: datetime
    approved_at: datetime | None
    deployed_at: datetime | None

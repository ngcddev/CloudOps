# Esquemas de la puerta de seguridad: eventos del pipeline y corridas con sus controles (spec 006).
from datetime import datetime
from typing import Literal, get_args

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.services.security_gate import STEPS

Step = Literal["secretos", "construccion", "vulnerabilidades", "sbom", "firma", "verificacion"]
assert set(STEPS) == set(get_args(Step))  # los controles del esquema y los de las reglas son los mismos


class PipelineEvent(BaseModel):
    """Lo que el pipeline cuenta al Hub: `inicio` abre la corrida, `paso` registra un control y `fin` la cierra."""

    event: Literal["inicio", "paso", "fin"]
    # Nombre del repositorio del sitio: restaurante, ferreteria o consultorio
    site: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{0,40}$")
    version: str = Field(min_length=1, max_length=50)
    commit_sha: str | None = Field(default=None, max_length=64)
    # inicio: las imágenes que debe producir la versión
    images: list[str] = Field(default_factory=list, max_length=5)
    # paso
    step: Step | None = None
    image: str | None = Field(default=None, max_length=100)
    summary: str = Field(default="", max_length=2000)
    report: dict | list | None = None
    # paso y fin
    status: Literal["ok", "fallo"] | None = None
    # fin: digest de cada imagen verificada
    image_digests: dict[str, str] | None = None

    @model_validator(mode="after")
    def _campos_del_evento(self) -> "PipelineEvent":
        if self.event == "paso" and (self.step is None or self.status is None):
            raise ValueError("Un paso necesita el control (step) y su resultado (status).")
        if self.event == "fin" and self.status is None:
            raise ValueError("El fin de la corrida necesita su resultado (status).")
        return self


class SecurityCheckOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    step: str
    image: str | None
    status: str
    summary: str
    # true si el control guardó un reporte que se puede descargar como evidencia
    has_report: bool
    created_at: datetime


class SecurityRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    service_id: int
    version: str
    commit_sha: str | None
    images: list[str]
    status: str
    failed_step: str | None
    image_digests: dict | None
    started_at: datetime
    finished_at: datetime | None
    checks: list[SecurityCheckOut] = Field(default_factory=list)


class GateOut(BaseModel):
    """Estado de la puerta para una versión: `sin_corrida`, `en_curso`, `ok` o `fallo`, con su última corrida."""

    version: str
    status: str
    failed_step: str | None
    run: SecurityRunOut | None

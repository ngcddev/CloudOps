# Esquemas de entrada y salida de los reportes mensuales (spec 013).
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

# Mismo formato de mes que el dashboard (spec 010)
MONTH_PATTERN = r"^[0-9]{4}-(0[1-9]|1[0-2])$"


class ReportCreate(BaseModel):
    kind: Literal["operativo", "ejecutivo"]
    # Obligatorio en el ejecutivo; el operativo es de toda la agencia y lo ignora
    client_id: int | None = None
    month: str = Field(pattern=MONTH_PATTERN)

    @model_validator(mode="after")
    def _cliente_del_ejecutivo(self) -> "ReportCreate":
        if self.kind == "ejecutivo" and self.client_id is None:
            raise ValueError("El reporte ejecutivo necesita un cliente.")
        if self.kind == "operativo":
            self.client_id = None
        return self


class ReportOut(BaseModel):
    """Un reporte generado, con sus números congelados en `data`."""

    id: int
    kind: Literal["operativo", "ejecutivo"]
    client_id: int | None
    client_name: str | None
    month: str
    # Datos del reporte: la forma depende del tipo (services/reports.py)
    data: dict
    generated_by_name: str | None
    created_at: datetime

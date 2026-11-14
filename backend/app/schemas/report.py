# Esquemas de los reportes mensuales (spec 013).
import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator

MES = re.compile(r"^[0-9]{4}-(0[1-9]|1[0-2])$")


class ReportIn(BaseModel):
    kind: Literal["operativo", "ejecutivo"]
    # Obligatorio en el ejecutivo; el operativo es de toda la agencia
    client_id: int | None = None
    # YYYY-MM; por omisión, el mes actual
    month: str | None = None

    @field_validator("month")
    @classmethod
    def mes_valido(cls, valor: str | None) -> str | None:
        if valor is not None and not MES.match(valor):
            raise ValueError("El mes debe tener el formato AAAA-MM, por ejemplo 2026-10.")
        return valor


class ReportSummary(BaseModel):
    id: int
    kind: Literal["operativo", "ejecutivo"]
    client_id: int | None
    client_name: str | None
    month: str
    month_label: str
    generated_by: str | None
    created_at: datetime


class ReportOut(ReportSummary):
    # Los datos del mes, congelados al generar el reporte
    data: dict

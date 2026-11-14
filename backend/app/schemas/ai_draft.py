# Esquemas de los borradores del asistente para un incidente (spec 012).
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class GenerateIn(BaseModel):
    # Sin `kinds` se generan los dos: el resumen técnico y el mensaje al cliente
    kinds: list[Literal["resumen", "mensaje_cliente"]] | None = None


class ApproveIn(BaseModel):
    # Texto editado por la persona; sin él se aprueba el borrador tal cual
    text: str | None = Field(default=None, max_length=2000)


class DraftOut(BaseModel):
    id: int
    incident_id: int
    kind: Literal["resumen", "mensaje_cliente"]
    status: Literal["borrador_ia", "aprobado", "descartado"]
    # llm: lo redactó el modelo · plantilla: texto base (la IA no respondió o su texto no pasó las verificaciones)
    source: Literal["llm", "plantilla"]
    model: str | None
    prompt_version: str | None
    generated_text: str
    final_text: str | None
    # Aviso para la persona: por qué se usó el texto base, qué términos u horas se rechazaron
    notice: str | None
    latency_ms: int | None
    approved_by: str | None
    approved_at: datetime | None
    created_at: datetime

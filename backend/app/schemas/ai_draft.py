# Esquemas de entrada y salida de los borradores de texto de un incidente (spec 012).
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class AiDraftOut(BaseModel):
    """Un borrador: lo que redactó el asistente (o el técnico) y, si se aprobó, el texto final."""

    id: int
    incident_id: int
    kind: Literal["resumen", "mensaje_cliente"]
    status: Literal["borrador_ia", "aprobado", "descartado"]
    model: str
    prompt_version: str | None
    generated_text: str
    final_text: str | None
    # Quién lo escribió a mano; nulo si lo redactó el asistente
    created_by_name: str | None
    approved_by_name: str | None
    approved_at: datetime | None
    latency_ms: int | None
    created_at: datetime


class AiDraftsGenerated(BaseModel):
    """Respuesta de «Generar borradores»: los que pasaron los controles y por qué se descartó el resto."""

    drafts: list[AiDraftOut]
    problems: list[str]


class ManualTemplates(BaseModel):
    """Textos con los datos reales para escribir a mano; nulos mientras el incidente no se mitigue."""

    resumen: str | None
    mensaje_cliente: str | None


class IncidentDrafts(BaseModel):
    """Los borradores de un incidente, del más antiguo al más reciente, y las plantillas para escribir a mano."""

    drafts: list[AiDraftOut]
    manual_templates: ManualTemplates


class ManualDraftIn(BaseModel):
    """Borrador escrito a mano por el técnico cuando el asistente no responde (CA-5)."""

    kind: Literal["resumen", "mensaje_cliente"]
    text: str = Field(max_length=4000)

    @field_validator("text")
    @classmethod
    def _texto_obligatorio(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El texto no puede estar vacío.")
        return value

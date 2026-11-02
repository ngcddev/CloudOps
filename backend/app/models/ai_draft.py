# Borrador de texto de un incidente: resumen técnico o mensaje al cliente (tabla ai_drafts, spec 012).
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class AiDraft(Base):
    __tablename__ = "ai_drafts"

    id: Mapped[int] = mapped_column(primary_key=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("incidents.id"), nullable=False, index=True)
    # `resumen` (solo lo ve la agencia) o `mensaje_cliente` (lo ve el cliente cuando se aprueba)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    # borrador_ia → aprobado | descartado (nombres canónicos). Nada llega al cliente sin `aprobado`.
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="borrador_ia")
    # Modelo que lo redactó (p. ej. `qwen2.5:7b`) o `manual` si lo escribió un técnico
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    # Versión de las instrucciones del asistente (`v1`); nula en los escritos a mano
    prompt_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    generated_text: Mapped[str] = mapped_column(Text, nullable=False)
    # Texto que aprobó el técnico, con sus ediciones; nulo hasta aprobar
    final_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Quién escribió el borrador a mano; nulo si lo redactó el asistente
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    approved_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Lo que tardó el asistente en responder; nulo en los escritos a mano
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    incident = relationship("Incident")
    created_by = relationship("User", foreign_keys=[created_by_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])

# Borradores de texto que redacta el asistente local para un incidente (tabla ai_drafts, spec 012): el resumen técnico para el
# equipo y el mensaje para el cliente. Nada sale de la agencia mientras esté en `borrador_ia`: una persona lo edita y lo aprueba
# (principio 6). Cada borrador guarda con qué modelo y prompt se hizo y qué verificaciones automáticas se le aplicaron.
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class AiDraft(Base):
    __tablename__ = "ai_drafts"

    id: Mapped[int] = mapped_column(primary_key=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("incidents.id"), nullable=False, index=True)
    # resumen (técnico, para la agencia) | mensaje_cliente (sin jerga, para el portal)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    # borrador_ia → aprobado | descartado
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="borrador_ia")
    # llm (lo redactó el modelo) | plantilla (texto base determinista: la IA no respondió o su texto no pasó las verificaciones)
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    model: Mapped[str | None] = mapped_column(String(60), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(30), nullable=True)
    generated_text: Mapped[str] = mapped_column(Text, nullable=False)
    # Lo que realmente se aprobó (el borrador editado por la persona); nulo mientras no se apruebe
    final_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Resultado de las verificaciones: términos prohibidos, horas que no coinciden, motivo de usar la plantilla
    checks: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    approved_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    incident = relationship("Incident")
    approved_by = relationship("User", foreign_keys=[approved_by_id])

# Registro de cada pregunta al asistente y de lo que decidió la compuerta (tabla ai_queries, spec 012).
# Es la base de la medición LLMOps/MLOps: cuántas veces se despertó el LLM, cuántas se evitaron, cuánto tardó
# y qué dijo la persona sobre la decisión (`feedback_label`, material para reentrenar la compuerta).
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import JSON_DOC, Base


class AiQuery(Base):
    __tablename__ = "ai_queries"
    __table_args__ = (Index("ix_ai_queries_created_at", "created_at"),)   # el de la migración 0010 (auditoría BD-06)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    # en_tema | fuera_de_tema (decisión de la compuerta)
    gate_label: Mapped[str] = mapped_column(String(20), nullable=False)
    p_fuera_de_tema: Mapped[float] = mapped_column(Float, nullable=False)
    gate_version: Mapped[str] = mapped_column(String(30), nullable=False)
    llm_woken: Mapped[bool] = mapped_column(Boolean, nullable=False)
    # Nulos si no se llamó al LLM
    model: Mapped[str | None] = mapped_column(String(60), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(30), nullable=True)
    llm_ok: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    # Secciones de la ayuda que sirvieron de contexto (trazabilidad de la respuesta); vacío = sin información
    context_sections: Mapped[list | None] = mapped_column(JSON_DOC, nullable=True)
    # Cómo se armó el contexto: completo | recuperacion | rag (el RAG puede caer a recuperación léxica) y, con RAG,
    # la similitud coseno del mejor trozo
    context_mode: Mapped[str | None] = mapped_column(String(20), nullable=True)
    retrieval_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Lo que la persona dice que era la pregunta en realidad (en_tema | fuera_de_tema); nulo = sin opinar
    feedback_label: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

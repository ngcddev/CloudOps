# Bitácora de acciones sensibles, de solo inserción (tabla audit_logs, spec 007).
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import JSON_DOC, Base


class AuditLog(Base):
    __tablename__ = "audit_logs"
    # Los mismos índices que creó la migración 0006: sin declararlos aquí, `alembic revision --autogenerate` propondría borrarlos (auditoría BD-06)
    __table_args__ = (Index("ix_audit_logs_created_at", "created_at"), Index("ix_audit_logs_entity", "entity", "entity_id"))

    id: Mapped[int] = mapped_column(primary_key=True)
    # Nulo = la acción la hizo el sistema (por ejemplo, confirmar una publicación)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    entity: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    details: Mapped[dict | None] = mapped_column(JSON_DOC, nullable=True)
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")

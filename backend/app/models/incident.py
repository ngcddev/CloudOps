# Modelo de incidente de un servicio, abierto por una alerta o a mano (tabla incidents, spec 008).
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Incident(Base):
    __tablename__ = "incidents"
    __table_args__ = (
        # Dos avisos simultáneos de la misma falla no pueden abrir dos incidentes (CA-3): el
        # fingerprint de Alertmanager es único solo entre los incidentes abiertos.
        Index(
            "ux_incidents_fingerprint_abierto",
            "fingerprint",
            unique=True,
            postgresql_where=text("status = 'abierto'"),
            sqlite_where=text("status = 'abierto'"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"), nullable=False)
    priority: Mapped[str] = mapped_column(String(2), nullable=False)
    # abierto → mitigado → cerrado
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="abierto")
    # `alerta` (lo abrió Alertmanager) o `manual` (lo abrió un técnico)
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    # Huella de la alerta en Alertmanager; nula en los incidentes manuales
    fingerprint: Mapped[str | None] = mapped_column(String(100), nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    # Hora real en que empezó la falla (no la hora en que llegó el aviso)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    mitigated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    response_due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolution_due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    assignee_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    # Nulo = lo abrió el sistema
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # Rollback (spec 009): nulos hasta que un técnico lo pide. El estado (`enviado`, `sincronizando`,
    # `recuperado`) y el MTTR se calculan al leer; no se guardan.
    rollback_from_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    rollback_to_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    rollback_commit_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rollback_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    rollback_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rollback_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    service = relationship("Service")
    assignee = relationship("User", foreign_keys=[assignee_id])
    created_by = relationship("User", foreign_keys=[created_by_id])
    rollback_by = relationship("User", foreign_keys=[rollback_by_id])
    events = relationship(
        "IncidentEvent", back_populates="incident", cascade="all, delete-orphan", order_by="IncidentEvent.id"
    )

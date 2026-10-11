# Modelo de solicitud de cambio de versión de un servicio (tabla change_requests, spec 005).
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class ChangeRequest(Base):
    __tablename__ = "change_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), nullable=False)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"), nullable=False)
    from_version: Mapped[str] = mapped_column(String(50), nullable=False)
    to_version: Mapped[str] = mapped_column(String(50), nullable=False)
    # pendiente → aprobada → en_validacion → desplegada | rechazada (constitución, estados)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pendiente")
    requested_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    approved_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    gitops_commit_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deployed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    ticket = relationship("Ticket")
    service = relationship("Service")
    requested_by = relationship("User", foreign_keys=[requested_by_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])

    # Nombres que la bandeja de cambios muestra sin pedir los usuarios y solicitudes por separado
    @property
    def requested_by_name(self) -> str | None:
        return self.requested_by.name if self.requested_by else None

    @property
    def approved_by_name(self) -> str | None:
        return self.approved_by.name if self.approved_by else None

    @property
    def ticket_title(self) -> str | None:
        return self.ticket.title if self.ticket else None

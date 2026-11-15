# Modelo de solicitud de cambio de versión de un servicio (tabla change_requests, spec 005).
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

# Estados en los que un cambio sigue abierto. Los routers y el vigilante de despliegues tienen su propia copia (OPEN_STATUSES):
# una prueba comprueba que coinciden con esta, que es la que usa el índice único.
OPEN_STATUSES = ("pendiente", "aprobada", "en_validacion")
OPEN_PREDICATE = "status IN (" + ", ".join(f"'{estado}'" for estado in OPEN_STATUSES) + ")"


class ChangeRequest(Base):
    __tablename__ = "change_requests"
    __table_args__ = (
        Index("ix_change_requests_service_status", "service_id", "status"),
        Index("ix_change_requests_ticket_id", "ticket_id"),
        # Un solo cambio en curso por servicio: lo que el router comprueba con un SELECT, aquí lo garantiza la base ante dos peticiones a la vez (auditoría BD-02)
        Index(
            "uq_change_requests_open_per_service", "service_id", unique=True,
            postgresql_where=text(OPEN_PREDICATE), sqlite_where=text(OPEN_PREDICATE),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), nullable=False)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"), nullable=False)
    from_version: Mapped[str] = mapped_column(String(50), nullable=False)
    to_version: Mapped[str] = mapped_column(String(50), nullable=False)
    # pendiente → aprobada → en_validacion → desplegada | fallida; o pendiente → rechazada (constitución, estados)
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

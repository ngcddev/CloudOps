# Evento de la línea de tiempo de un incidente (tabla incident_events, spec 008).
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class IncidentEvent(Base):
    __tablename__ = "incident_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("incidents.id"), nullable=False)
    # detectado, tomado, nota, recuperado o cerrado
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Nulo = Sistema
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    incident = relationship("Incident", back_populates="events")
    actor = relationship("User")

    @property
    def actor_name(self) -> str:
        """Nombre que muestra la línea de tiempo: el del usuario o «Sistema»."""
        return self.actor.name if self.actor is not None else "Sistema"

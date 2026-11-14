# Reportes mensuales generados (tabla reports, spec 013): el operativo de la agencia y el ejecutivo de cada cliente. Los datos del mes quedan
# congelados en `data` al generarlo: el reporte no cambia aunque después cambien los tickets o las métricas, y el PDF sale siempre de esos datos.
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    # operativo (toda la agencia, uso interno) | ejecutivo (un cliente, sin jerga)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    # Nulo en el operativo; el cliente dueño en el ejecutivo
    client_id: Mapped[int | None] = mapped_column(ForeignKey("clients.id"), nullable=True, index=True)
    # YYYY-MM
    month: Mapped[str] = mapped_column(String(7), nullable=False)
    data: Mapped[dict] = mapped_column(JSON, nullable=False)
    generated_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client")
    generated_by = relationship("User", foreign_keys=[generated_by_id])

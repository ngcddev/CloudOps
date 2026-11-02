# Reporte mensual generado: operativo (agencia) o ejecutivo (un cliente), con sus números congelados
# (tabla reports, spec 013).
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    # `operativo` (toda la agencia; solo lo ve la agencia) o `ejecutivo` (un cliente; lo ve ese cliente)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    # Nulo en el operativo
    client_id: Mapped[int | None] = mapped_column(ForeignKey("clients.id"), nullable=True, index=True)
    # Mes del reporte en America/Bogota, `YYYY-MM`
    month: Mapped[str] = mapped_column(String(7), nullable=False)
    # Todos los números y textos del reporte tal como se generaron: no cambian después (plan 013)
    data: Mapped[dict] = mapped_column(JSON, nullable=False)
    generated_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client")
    generated_by = relationship("User")

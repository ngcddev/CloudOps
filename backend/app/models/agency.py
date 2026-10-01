# Modelo de agencia: la empresa que opera los servicios de sus clientes (tabla agencies, plan 001).
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Agency(Base):
    __tablename__ = "agencies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    # Fechas en UTC (se muestran en America/Bogota en la interfaz)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    clients = relationship("Client", back_populates="agency")

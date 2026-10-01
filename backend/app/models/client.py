# Modelo Client: la empresa cliente de la agencia (tabla clients, plan 001).
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    agency_id: Mapped[int | None] = mapped_column(ForeignKey("agencies.id"))
    name: Mapped[str] = mapped_column(String(200))
    contact_name: Mapped[str | None] = mapped_column(String(200))
    email: Mapped[str | None] = mapped_column(String(200))
    phone: Mapped[str | None] = mapped_column(String(50))
    # Fechas en UTC (se muestran en America/Bogota en la interfaz)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    agency = relationship("Agency", back_populates="clients")
    projects = relationship("Project", back_populates="client", cascade="all, delete-orphan")

# Modelo del historial de versiones publicadas de un servicio (tabla deployments, spec 005).
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Deployment(Base):
    __tablename__ = "deployments"

    id: Mapped[int] = mapped_column(primary_key=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    commit_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # Nombre de quien autorizó la publicación (el usuario del Hub que aprobó)
    author: Mapped[str] = mapped_column(String(200), nullable=False)
    # `cambio` (spec 005) o `rollback` (spec 009)
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="cambio")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    service = relationship("Service", back_populates="deployments")

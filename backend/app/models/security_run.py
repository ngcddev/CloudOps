# Corrida de la puerta de seguridad de una versión de un sitio (tabla security_runs, spec 006).
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class SecurityRun(Base):
    __tablename__ = "security_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    commit_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # Imágenes que debe producir la versión (el consultorio tiene dos); cada una pasa los mismos controles
    images: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    # en_curso → ok | fallo
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="en_curso")
    failed_step: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # Digest de cada imagen verificada, para saber exactamente qué se firmó
    image_digests: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    service = relationship("Service")
    checks = relationship(
        "SecurityCheck", back_populates="run", cascade="all, delete-orphan", order_by="SecurityCheck.id"
    )

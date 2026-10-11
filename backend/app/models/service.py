# Modelo de servicio operado para un proyecto (tabla services, spec 001).
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    host: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    template: Mapped[str] = mapped_column(String(30), nullable=False)
    namespace: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="operativo")
    # Versión que corre, última versión estable y estado que informa Argo CD (spec 005)
    current_version: Mapped[str] = mapped_column(String(50), nullable=False, default="v1", server_default="v1")
    stable_version: Mapped[str] = mapped_column(String(50), nullable=False, default="v1", server_default="v1")
    sync_status: Mapped[str] = mapped_column(String(30), nullable=False, default="Unknown", server_default="Unknown")
    health_status: Mapped[str] = mapped_column(String(30), nullable=False, default="Unknown", server_default="Unknown")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="services")
    plan = relationship("Plan")
    deployments = relationship("Deployment", back_populates="service", order_by="Deployment.id")

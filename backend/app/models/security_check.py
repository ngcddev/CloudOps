# Resultado de un control de la puerta de seguridad, con su evidencia (tabla security_checks, spec 006).
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, false, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import JSON_DOC, Base


class SecurityCheck(Base):
    __tablename__ = "security_checks"
    # Un control por corrida, paso e imagen (el control de secretos no tiene imagen: NULL cuenta como un valor); lo que `add_check` comprueba en memoria,
    # aquí lo garantiza la base ante un reintento del pipeline a la vez (auditoría BD-02)
    __table_args__ = (
        Index("uq_security_checks_run_step_image", "run_id", "step", text("coalesce(image, '')"), unique=True),
        Index("ix_security_checks_run", "run_id"),   # el de la migración 0007 (auditoría BD-06)
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("security_runs.id"), nullable=False)
    # secretos · construccion · vulnerabilidades · sbom · firma · verificacion
    step: Mapped[str] = mapped_column(String(30), nullable=False)
    # Imagen a la que aplica; nulo en los controles de toda la versión (secretos)
    image: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(10), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # Reporte completo del control (Gitleaks, Trivy, SBOM...): la evidencia que se muestra en el Hub
    # Diferido: no se trae de la base salvo que alguien lo pida (la lista de corridas no lo necesita; auditoría BD-03)
    report: Mapped[dict | list | None] = mapped_column(JSON_DOC, nullable=True, deferred=True)
    # Si el control guardó reporte: se calcula al registrarlo para que la lista no tenga que cargar el JSON de Trivy o del SBOM solo para saberlo
    has_report: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    run = relationship("SecurityRun", back_populates="checks")

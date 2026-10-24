# Resultado de un control de la puerta de seguridad, con su evidencia (tabla security_checks, spec 006).
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class SecurityCheck(Base):
    __tablename__ = "security_checks"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("security_runs.id"), nullable=False)
    # secretos · construccion · vulnerabilidades · sbom · firma · verificacion
    step: Mapped[str] = mapped_column(String(30), nullable=False)
    # Imagen a la que aplica; nulo en los controles de toda la versión (secretos)
    image: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(10), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # Reporte completo del control (Gitleaks, Trivy, SBOM...): la evidencia que se muestra en el Hub
    report: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    run = relationship("SecurityRun", back_populates="checks")

    @property
    def has_report(self) -> bool:
        return self.report is not None

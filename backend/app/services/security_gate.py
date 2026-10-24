# Puerta de seguridad: estado de la última corrida de una versión y reglas para abrirla y cerrarla (spec 006).
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.security_run import SecurityRun

# Controles de la puerta, en el orden en que corren
STEP_SECRETS = "secretos"
IMAGE_STEPS = ("construccion", "vulnerabilidades", "sbom", "firma", "verificacion")
STEPS = (STEP_SECRETS, *IMAGE_STEPS)

SIN_CORRIDA = "sin_corrida"
EN_CURSO = "en_curso"
OK = "ok"
FALLO = "fallo"


@dataclass(frozen=True)
class Gate:
    """Estado de la puerta para una versión: `sin_corrida`, `en_curso`, `ok` o `fallo` (con el control)."""

    status: str
    run: SecurityRun | None = None

    @property
    def failed_step(self) -> str | None:
        return self.run.failed_step if self.run is not None else None


def latest_run(db: Session, service_id: int, version: str) -> SecurityRun | None:
    """La última corrida de la versión: si se vuelve a subir, vale la más reciente."""
    return db.scalar(
        select(SecurityRun)
        .where(SecurityRun.service_id == service_id, SecurityRun.version == version)
        .order_by(SecurityRun.id.desc())
        .limit(1)
    )


def gate_status(db: Session, service_id: int, version: str) -> Gate:
    run = latest_run(db, service_id, version)
    if run is None:
        return Gate(SIN_CORRIDA)
    return Gate(run.status, run)

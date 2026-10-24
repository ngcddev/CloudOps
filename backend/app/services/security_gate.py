# Puerta de seguridad: estado de la última corrida de una versión y reglas para abrirla y cerrarla (spec 006).
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.security_check import SecurityCheck
from app.models.security_run import SecurityRun

# Controles de la puerta, en el orden en que corren
STEP_SECRETS = "secretos"
IMAGE_STEPS = ("construccion", "vulnerabilidades", "sbom", "firma", "verificacion")
STEPS = (STEP_SECRETS, *IMAGE_STEPS)

SIN_CORRIDA = "sin_corrida"
EN_CURSO = "en_curso"
OK = "ok"
FALLO = "fallo"


class GateError(Exception):
    """Un evento de la puerta que no se puede aplicar (corrida cerrada, paso repetido, imagen ajena...)."""


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


def open_run(db: Session, service_id: int, version: str, commit_sha: str | None, images: list[str]) -> SecurityRun:
    """Abre una corrida nueva para la versión; las anteriores quedan como historial."""
    run = SecurityRun(
        service_id=service_id, version=version, commit_sha=commit_sha, images=images, status=EN_CURSO
    )
    db.add(run)
    db.flush()
    return run


def _expected(run: SecurityRun) -> list[tuple[str, str | None]]:
    """Controles que una corrida necesita para estar completa: secretos una vez y el resto por cada imagen."""
    expected: list[tuple[str, str | None]] = [(STEP_SECRETS, None)]
    for image in run.images:
        expected.extend((step, image) for step in IMAGE_STEPS)
    return expected


def missing_checks(run: SecurityRun) -> list[tuple[str, str | None]]:
    """Controles que faltan o no pasaron: una corrida solo es `ok` si todos los esperados están en ok."""
    passed = {(c.step, c.image) for c in run.checks if c.status == OK}
    return [item for item in _expected(run) if item not in passed]


def add_check(
    db: Session,
    run: SecurityRun,
    step: str,
    status: str,
    summary: str,
    report: dict | list | None,
    image: str | None,
) -> SecurityCheck:
    """Registra un control. Un control que falla cierra la corrida en `fallo` de inmediato."""
    if run.status != EN_CURSO:
        raise GateError("La corrida de esa versión ya terminó.")
    if step == STEP_SECRETS:
        image = None  # el control de secretos revisa la versión completa, no una imagen
    elif image not in run.images:
        raise GateError(f"La imagen «{image}» no es una de las que declaró la corrida: {', '.join(run.images)}.")
    if any(c.step == step and c.image == image for c in run.checks):
        raise GateError("Ese control ya se registró en esta corrida.")
    check = SecurityCheck(run=run, step=step, image=image, status=status, summary=summary, report=report)
    db.add(check)
    db.flush()
    if status == FALLO:
        close_run(db, run, FALLO, failed_step=step)
    return check


def close_run(
    db: Session,
    run: SecurityRun,
    status: str,
    failed_step: str | None = None,
    image_digests: dict | None = None,
) -> SecurityRun:
    """Cierra la corrida. `ok` exige todos los controles esperados en ok; si falta alguno queda en `fallo`."""
    if run.status != EN_CURSO:
        return run
    if status == OK:
        missing = missing_checks(run)
        if missing:
            status, failed_step = FALLO, missing[0][0]
    elif failed_step is None:
        failed_step = "pipeline"  # el flujo terminó mal sin registrar qué control falló
    run.status = status
    run.failed_step = failed_step if status == FALLO else None
    run.image_digests = image_digests
    run.finished_at = datetime.now(timezone.utc)
    db.flush()
    return run

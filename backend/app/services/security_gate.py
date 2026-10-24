# Puerta de seguridad: estado de la última corrida de una versión y reglas para abrirla y cerrarla (spec 006).
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.change_request import ChangeRequest
from app.models.security_check import SecurityCheck
from app.models.security_run import SecurityRun
from app.services import audit
from app.services.change_flow import step_event, transition

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


# Nombre de cada control para quien opera la consola (el cliente nunca ve esto: ver CLIENT_TEXT)
STEP_LABELS = {
    "secretos": "secretos en el código",
    "construccion": "construcción de la imagen",
    "vulnerabilidades": "vulnerabilidades críticas",
    "sbom": "inventario de componentes (SBOM)",
    "firma": "firma de la imagen",
    "verificacion": "verificación de la firma",
    "pipeline": "ejecución del pipeline",
}


# Lo que ve el cliente cuando una actualización se detiene: textos del glosario (docs/glosario.md), sin jerga
_TEXT_SENSITIVE = "Una actualización fue detenida porque contenía información sensible."
_TEXT_ORIGIN = "Una actualización fue detenida porque no pasó la verificación de origen."
_TEXT_GENERIC = "Una actualización fue detenida antes de publicarse por controles de seguridad."
CLIENT_TEXT = {
    "secretos": _TEXT_SENSITIVE,
    "firma": _TEXT_ORIGIN,
    "verificacion": _TEXT_ORIGIN,
}


def client_text(step: str | None) -> str:
    return CLIENT_TEXT.get(step or "", _TEXT_GENERIC)


def not_approvable_message(version: str, gate: "Gate") -> str:
    """Por qué no se puede aprobar un cambio hacia `version`, para la agencia."""
    if gate.status == SIN_CORRIDA:
        return (
            f"La versión {version} aún no pasó por la puerta de seguridad: "
            "súbela al repositorio del sitio para que corran los controles."
        )
    if gate.status == EN_CURSO:
        return f"Los controles de seguridad de la versión {version} todavía están corriendo."
    label = STEP_LABELS.get(gate.failed_step or "", gate.failed_step or "un control")
    return f"La versión {version} no pasó los controles de seguridad ({label})."


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
    if run.status == FALLO:
        for change in pending_changes_for(db, run):
            reject_for_security(db, change, run)
    return run


def pending_changes_for(db: Session, run: SecurityRun) -> list[ChangeRequest]:
    """Solicitudes de cambio aún pendientes hacia la versión de esta corrida."""
    return list(
        db.scalars(
            select(ChangeRequest).where(
                ChangeRequest.service_id == run.service_id,
                ChangeRequest.to_version == run.version,
                ChangeRequest.status == "pendiente",
            )
        )
    )


def reject_for_security(db: Session, change: ChangeRequest, run: SecurityRun) -> None:
    """Rechaza la solicitud porque su versión no pasó la puerta, a nombre del sistema.

    El cliente ve el texto del glosario; el detalle técnico queda en una nota interna.
    """
    step = run.failed_step or "pipeline"
    label = STEP_LABELS.get(step, step)
    reason = f"Detenida por controles de seguridad: {label}"
    transition(change, "rechazada", reason=reason)
    db.add(step_event(change, "pendiente", None, client_text(step)))
    db.add(
        step_event(
            change, "pendiente", None,
            f"La versión {run.version} no pasó la puerta de seguridad (corrida #{run.id}): {label}.",
            internal=True,
        )
    )
    audit.record(
        db, None, "rechazar", "change_request", change.id,
        {"motivo": reason, "control": step, "corrida": run.id},
    )

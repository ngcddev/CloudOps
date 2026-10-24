# Consulta de la puerta de seguridad: corridas por servicio, controles de un cambio y su evidencia (spec 006, T17).
# Solo agencia: el cliente solo ve el texto en lenguaje de negocio que deja el rechazo en su solicitud.
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.deps import require_agency
from app.models.change_request import ChangeRequest
from app.models.security_check import SecurityCheck
from app.models.security_run import SecurityRun
from app.models.service import Service
from app.schemas.security import GateOut, SecurityRunOut
from app.services import security_gate as gate

router = APIRouter(prefix="/api", tags=["puerta de seguridad"], dependencies=[Depends(require_agency)])


@router.get("/services/{service_id}/security-runs", response_model=list[SecurityRunOut])
def service_security_runs(service_id: int, db: Session = Depends(get_db)):
    """Corridas de la puerta del servicio, de la más reciente a la más antigua, con sus controles."""
    if db.get(Service, service_id) is None:
        raise HTTPException(status_code=404, detail="El servicio no existe.")
    return db.scalars(
        select(SecurityRun)
        .options(selectinload(SecurityRun.checks))
        .where(SecurityRun.service_id == service_id)
        .order_by(SecurityRun.id.desc())
    ).all()


@router.get("/change-requests/{change_id}/checks", response_model=GateOut)
def change_checks(change_id: int, db: Session = Depends(get_db)):
    """La puerta de la versión destino del cambio: su estado y los controles de la última corrida."""
    change = db.get(ChangeRequest, change_id)
    if change is None:
        raise HTTPException(status_code=404, detail="La solicitud de cambio no existe.")
    current = gate.gate_status(db, change.service_id, change.to_version)
    return GateOut(
        version=change.to_version,
        status=current.status,
        failed_step=current.failed_step,
        run=SecurityRunOut.model_validate(current.run) if current.run is not None else None,
    )


@router.get("/security-checks/{check_id}/report")
def check_report(check_id: int, db: Session = Depends(get_db)):
    """Descarga el reporte completo de un control (la evidencia: Trivy, SBOM, resultado de verify...)."""
    check = db.get(SecurityCheck, check_id)
    if check is None or check.report is None:
        raise HTTPException(status_code=404, detail="Ese control no tiene reporte guardado.")
    name = f"{check.step}-{check.image or 'version'}-corrida{check.run_id}.json"
    return Response(
        content=json.dumps(check.report, ensure_ascii=False, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{name}"'},
    )

# Eventos de la puerta de seguridad: el pipeline cuenta qué controles pasó cada versión (spec 006, T13).
import hmac

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models.security_run import SecurityRun
from app.models.service import Service
from app.schemas.security import PipelineEvent, SecurityRunOut
from app.services import security_gate as gate

router = APIRouter(prefix="/api", tags=["puerta de seguridad"])


def require_pipeline(authorization: str | None = Header(default=None)) -> None:
    """Solo el pipeline entra: token propio (PIPELINE_TOKEN), distinto al de las sesiones."""
    expected = settings.pipeline_token
    supplied = (authorization or "").removeprefix("Bearer ").strip()
    if not expected or not supplied or not hmac.compare_digest(supplied, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token del pipeline no válido.",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/pipeline-events", response_model=SecurityRunOut, dependencies=[Depends(require_pipeline)])
def pipeline_event(event: PipelineEvent, db: Session = Depends(get_db)):
    """Abre la corrida de una versión, registra uno de sus controles o la cierra."""
    service = db.scalar(select(Service).where(Service.namespace == f"cliente-{event.site}"))
    if service is None:
        raise HTTPException(status_code=404, detail=f"El sitio «{event.site}» no existe.")

    try:
        if event.event == "inicio":
            images = event.images or [event.site]
            run = gate.open_run(db, service.id, event.version, event.commit_sha, images)
        else:
            if event.run_id is not None:
                # Un pipeline que se relanza no debe tocar la corrida de otro: los eventos van a la suya
                run = db.get(SecurityRun, event.run_id)
                if run is not None and (run.service_id != service.id or run.version != event.version):
                    raise HTTPException(status_code=409, detail="Esa corrida no es de este sitio y versión.")
            else:
                run = gate.latest_run(db, service.id, event.version)
            if run is None:
                raise HTTPException(
                    status_code=404, detail=f"La versión «{event.version}» no tiene una corrida abierta."
                )
            if event.event == "paso":
                gate.add_check(db, run, event.step, event.status, event.summary, event.report, event.image)
            else:
                gate.close_run(db, run, event.status, image_digests=event.image_digests)
    except gate.GateError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    db.commit()
    db.refresh(run)
    return run

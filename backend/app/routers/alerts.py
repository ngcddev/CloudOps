# Webhook de Alertmanager: recibe los avisos de caída y recuperación de los sitios (spec 008, T10-T12).
import hmac

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.schemas.alertmanager import AlertmanagerPayload, AlertmanagerResponse, AlertResult
from app.services import incident_alerts

router = APIRouter(prefix="/api/alerts", tags=["monitoreo"])


def require_alertmanager(authorization: str | None = Header(default=None)) -> None:
    """Solo Alertmanager entra: token propio (ALERTMANAGER_TOKEN), distinto al de sesiones y pipeline."""
    expected = settings.alertmanager_token
    supplied = (authorization or "").removeprefix("Bearer ").strip()
    if not expected or not supplied or not hmac.compare_digest(supplied, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de Alertmanager no válido.",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/alertmanager", response_model=AlertmanagerResponse, dependencies=[Depends(require_alertmanager)])
def alertmanager_webhook(payload: AlertmanagerPayload, db: Session = Depends(get_db)):
    """Procesa cada alerta del aviso en una sola transacción y responde 200 aunque alguna se ignore.

    Alertmanager reintenta si no recibe 2xx: un servicio desconocido no debe provocar reintentos sin fin.
    """
    results = []
    for alert in payload.alerts:
        if alert.status == "firing":
            result, incident_id = incident_alerts.open_from_alert(db, alert, settings.alert_confirm_seconds)
        else:
            result, incident_id = incident_alerts.resolve_from_alert(db, alert)
        results.append(AlertResult(fingerprint=alert.fingerprint, result=result, incident_id=incident_id))
    db.commit()
    return AlertmanagerResponse(results=results)

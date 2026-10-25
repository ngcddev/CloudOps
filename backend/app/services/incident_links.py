# Enlaces del detalle de un incidente: registros del sitio en Grafana y último cambio en Gitea (spec 008, T07).
import json
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.change_request import ChangeRequest
from app.models.deployment import Deployment
from app.models.incident import Incident

# Los registros se abren desde un poco antes del inicio, para ver lo que llevó a la falla
LOGS_MARGIN = timedelta(minutes=5)
# uid de la fuente de datos de Loki provisionada en Grafana (observability/grafana)
LOKI_DATASOURCE_UID = "loki"


def _as_utc(value: datetime | None) -> datetime | None:
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _ms(value: datetime) -> str:
    """Grafana recibe las fechas del rango como milisegundos desde 1970."""
    return str(int(value.timestamp() * 1000))


def logs_url(grafana_url: str, namespace: str, started_at: datetime, mitigated_at: datetime | None) -> str | None:
    """Grafana Explore con Loki y `{namespace="<ns>"}`, de 5 min antes del inicio a la mitigación (o ahora)."""
    if not grafana_url:
        return None
    pane = {
        "datasource": LOKI_DATASOURCE_UID,
        "queries": [
            {
                "refId": "A",
                "expr": f'{{namespace="{namespace}"}}',
                "datasource": {"type": "loki", "uid": LOKI_DATASOURCE_UID},
            }
        ],
        "range": {
            "from": _ms(_as_utc(started_at) - LOGS_MARGIN),
            "to": _ms(_as_utc(mitigated_at)) if mitigated_at is not None else "now",
        },
    }
    panes = quote(json.dumps({"incidente": pane}, separators=(",", ":")), safe="")
    return f"{grafana_url.rstrip('/')}/explore?schemaVersion=1&orgId=1&panes={panes}"


def commit_url(gitea_public_url: str, repo: str, sha: str | None) -> str | None:
    """Dirección del commit de hub-gitops en Gitea tal como la abre el navegador."""
    if not gitea_public_url or not sha:
        return None
    return f"{gitea_public_url.rstrip('/')}/{repo}/commit/{sha}"


def last_change(db: Session, service_id: int, gitea_public_url: str, repo: str) -> dict | None:
    """Última publicación del servicio y el cambio que la pidió, con el enlace a su commit."""
    deployment = db.scalar(
        select(Deployment).where(Deployment.service_id == service_id).order_by(Deployment.id.desc()).limit(1)
    )
    if deployment is None:
        return None
    change = db.scalar(
        select(ChangeRequest)
        .where(ChangeRequest.service_id == service_id, ChangeRequest.to_version == deployment.version)
        .order_by(ChangeRequest.id.desc())
        .limit(1)
    )
    sha = deployment.commit_sha or (change.gitops_commit_sha if change is not None else None)
    return {
        "version": deployment.version,
        "author": deployment.author,
        "source": deployment.source,
        "deployed_at": _as_utc(deployment.created_at),
        "change_request_id": change.id if change is not None else None,
        "commit_sha": sha,
        "commit_url": commit_url(gitea_public_url, repo, sha),
    }


def build_links(db: Session, incident: Incident, grafana_url: str, gitea_public_url: str, repo: str) -> dict:
    """Los dos enlaces que muestra el detalle del incidente para diagnosticar rápido (HU-3, CA-7)."""
    return {
        "logs_url": logs_url(grafana_url, incident.service.namespace, incident.started_at, incident.mitigated_at),
        "last_change": last_change(db, incident.service_id, gitea_public_url, repo),
    }

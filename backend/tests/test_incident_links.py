# Pruebas de los enlaces del incidente: registros en Grafana y último cambio en Gitea (spec 008, T07).
import json
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlsplit

from sqlalchemy import select

from app.models import ChangeRequest, Deployment, Incident, Service, Ticket
from app.services.incident_links import build_links, commit_url, logs_url

T0 = datetime(2026, 10, 24, 14, 0, tzinfo=timezone.utc)
GRAFANA = "http://grafana.hub.local"
GITEA = "http://gitea.hub.local"
REPO = "forja-digital/hub-gitops"


def _pane(url: str) -> dict:
    query = parse_qs(urlsplit(url).query)
    return json.loads(query["panes"][0])["incidente"]


def test_registros_desde_5_min_antes_del_inicio_hasta_ahora():
    url = logs_url(GRAFANA, "cliente-restaurante", T0, None)

    assert url.startswith("http://grafana.hub.local/explore?")
    pane = _pane(url)
    assert pane["queries"][0]["expr"] == '{namespace="cliente-restaurante"}'
    assert pane["datasource"] == "loki"
    assert pane["range"]["from"] == str(int((T0 - timedelta(minutes=5)).timestamp() * 1000))
    assert pane["range"]["to"] == "now"


def test_registros_hasta_la_mitigacion_y_sin_grafana_no_hay_enlace():
    mitigated = T0 + timedelta(minutes=12)

    assert _pane(logs_url(GRAFANA + "/", "cliente-restaurante", T0, mitigated))["range"]["to"] == str(
        int(mitigated.timestamp() * 1000)
    )
    assert logs_url("", "cliente-restaurante", T0, None) is None


def test_enlace_al_commit():
    assert commit_url(GITEA, REPO, "abc123") == "http://gitea.hub.local/forja-digital/hub-gitops/commit/abc123"
    assert commit_url("", REPO, "abc123") is None
    assert commit_url(GITEA, REPO, None) is None


def test_incidente_de_la_sazon_con_un_cambio_publicado(seeded):
    db = seeded
    service = db.scalar(select(Service).where(Service.namespace == "cliente-restaurante"))
    ticket = db.scalar(select(Ticket).limit(1))
    change = ChangeRequest(
        ticket_id=ticket.id, service_id=service.id, from_version="v1", to_version="v2",
        status="desplegado", gitops_commit_sha="f00dbabe",
    )
    db.add(change)
    db.add(Deployment(service_id=service.id, version="v2", commit_sha="f00dbabe", author="Ana Técnica"))
    incident = Incident(
        service_id=service.id, priority="P1", status="abierto", source="alerta", fingerprint="fp",
        title="El sitio no responde", started_at=T0, response_due_at=T0 + timedelta(minutes=15),
        resolution_due_at=T0 + timedelta(hours=4),
    )
    db.add(incident)
    db.commit()

    links = build_links(db, incident, GRAFANA, GITEA, REPO)

    assert _pane(links["logs_url"])["queries"][0]["expr"] == '{namespace="cliente-restaurante"}'
    last = links["last_change"]
    assert (last["version"], last["author"], last["change_request_id"]) == ("v2", "Ana Técnica", change.id)
    assert last["commit_url"] == "http://gitea.hub.local/forja-digital/hub-gitops/commit/f00dbabe"


def test_servicio_sin_publicaciones_no_tiene_ultimo_cambio(seeded):
    db = seeded
    service = db.scalar(select(Service).where(Service.namespace == "cliente-ferreteria"))
    incident = Incident(
        service_id=service.id, priority="P2", status="abierto", source="manual", title="Lento",
        started_at=T0, response_due_at=T0 + timedelta(hours=1), resolution_due_at=T0 + timedelta(hours=8),
    )
    db.add(incident)
    db.commit()

    assert build_links(db, incident, GRAFANA, GITEA, REPO)["last_change"] is None

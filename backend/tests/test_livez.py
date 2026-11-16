# La liveness de la API no depende de la base (spec 022, T09; auditoría K8-03): /livez dice si el proceso responde y /health si hay base. Con una sola sonda
# para las dos cosas, un reinicio de PostgreSQL hacía que el kubelet matara la API en bucle, mucho después de que la base volviera.
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from app.db import get_db
from app.main import app

API_YAML = Path("/gitops/hub/api.yaml")


class _SesionSinBase:
    """Una sesión cuya base no contesta."""

    def execute(self, *_args, **_kwargs):
        raise ConnectionError("PostgreSQL no responde")


def _sin_base():
    yield _SesionSinBase()


@pytest.fixture
def con_la_base_caida():
    app.dependency_overrides[get_db] = _sin_base
    yield TestClient(app)
    app.dependency_overrides.pop(get_db, None)


def test_livez_responde_ok_aunque_la_base_este_caida(con_la_base_caida):
    respuesta = con_la_base_caida.get("/livez")

    assert respuesta.status_code == 200 and respuesta.json() == {"status": "ok"}


def test_health_sigue_diciendo_503_sin_base(con_la_base_caida):
    # La readiness sí debe sacar a la API del Service cuando no hay base
    respuesta = con_la_base_caida.get("/health")

    assert respuesta.status_code == 503


def test_livez_no_pide_una_conexion_a_la_base():
    def explota():
        raise AssertionError("/livez no debe abrir una sesión de base")
        yield

    app.dependency_overrides[get_db] = explota
    try:
        assert TestClient(app).get("/livez").status_code == 200
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.skipif(not API_YAML.exists(), reason="gitops no está montado en /gitops")
def test_el_manifiesto_separa_la_vida_de_la_readiness_y_da_margen_al_arranque():
    api = next(d for d in yaml.safe_load_all(API_YAML.read_text(encoding="utf-8")) if d and d["kind"] == "Deployment" and d["metadata"]["name"] == "api")
    contenedor = api["spec"]["template"]["spec"]["containers"][0]

    assert contenedor["livenessProbe"]["httpGet"]["path"] == "/livez"       # no depende de la base: no reinicia al caer PostgreSQL
    assert contenedor["readinessProbe"]["httpGet"]["path"] == "/health"     # sí depende: sin base sale del Service
    arranque = contenedor["startupProbe"]
    assert arranque["httpGet"]["path"] == "/livez"
    assert arranque["periodSeconds"] * arranque["failureThreshold"] >= 120   # alembic y la semilla tras una actualización o un reinicio del nodo
    assert all(contenedor[sonda]["timeoutSeconds"] >= 3 for sonda in ("startupProbe", "livenessProbe", "readinessProbe"))

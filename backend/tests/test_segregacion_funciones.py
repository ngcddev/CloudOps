# Segregación de funciones (spec 018, T05): quien pide un cambio de versión no puede aprobarlo; otra persona de la agencia sí.
import pytest
from sqlalchemy import select

from app.config import settings
from app.integrations.gitea import GiteaClient
from app.main import app
from app.models import AuditLog, Service
from app.routers.change_requests import get_gitea
from tests.fake_gitea import FakeGitea
from tests.test_change_approve import ARCHIVOS

SOFIA = "sofia@forjadigital.test"
CAMILO = "camilo@forjadigital.test"


@pytest.fixture(autouse=True)
def segregacion_activa(monkeypatch):
    """El resto de las pruebas la apagan (conftest); aquí se prueba con el valor por defecto de producción."""
    monkeypatch.setattr(settings, "segregacion_funciones", True)


@pytest.fixture
def gitea():
    with FakeGitea(ARCHIVOS) as fake:
        app.dependency_overrides[get_gitea] = lambda: GiteaClient(fake.url, fake.repo, fake.token)
        yield fake
        app.dependency_overrides.pop(get_gitea, None)


@pytest.fixture
def cambio(seeded, as_user, pass_gate):
    """Un cambio pendiente de El Tornillo, pedido por Sofía."""
    pass_gate("cliente-ferreteria", "v1.1")
    service = seeded.scalar(select(Service).where(Service.namespace == "cliente-ferreteria"))
    sofia = as_user(SOFIA)
    ticket = sofia.post(
        "/api/tickets",
        json={"service_id": service.id, "title": "Publicar la portada", "description": "Portada de temporada.", "kind": "cambio"},
    ).json()
    return sofia.post("/api/change-requests", json={"ticket_id": ticket["id"], "to_version": "v1.1"}).json()


def test_quien_pidio_el_cambio_no_puede_aprobarlo(as_user, gitea, cambio):
    respuesta = as_user(SOFIA).post(f"/api/change-requests/{cambio['id']}/approve")

    assert respuesta.status_code == 403
    assert "otra persona" in respuesta.json()["detail"]
    assert gitea.commits == []


def test_el_intento_queda_en_la_bitacora_y_el_cambio_sigue_pendiente(as_user, seeded, gitea, cambio):
    as_user(SOFIA).post(f"/api/change-requests/{cambio['id']}/approve")

    intento = seeded.scalar(select(AuditLog).where(AuditLog.action == "denegar", AuditLog.entity_id == cambio["id"]))
    assert intento is not None and "segregación" in str(intento.details)
    assert as_user(SOFIA).get("/api/change-requests", params={"status": "pendiente"}).json()[0]["id"] == cambio["id"]


def test_otra_persona_de_la_agencia_si_puede_aprobarlo(as_user, gitea, cambio):
    respuesta = as_user(CAMILO).post(f"/api/change-requests/{cambio['id']}/approve")

    assert respuesta.status_code == 200
    assert respuesta.json()["approved_by_name"] == "Camilo Torres"
    assert len(gitea.commits) == 1


def test_apagada_por_configuracion_quien_pidio_puede_aprobar(as_user, gitea, cambio, monkeypatch):
    monkeypatch.setattr(settings, "segregacion_funciones", False)

    assert as_user(SOFIA).post(f"/api/change-requests/{cambio['id']}/approve").status_code == 200

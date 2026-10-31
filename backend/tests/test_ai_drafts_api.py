# Pruebas de la API de los borradores con el asistente simulado (spec 012, T06-T09).
import pytest
from sqlalchemy import select

from app.main import app
from app.models import AiDraft, Incident, Service
from app.routers.ai_drafts import get_writer
from tests.ai_support import mitigated_incident
from tests.fake_ollama import FakeOllama
from tests.rollback_support import open_incident


@pytest.fixture
def client(as_agency):
    return as_agency


@pytest.fixture
def assistant():
    """El asistente simulado, respondiendo; cada prueba puede pedirle que falle."""
    fake = FakeOllama()
    app.dependency_overrides[get_writer] = lambda: fake
    yield fake
    app.dependency_overrides.pop(get_writer, None)


@pytest.fixture
def incidente(seeded) -> Incident:
    return mitigated_incident(seeded)


# ---------- T06: generar ----------


def test_genera_los_dos_borradores(client, assistant, incidente):
    response = client.post(f"/api/incidents/{incidente.id}/ai-drafts")

    assert response.status_code == 201
    body = response.json()
    assert [d["kind"] for d in body["drafts"]] == ["resumen", "mensaje_cliente"]
    assert {d["status"] for d in body["drafts"]} == {"borrador_ia"}
    assert body["problems"] == []


def test_un_cerrado_tambien_genera(client, assistant, seeded):
    cerrado = mitigated_incident(seeded, status="cerrado")
    assert client.post(f"/api/incidents/{cerrado.id}/ai-drafts").status_code == 201


def test_abierto_no_genera(client, assistant, seeded):
    sazon = seeded.scalar(select(Service).where(Service.namespace == "cliente-restaurante"))
    abierto = open_incident(seeded, sazon)

    response = client.post(f"/api/incidents/{abierto.id}/ai-drafts")
    assert response.status_code == 409
    assert "mitigado" in response.json()["detail"]


def test_sin_asistente_avisa_que_se_escriba_a_mano(client, incidente):
    response = client.post(f"/api/incidents/{incidente.id}/ai-drafts")

    assert response.status_code == 503
    assert "Escribe el texto a mano" in response.json()["detail"]


def test_si_el_asistente_no_responde_el_incidente_sigue_igual(client, assistant, seeded, incidente):
    assistant.fail = True

    response = client.post(f"/api/incidents/{incidente.id}/ai-drafts")

    assert response.status_code == 503
    assert "60 segundos" in response.json()["detail"] and "Escribe el texto a mano" in response.json()["detail"]
    seeded.expire_all()
    assert seeded.scalars(select(AiDraft)).all() == []
    assert seeded.get(Incident, incidente.id).status == "mitigado"


def test_el_cliente_no_puede_generar(as_client, assistant, incidente):
    assert as_client.post(f"/api/incidents/{incidente.id}/ai-drafts").status_code == 403


def test_incidente_que_no_existe(client, assistant, seeded):
    assert client.post("/api/incidents/999/ai-drafts").status_code == 404


# ---------- T07: listar ----------


def test_lista_los_borradores_en_orden(client, assistant, incidente):
    client.post(f"/api/incidents/{incidente.id}/ai-drafts")
    client.post(f"/api/incidents/{incidente.id}/ai-drafts")

    body = client.get(f"/api/incidents/{incidente.id}/drafts").json()
    assert [d["kind"] for d in body["drafts"]] == ["resumen", "mensaje_cliente"] * 2
    assert [d["id"] for d in body["drafts"]] == sorted(d["id"] for d in body["drafts"])
    assert {d["status"] for d in body["drafts"]} == {"borrador_ia"}


def test_las_plantillas_traen_las_horas_reales(client, incidente):
    templates = client.get(f"/api/incidents/{incidente.id}/drafts").json()["manual_templates"]

    assert templates["mensaje_cliente"] == (
        "Detectamos una falla temporal en su sitio a las 14:00. Activamos la recuperación y a las 14:07 "
        "el servicio volvió a funcionar. Tiempo total: 7 minutos."
    )
    assert "14:00" in templates["resumen"] and "14:07" in templates["resumen"]
    assert "rollback de v2 a v1" in templates["resumen"]


def test_la_plantilla_del_cerrado_lleva_la_causa_raiz(client, seeded):
    cerrado = mitigated_incident(seeded, status="cerrado")
    resumen = client.get(f"/api/incidents/{cerrado.id}/drafts").json()["manual_templates"]["resumen"]

    assert resumen.endswith("Causa raíz: La versión nueva respondía con error en la página principal.")


def test_sin_mitigar_no_hay_plantillas(client, seeded):
    sazon = seeded.scalar(select(Service).where(Service.namespace == "cliente-restaurante"))
    body = client.get(f"/api/incidents/{open_incident(seeded, sazon).id}/drafts").json()

    assert body == {"drafts": [], "manual_templates": {"resumen": None, "mensaje_cliente": None}}


def test_el_cliente_no_ve_los_borradores(as_client, incidente):
    assert as_client.get(f"/api/incidents/{incidente.id}/drafts").status_code == 403

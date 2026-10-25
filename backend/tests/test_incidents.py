# Pruebas de los incidentes manuales: abrir, listar, tomar, anotar, mitigar y cerrar (spec 008, T04-T06).
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.models import AuditLog, Client, Incident, Service
from app.routers import incidents as incidents_router

T0 = datetime(2026, 10, 24, 14, 0, tzinfo=timezone.utc)


@pytest.fixture
def client(as_agency):
    """Estas pruebas operan como técnico de la agencia; los permisos se prueban con as_client."""
    return as_agency


@pytest.fixture
def clock(monkeypatch):
    """Reloj controlado: `clock.at(minutos)` fija la hora del Hub en T0 + minutos."""

    class Clock:
        now = T0

        def at(self, minutes: float) -> None:
            self.now = T0 + timedelta(minutes=minutes)

    fake = Clock()
    monkeypatch.setattr(incidents_router, "utcnow", lambda: fake.now)
    return fake


def _service_id(session_factory, namespace: str) -> int:
    with session_factory() as db:
        return db.scalar(select(Service.id).where(Service.namespace == namespace))


def _open(client, session_factory, namespace="cliente-restaurante", priority="P1", title="El sitio no carga"):
    response = client.post(
        "/api/incidents",
        json={"service_id": _service_id(session_factory, namespace), "priority": priority, "title": title},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_p1_manual_de_la_sazon_vence_a_las_1415_y_1800(client, seeded, session_factory, clock):
    incident = _open(client, session_factory)

    assert incident["status"] == "abierto"
    assert incident["source"] == "manual"
    assert incident["client_name"] == "Restaurante La Sazón"
    assert incident["started_at"].startswith("2026-10-24T14:00:00")
    assert incident["response_due_at"].startswith("2026-10-24T14:15:00")
    assert incident["resolution_due_at"].startswith("2026-10-24T18:00:00")
    assert (incident["response_state"], incident["resolution_state"]) == ("a_tiempo", "a_tiempo")

    with session_factory() as db:
        saved = db.get(Incident, incident["id"])
        assert [event.type for event in saved.events] == ["detectado"]
        log = db.scalar(select(AuditLog).where(AuditLog.entity == "incident"))
        assert (log.action, log.entity_id) == ("crear", incident["id"])


def test_p2_de_el_tornillo_usa_el_horario_de_su_plan(client, seeded, session_factory, clock):
    # 14:00 UTC = 09:00 en Bogotá, un sábado dentro del horario Estándar (lun-sab 07:00-20:00)
    incident = _open(client, session_factory, "cliente-ferreteria", "P2")

    assert incident["response_due_at"].startswith("2026-10-24T15:00:00")


def test_listar_filtra_por_estado_cliente_y_prioridad(client, seeded, session_factory, clock):
    p1 = _open(client, session_factory)
    p2 = _open(client, session_factory, "cliente-ferreteria", "P2")
    with session_factory() as db:
        tornillo = db.scalar(select(Client.id).where(Client.name == "Ferretería El Tornillo"))

    assert [i["id"] for i in client.get("/api/incidents").json()] == [p2["id"], p1["id"]]
    assert [i["id"] for i in client.get("/api/incidents", params={"priority": "P1"}).json()] == [p1["id"]]
    assert [i["id"] for i in client.get("/api/incidents", params={"client_id": tornillo}).json()] == [p2["id"]]
    assert client.get("/api/incidents", params={"status": "cerrado"}).json() == []


def test_el_reloj_de_la_lista_corre_con_la_hora_real(client, seeded, session_factory, clock):
    _open(client, session_factory)

    clock.at(13)
    assert client.get("/api/incidents").json()[0]["response_state"] == "en_riesgo"
    clock.at(16)
    assert client.get("/api/incidents").json()[0]["response_state"] == "vencido"


def test_servicio_inexistente_y_datos_invalidos(client, seeded):
    assert client.post("/api/incidents", json={"service_id": 999, "priority": "P1", "title": "x"}).status_code == 404
    invalid = client.post("/api/incidents", json={"service_id": 1, "priority": "P9", "title": " "})
    assert invalid.status_code == 422


def test_el_cliente_no_ve_ni_abre_incidentes(as_client, seeded, session_factory):
    service_id = _service_id(session_factory, "cliente-restaurante")

    assert as_client.get("/api/incidents").status_code == 403
    assert as_client.post("/api/incidents", json={"service_id": service_id, "priority": "P1", "title": "x"}).status_code == 403

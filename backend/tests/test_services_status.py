# Pruebas del estado de los servicios y el historial de versiones (spec 005, T16 · CA-4).
from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.models import ChangeRequest, Deployment, Service, Ticket, User


@pytest.fixture
def client(as_agency):
    """Estas pruebas operan como técnico de la agencia (spec 007); los permisos se prueban con as_client y anonymous."""
    return as_agency


@pytest.fixture
def ferreteria(seeded) -> Service:
    return seeded.scalar(select(Service).where(Service.namespace == "cliente-ferreteria"))


def test_devuelve_los_tres_clientes_con_version_sync_y_salud(client, seeded):
    response = client.get("/api/services/status")

    assert response.status_code == 200
    by_ns = {item["namespace"]: item for item in response.json()}
    assert set(by_ns) == {"cliente-restaurante", "cliente-ferreteria", "cliente-consultorio"}
    tornillo = by_ns["cliente-ferreteria"]
    assert tornillo["client_name"] == "Ferretería El Tornillo"
    assert (tornillo["current_version"], tornillo["stable_version"]) == ("v1", "v1")
    assert (tornillo["sync_status"], tornillo["health_status"]) == ("Unknown", "Unknown")
    assert tornillo["last_author"] is None and tornillo["open_change_id"] is None


def test_muestra_la_version_nueva_el_estado_y_el_ultimo_autor(client, seeded, ferreteria):
    tecnico = seeded.scalar(select(User).where(User.role == "agencia"))
    ferreteria.current_version = ferreteria.stable_version = "v1.1"
    ferreteria.sync_status, ferreteria.health_status = "Synced", "Healthy"
    seeded.add(
        Deployment(
            service_id=ferreteria.id,
            version="v1.1",
            commit_sha="a" * 40,
            author=tecnico.name,
            source="cambio",
            created_at=datetime(2026, 10, 11, 15, 0, tzinfo=timezone.utc),
        )
    )
    seeded.commit()

    item = next(i for i in client.get("/api/services/status").json() if i["namespace"] == "cliente-ferreteria")

    assert item["current_version"] == "v1.1"
    assert (item["sync_status"], item["health_status"]) == ("Synced", "Healthy")
    assert item["last_author"] == tecnico.name
    assert item["last_change_at"].startswith("2026-10-11T15:00")


def test_indica_el_cambio_en_curso(client, seeded, ferreteria):
    ticket = Ticket(service_id=ferreteria.id, title="Portada", description="x", kind="cambio")
    seeded.add(ticket)
    seeded.flush()
    seeded.add(
        ChangeRequest(
            ticket_id=ticket.id, service_id=ferreteria.id, from_version="v1", to_version="v1.1",
            status="en_validacion",
        )
    )
    seeded.commit()

    item = next(i for i in client.get("/api/services/status").json() if i["namespace"] == "cliente-ferreteria")

    assert (item["open_change_status"], item["open_change_to_version"]) == ("en_validacion", "v1.1")


def test_historial_de_versiones_del_mas_reciente_al_mas_antiguo(client, seeded, ferreteria):
    for version in ("v1.1", "v1.2"):
        seeded.add(Deployment(service_id=ferreteria.id, version=version, author="Sofía", source="cambio"))
    seeded.commit()

    response = client.get(f"/api/services/{ferreteria.id}/deployments")

    assert response.status_code == 200
    assert [d["version"] for d in response.json()] == ["v1.2", "v1.1"]
    assert response.json()[0]["author"] == "Sofía"


def test_historial_de_un_servicio_sin_cambios_esta_vacio(client, ferreteria):
    assert client.get(f"/api/services/{ferreteria.id}/deployments").json() == []


def test_servicio_inexistente_es_404(client, seeded):
    assert client.get("/api/services/9999/deployments").status_code == 404


def test_el_estado_tecnico_de_los_servicios_es_solo_de_agencia(as_user, anonymous, ferreteria):
    cliente = as_user("contacto@eltornillo.test")

    assert cliente.get("/api/services/status").status_code == 403
    assert cliente.get(f"/api/services/{ferreteria.id}/deployments").status_code == 403
    assert anonymous.get("/api/services/status").status_code == 401
    assert anonymous.get(f"/api/services/{ferreteria.id}/deployments").status_code == 401


# --- Puerta de seguridad de la versión activa (spec 006, T20) ---


def test_indica_la_puerta_de_la_version_activa_de_cada_servicio(client, seeded, pass_gate):
    pass_gate("cliente-ferreteria", "v1")
    por_ns = {item["namespace"]: item for item in client.get("/api/services/status").json()}

    assert por_ns["cliente-ferreteria"]["security_status"] == "ok"
    assert por_ns["cliente-restaurante"]["security_status"] == "sin_corrida"
    assert por_ns["cliente-restaurante"]["security_failed_step"] is None


def test_la_puerta_de_otra_version_no_cuenta_como_la_activa(client, seeded, pass_gate):
    pass_gate("cliente-ferreteria", "v1.1")  # la activa sigue siendo v1

    por_ns = {item["namespace"]: item for item in client.get("/api/services/status").json()}

    assert por_ns["cliente-ferreteria"]["security_status"] == "sin_corrida"


def test_una_version_activa_que_fallo_la_puerta_dice_cual_control(client, seeded):
    from app.services import security_gate as gate

    servicio = seeded.scalar(select(Service).where(Service.namespace == "cliente-restaurante"))
    run = gate.open_run(seeded, servicio.id, "v1", None, ["restaurante"])
    gate.add_check(seeded, run, "secretos", "fallo", "1 hallazgo", None, None)
    seeded.commit()

    por_ns = {item["namespace"]: item for item in client.get("/api/services/status").json()}

    assert (por_ns["cliente-restaurante"]["security_status"], por_ns["cliente-restaurante"]["security_failed_step"]) == (
        "fallo", "secretos",
    )

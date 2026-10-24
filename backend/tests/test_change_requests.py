# Pruebas de crear y rechazar solicitudes de cambio (spec 005, T13).
import pytest
from sqlalchemy import select

from app.models import Service, TicketEvent, User


@pytest.fixture
def client(as_agency):
    """Estas pruebas operan como técnico de la agencia (spec 007); los permisos se prueban con as_client y anonymous."""
    return as_agency


@pytest.fixture
def ferreteria(seeded):
    """El servicio de El Tornillo, con la semilla cargada."""
    return seeded.scalar(select(Service).where(Service.namespace == "cliente-ferreteria"))


def _ticket(client, service_id, kind="cambio"):
    response = client.post(
        "/api/tickets",
        json={
            "service_id": service_id,
            "title": "Publicar la nueva portada",
            "description": "Queremos la portada de temporada.",
            "kind": kind,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create(client, ticket_id, to_version="v1.1", **extra):
    return client.post(
        "/api/change-requests", json={"ticket_id": ticket_id, "to_version": to_version, **extra}
    )


def test_crea_la_solicitud_en_pendiente_con_la_version_actual(client, ferreteria):
    ticket_id = _ticket(client, ferreteria.id)

    response = _create(client, ticket_id)

    assert response.status_code == 201
    body = response.json()
    assert (body["status"], body["from_version"], body["to_version"]) == ("pendiente", "v1", "v1.1")
    assert body["service_id"] == ferreteria.id
    assert body["approved_at"] is None and body["gitops_commit_sha"] is None


def test_el_paso_queda_en_el_historial_de_la_solicitud(client, seeded, ferreteria):
    tecnico = seeded.scalar(select(User).where(User.role == "agencia"))
    ticket_id = _ticket(client, ferreteria.id)

    _create(client, ticket_id, requested_by_id=tecnico.id)

    events = seeded.scalars(select(TicketEvent).where(TicketEvent.ticket_id == ticket_id)).all()
    assert [(e.type, e.from_value, e.to_value, e.actor_id) for e in events] == [
        ("cambio", None, "pendiente", tecnico.id)
    ]


def test_solo_acepta_solicitudes_de_tipo_cambio(client, ferreteria):
    ticket_id = _ticket(client, ferreteria.id, kind="solicitud")

    response = _create(client, ticket_id)

    assert response.status_code == 422
    assert "tipo cambio" in response.json()["detail"]


def test_solicitud_inexistente_es_404(client, seeded):
    assert _create(client, 9999).status_code == 404


def test_rechaza_una_version_invalida(client, ferreteria):
    ticket_id = _ticket(client, ferreteria.id)

    response = _create(client, ticket_id, to_version="v 1; rm -rf")

    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "La versión destino no es válida (por ejemplo: v1.1)."


def test_no_acepta_la_version_que_ya_corre(client, ferreteria):
    ticket_id = _ticket(client, ferreteria.id)

    response = _create(client, ticket_id, to_version="v1")

    assert response.status_code == 422
    assert "ya está en la versión v1" in response.json()["detail"]


def test_un_sitio_no_puede_tener_dos_cambios_en_curso(client, ferreteria):
    first = _ticket(client, ferreteria.id)
    second = _ticket(client, ferreteria.id)
    assert _create(client, first).status_code == 201

    response = _create(client, second, to_version="v1.2")

    assert response.status_code == 409


def test_rechaza_con_motivo_y_queda_registrado(client, seeded, ferreteria):
    tecnico = seeded.scalar(select(User).where(User.role == "agencia"))
    change_id = _create(client, _ticket(client, ferreteria.id)).json()["id"]

    response = client.post(
        f"/api/change-requests/{change_id}/reject",
        json={"reason": "La portada no cumple la guía de marca", "actor_id": tecnico.id},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "rechazada"
    assert response.json()["rejection_reason"] == "La portada no cumple la guía de marca"
    events = seeded.scalars(
        select(TicketEvent).where(TicketEvent.ticket_id == response.json()["ticket_id"]).order_by(TicketEvent.id)
    ).all()
    assert [(e.from_value, e.to_value, e.actor_id) for e in events][-1] == ("pendiente", "rechazada", tecnico.id)


@pytest.mark.parametrize("body", [{}, {"reason": ""}, {"reason": "   "}])
def test_rechazar_sin_motivo_es_422(client, ferreteria, body):
    change_id = _create(client, _ticket(client, ferreteria.id)).json()["id"]

    response = client.post(f"/api/change-requests/{change_id}/reject", json=body)

    assert response.status_code == 422
    assert "motivo" in response.json()["detail"][0]["msg"]


def test_no_se_rechaza_dos_veces_ni_una_inexistente(client, ferreteria):
    change_id = _create(client, _ticket(client, ferreteria.id)).json()["id"]
    client.post(f"/api/change-requests/{change_id}/reject", json={"reason": "No aplica"})

    again = client.post(f"/api/change-requests/{change_id}/reject", json={"reason": "No aplica"})
    missing = client.post("/api/change-requests/9999/reject", json={"reason": "No aplica"})

    assert again.status_code == 409
    assert missing.status_code == 404


def test_tras_rechazar_se_puede_pedir_otro_cambio(client, ferreteria):
    first = _create(client, _ticket(client, ferreteria.id)).json()["id"]
    client.post(f"/api/change-requests/{first}/reject", json={"reason": "Falta contenido"})

    assert _create(client, _ticket(client, ferreteria.id), to_version="v1.2").status_code == 201


def test_lista_las_solicitudes_de_cambio_con_nombres_y_filtra_por_estado(client, seeded, ferreteria):
    tecnico = seeded.scalar(select(User).where(User.role == "agencia"))
    first = _create(client, _ticket(client, ferreteria.id), requested_by_id=tecnico.id).json()["id"]
    client.post(f"/api/change-requests/{first}/reject", json={"reason": "Falta contenido"})
    second = _create(client, _ticket(client, ferreteria.id), to_version="v1.2").json()["id"]

    listed = client.get("/api/change-requests").json()

    assert [item["id"] for item in listed] == [second, first]
    assert listed[1]["requested_by_name"] == tecnico.name
    assert listed[1]["ticket_title"] == "Publicar la nueva portada"
    pendientes = client.get("/api/change-requests", params={"status": "pendiente"}).json()
    assert [item["id"] for item in pendientes] == [second]
    assert client.get("/api/change-requests", params={"service_id": 9999}).json() == []

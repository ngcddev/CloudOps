# Pruebas de creación, bandeja y detalle de solicitudes (spec 004, T09).
from sqlalchemy import select

from app.models import Client, Service, Ticket, TicketEvent
from app.seed import seed_if_empty


def _seed_service(session_factory):
    with session_factory() as db:
        seed_if_empty(db)
        service = db.scalar(select(Service).order_by(Service.id))
        client = db.scalar(select(Client).order_by(Client.id))
        return service.id, client.id


def test_crear_listar_filtrar_y_ver_ticket(client, session_factory):
    service_id, client_id = _seed_service(session_factory)
    payload = {
        "service_id": service_id,
        "title": "El menú no aparece",
        "description": "La carta del domingo no carga.",
    }

    created = client.post("/api/tickets", json=payload)
    assert created.status_code == 201
    ticket_id = created.json()["id"]
    assert created.json()["status"] == "abierto"

    listed = client.get("/api/tickets", params={"client_id": client_id, "status": "abierto"})
    assert listed.status_code == 200
    assert [ticket["id"] for ticket in listed.json()] == [ticket_id]

    detail = client.get(f"/api/tickets/{ticket_id}")
    assert detail.status_code == 200
    assert detail.json()["title"] == payload["title"]
    assert detail.json()["events"] == []


def test_lista_filtra_por_prioridad(client, session_factory):
    service_id, client_id = _seed_service(session_factory)
    first = client.post(
        "/api/tickets",
        json={"service_id": service_id, "title": "P1", "description": "Urgente"},
    ).json()["id"]
    second = client.post(
        "/api/tickets",
        json={"service_id": service_id, "title": "P2", "description": "Importante"},
    ).json()["id"]

    with session_factory() as db:
        db.get(Ticket, first).priority = "P1"
        db.get(Ticket, second).priority = "P2"
        db.commit()

    response = client.get("/api/tickets", params={"client_id": client_id, "priority": "P2"})
    assert response.status_code == 200
    assert [ticket["id"] for ticket in response.json()] == [second]


def test_detalle_devuelve_historial(client, session_factory):
    service_id, _ = _seed_service(session_factory)
    ticket_id = client.post(
        "/api/tickets",
        json={"service_id": service_id, "title": "Historial", "description": "Prueba"},
    ).json()["id"]
    with session_factory() as db:
        db.add(TicketEvent(ticket_id=ticket_id, type="comentario", note="Recibido", internal=False))
        db.commit()

    response = client.get(f"/api/tickets/{ticket_id}")
    assert response.status_code == 200
    assert response.json()["events"][0]["note"] == "Recibido"


def test_clasificar_propone_p2_calcula_sla_y_registra_evento(client, session_factory):
    service_id, _ = _seed_service(session_factory)
    ticket_id = client.post(
        "/api/tickets",
        json={"service_id": service_id, "title": "Menú", "description": "No aparece"},
    ).json()["id"]

    response = client.post(
        f"/api/tickets/{ticket_id}/classify",
        json={"impact": "alto", "urgency": "media"},
    )

    assert response.status_code == 200
    assert response.json()["priority"] == "P2"
    assert response.json()["response_due_at"] is not None
    assert response.json()["resolution_due_at"] is not None
    detail = client.get(f"/api/tickets/{ticket_id}").json()
    assert detail["events"][0]["type"] == "prioridad"


def test_corregir_prioridad_sin_motivo_responde_422(client, session_factory):
    service_id, _ = _seed_service(session_factory)
    ticket_id = client.post(
        "/api/tickets",
        json={"service_id": service_id, "title": "Menú", "description": "No aparece"},
    ).json()["id"]

    response = client.post(
        f"/api/tickets/{ticket_id}/classify",
        json={"impact": "alto", "urgency": "media", "priority": "P1"},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Debe indicar un motivo para corregir la prioridad propuesta."
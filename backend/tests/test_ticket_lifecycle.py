# Prueba punta a punta del ciclo de una solicitud (spec 004, T14).
from sqlalchemy import select

from app.models import Client, Service
from app.seed import seed_if_empty


def test_ciclo_completo_de_solicitud_desde_cliente_hasta_resuelto(client, session_factory):
    with session_factory() as db:
        seed_if_empty(db)
        service = db.scalar(select(Service).order_by(Service.id))
        client_id = db.scalar(select(Client.id).order_by(Client.id))

    created = client.post(
        "/api/tickets",
        json={
            "service_id": service.id,
            "created_by_id": 2,
            "title": "El menú del domingo no aparece",
            "description": "La carta no carga en el sitio.",
        },
    )
    assert created.status_code == 201
    ticket_id = created.json()["id"]

    classified = client.post(
        f"/api/tickets/{ticket_id}/classify",
        json={"impact": "alto", "urgency": "media"},
    )
    assert classified.status_code == 200
    assert classified.json()["priority"] == "P2"

    assigned = client.post(
        f"/api/tickets/{ticket_id}/assign",
        json={"assignee_id": 1, "actor_id": 1},
    )
    assert assigned.status_code == 200

    for new_status in ("en_progreso", "en_espera", "en_progreso", "resuelto", "cerrado"):
        transitioned = client.post(
            f"/api/tickets/{ticket_id}/transition",
            json={"new_status": new_status, "actor_id": 1},
        )
        assert transitioned.status_code == 200

    work_log = client.post(
        f"/api/tickets/{ticket_id}/work-logs",
        json={"user_id": 1, "hours": 1.5, "note": "Corrección del menú"},
    )
    assert work_log.status_code == 201

    agency_detail = client.get(f"/api/tickets/{ticket_id}")
    assert agency_detail.status_code == 200
    agency_body = agency_detail.json()
    assert agency_body["status"] == "cerrado"
    assert agency_body["priority"] == "P2"
    assert sum(log["hours"] for log in agency_body["work_logs"]) == 1.5
    assert len(agency_body["events"]) == 7
    assert all(event["created_at"] for event in agency_body["events"])
    assert all(event["actor_id"] in (None, 1) for event in agency_body["events"])

    client_detail = client.get(
        f"/api/tickets/{ticket_id}",
        params={"viewer_role": "cliente", "client_id": client_id},
    )
    assert client_detail.status_code == 200
    assert client_detail.json()["status"] == "Cerrado"
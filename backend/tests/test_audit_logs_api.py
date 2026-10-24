# Consulta de la bitácora: orden, filtros y permisos (spec 007, T15).
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.models import AuditLog, User
from app.services.audit import record


@pytest.fixture
def filas(seeded):
    sofia = seeded.scalar(select(User).where(User.email == "sofia@forjadigital.test"))
    camilo = seeded.scalar(select(User).where(User.email == "camilo@forjadigital.test"))
    hoy = datetime.now(timezone.utc)
    datos = [
        (sofia, "aprobar", "change_request", 1, hoy - timedelta(days=3)),
        (camilo, "asignar", "ticket", 2, hoy - timedelta(days=2)),
        (None, "desplegar", "change_request", 1, hoy - timedelta(days=1)),
    ]
    for user, action, entity, entity_id, cuando in datos:
        log = record(seeded, user, action, entity, entity_id)
        log.created_at = cuando
    seeded.commit()
    return sofia, camilo


def test_lista_las_mas_recientes_primero_y_nombra_al_sistema(as_agency, filas):
    body = as_agency.get("/api/audit-logs").json()

    assert [(row["action"], row["user_name"]) for row in body] == [
        ("desplegar", "Sistema"),
        ("asignar", "Camilo Torres"),
        ("aprobar", "Sofía Ramírez"),
    ]
    assert body[0]["user_id"] is None


def test_filtra_por_usuario_objeto_y_accion(as_agency, filas):
    sofia, _ = filas

    assert [r["action"] for r in as_agency.get("/api/audit-logs", params={"user_id": sofia.id}).json()] == ["aprobar"]
    assert [r["action"] for r in as_agency.get("/api/audit-logs", params={"entity": "ticket"}).json()] == ["asignar"]
    assert [r["action"] for r in as_agency.get("/api/audit-logs", params={"action": "desplegar"}).json()] == ["desplegar"]


def test_filtra_por_fechas(as_agency, filas):
    desde = (datetime.now(timezone.utc) - timedelta(days=2, hours=12)).isoformat()
    hasta = (datetime.now(timezone.utc) - timedelta(days=1, hours=12)).isoformat()

    todas_desde = as_agency.get("/api/audit-logs", params={"from": desde}).json()
    entre = as_agency.get("/api/audit-logs", params={"from": desde, "to": hasta}).json()

    assert [r["action"] for r in todas_desde] == ["desplegar", "asignar"]
    assert [r["action"] for r in entre] == ["asignar"]


def test_devuelve_como_maximo_200_filas(as_agency, seeded):
    for i in range(205):
        record(seeded, None, "desplegar", "change_request", i)
    seeded.commit()

    assert len(as_agency.get("/api/audit-logs").json()) == 200


def test_el_cliente_no_puede_ver_la_bitacora(as_client, filas):
    assert as_client.get("/api/audit-logs").status_code == 403


def test_la_bitacora_no_tiene_rutas_para_editar_ni_borrar(as_agency, filas):
    assert as_agency.delete("/api/audit-logs/1").status_code in (404, 405)
    assert as_agency.patch("/api/audit-logs/1", json={"action": "x"}).status_code in (404, 405)
    assert as_agency.post("/api/audit-logs", json={"action": "x"}).status_code in (404, 405)
    assert as_agency.put("/api/audit-logs", json={}).status_code in (404, 405)

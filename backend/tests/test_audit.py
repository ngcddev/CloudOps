# Pruebas de la bitácora: registro junto a la acción y migración (spec 007, T07).
import pytest
from sqlalchemy import select

from app.models import AuditLog, User
from app.services.audit import record


@pytest.fixture
def agency(db):
    user = User(name="Sofía", email="s@x.test", role="agencia")
    db.add(user)
    db.commit()
    return user


def test_record_agrega_la_fila_sin_hacer_commit(db, agency):
    record(db, agency, "aprobar", "change_request", 4, details={"to_version": "v1.1"}, ip="10.0.0.5")

    db.flush()
    assert db.scalar(select(AuditLog)) is not None  # visible en la misma sesión
    db.rollback()
    assert db.scalar(select(AuditLog)) is None  # la acción se deshizo y el registro también


def test_record_guarda_usuario_accion_objeto_y_hora(db, agency):
    record(db, agency, "aprobar", "change_request", 4, details={"to_version": "v1.1"}, ip="10.0.0.5")
    db.commit()

    log = db.scalar(select(AuditLog))
    assert (log.user_id, log.action, log.entity, log.entity_id) == (agency.id, "aprobar", "change_request", 4)
    assert log.details == {"to_version": "v1.1"}
    assert log.ip == "10.0.0.5"
    assert log.created_at is not None


def test_sin_usuario_la_accion_es_del_sistema(db):
    record(db, None, "desplegar", "change_request", 9)
    db.commit()

    log = db.scalar(select(AuditLog))
    assert log.user_id is None


# --- Correcciones de la revisión de código ---


def test_la_ip_es_la_que_agrega_el_proxy_no_la_que_escribe_el_cliente(as_agency, seeded):
    as_agency.post(
        "/api/clients", json={"name": "Panadería Luz"},
        headers={"X-Forwarded-For": "6.6.6.6, 10.1.2.3"},
    )

    log = seeded.scalar(select(AuditLog))
    assert log.ip == "10.1.2.3"


def test_sin_proxy_la_ip_es_la_de_la_conexion(as_agency, seeded):
    as_agency.post("/api/clients", json={"name": "Panadería Luz"})

    assert seeded.scalar(select(AuditLog)).ip == "testclient"


def test_registrar_horas_y_crear_proyectos_y_servicios_quedan_en_la_bitacora(as_agency, seeded):
    from app.models import Client, Plan, Ticket

    cliente = seeded.scalar(select(Client).order_by(Client.id))
    ticket = seeded.scalar(select(Ticket).order_by(Ticket.id))
    plan = seeded.scalar(select(Plan).order_by(Plan.id))

    as_agency.post(f"/api/tickets/{ticket.id}/work-logs", json={"hours": 1.5})
    proyecto = as_agency.post(f"/api/clients/{cliente.id}/projects", json={"name": "Sitio nuevo"}).json()
    as_agency.post(
        f"/api/projects/{proyecto['id']}/services",
        json={"name": "Web", "host": "nuevo.hub.local", "template": "landing", "namespace": "cliente-nuevo", "plan_id": plan.id},
    )

    logs = seeded.scalars(select(AuditLog).order_by(AuditLog.id)).all()
    assert [(log.action, log.entity) for log in logs] == [
        ("registrar_horas", "ticket"), ("crear", "project"), ("crear", "service"),
    ]
    assert logs[0].details == {"horas": 1.5}

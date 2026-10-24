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

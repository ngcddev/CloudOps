# Permisos, actor de la sesión y bitácora en las acciones sobre solicitudes (spec 007, T10).
import pytest
from sqlalchemy import select

from app.models import AuditLog, Ticket, TicketEvent, User, WorkLog


@pytest.fixture
def ticket(seeded) -> Ticket:
    return seeded.scalar(select(Ticket).where(Ticket.title == "Necesito actualizar el horario del menú"))


@pytest.fixture
def tecnico(seeded) -> User:
    return seeded.scalar(select(User).where(User.email == "sofia@forjadigital.test"))


ACCIONES = [
    ("classify", {"impact": "alto", "urgency": "media"}),
    ("assign", {"assignee_id": 1}),
    ("transition", {"new_status": "en_progreso"}),
    ("work-logs", {"hours": 1}),
]


@pytest.mark.parametrize(("ruta", "cuerpo"), ACCIONES)
def test_el_cliente_no_puede_ejecutar_acciones_de_agencia(as_client, seeded, ticket, ruta, cuerpo):
    response = as_client.post(f"/api/tickets/{ticket.id}/{ruta}", json=cuerpo)

    assert response.status_code == 403
    assert seeded.scalar(select(AuditLog)) is None


@pytest.mark.parametrize(("ruta", "cuerpo"), ACCIONES)
def test_sin_sesion_las_acciones_responden_401(anonymous, seeded, ticket, ruta, cuerpo):
    assert anonymous.post(f"/api/tickets/{ticket.id}/{ruta}", json=cuerpo).status_code == 401


def test_el_actor_es_el_usuario_del_token_aunque_el_cuerpo_traiga_otro(as_user, seeded, ticket, tecnico):
    otro = seeded.scalar(select(User).where(User.email == "camilo@forjadigital.test"))
    agencia = as_user("sofia@forjadigital.test")

    agencia.post(f"/api/tickets/{ticket.id}/classify", json={"impact": "alto", "urgency": "media", "actor_id": otro.id})
    agencia.post(f"/api/tickets/{ticket.id}/assign", json={"assignee_id": otro.id, "actor_id": otro.id})
    agencia.post(f"/api/tickets/{ticket.id}/transition", json={"new_status": "en_progreso", "actor_id": otro.id})
    agencia.post(f"/api/tickets/{ticket.id}/work-logs", json={"hours": 2, "user_id": otro.id})

    actores = set(seeded.scalars(select(TicketEvent.actor_id).where(TicketEvent.ticket_id == ticket.id)))
    assert actores == {tecnico.id}
    assert seeded.scalar(select(WorkLog.user_id).where(WorkLog.ticket_id == ticket.id)) == tecnico.id
    assert set(seeded.scalars(select(AuditLog.user_id))) == {tecnico.id}


def test_cada_accion_queda_en_la_bitacora_con_su_detalle(as_user, seeded, ticket):
    agencia = as_user("sofia@forjadigital.test")

    agencia.post(f"/api/tickets/{ticket.id}/classify", json={"impact": "alto", "urgency": "alta"})
    agencia.post(f"/api/tickets/{ticket.id}/assign", json={"assignee_id": 5})
    agencia.post(f"/api/tickets/{ticket.id}/transition", json={"new_status": "en_progreso"})

    logs = seeded.scalars(select(AuditLog).order_by(AuditLog.id)).all()
    assert [(log.action, log.entity, log.entity_id) for log in logs] == [
        ("cambiar_prioridad", "ticket", ticket.id),
        ("asignar", "ticket", ticket.id),
        ("cambiar_estado", "ticket", ticket.id),
    ]
    assert logs[0].details == {"de": "P2", "a": "P1", "motivo": None}
    assert logs[2].details == {"de": "abierto", "a": "en_progreso"}


def test_una_transicion_invalida_no_deja_fila_en_la_bitacora(as_user, seeded, ticket):
    response = as_user("sofia@forjadigital.test").post(
        f"/api/tickets/{ticket.id}/transition", json={"new_status": "cerrado"}
    )

    assert response.status_code == 409
    assert seeded.scalar(select(AuditLog)) is None


def test_corregir_la_prioridad_sin_motivo_no_deja_fila_en_la_bitacora(as_user, seeded, ticket):
    response = as_user("sofia@forjadigital.test").post(
        f"/api/tickets/{ticket.id}/classify", json={"impact": "alto", "urgency": "media", "priority": "P4"}
    )

    assert response.status_code == 422
    assert seeded.scalar(select(AuditLog)) is None

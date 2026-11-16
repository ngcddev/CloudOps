# Rechazo automático de las solicitudes cuya versión no pasó la puerta de seguridad (spec 006, T16 · CA-5).
import pytest
from sqlalchemy import select

from app.models import AuditLog, ChangeRequest, Service, Ticket, TicketEvent
from app.services import security_gate as gate

CLIENT_TEXT_SENSITIVE = "Una actualización fue detenida porque contenía información sensible."
CLIENT_TEXT_GENERIC = "Una actualización fue detenida antes de publicarse por controles de seguridad."
CLIENT_TEXT_ORIGIN = "Una actualización fue detenida porque no pasó la verificación de origen."


@pytest.fixture
def ferreteria(seeded) -> Service:
    return seeded.scalar(select(Service).where(Service.namespace == "cliente-ferreteria"))


def _cambio_pendiente(db, service, version="v1.1") -> ChangeRequest:
    ticket = Ticket(service_id=service.id, title="Publicar", description="x", kind="cambio")
    db.add(ticket)
    db.flush()
    change = ChangeRequest(
        ticket_id=ticket.id, service_id=service.id, from_version="v1", to_version=version, status="pendiente"
    )
    db.add(change)
    db.commit()
    return change


def _fallar(db, service, step, version="v1.1"):
    run = gate.open_run(db, service.id, version, None, ["ferreteria"])
    if step != "secretos":
        gate.add_check(db, run, "secretos", "ok", "", None, None)
    gate.add_check(db, run, step, "fallo", "detalle", None, None if step == "secretos" else "ferreteria")
    db.commit()
    return run


def test_al_fallar_los_secretos_la_solicitud_pendiente_queda_rechazada(seeded, ferreteria):
    change = _cambio_pendiente(seeded, ferreteria)

    _fallar(seeded, ferreteria, "secretos")

    seeded.refresh(change)
    assert change.status == "rechazada"
    assert change.rejection_reason == "Detenida por controles de seguridad: secretos en el código"


def test_el_cliente_ve_el_texto_del_glosario_y_no_el_detalle_tecnico(seeded, ferreteria):
    change = _cambio_pendiente(seeded, ferreteria)

    _fallar(seeded, ferreteria, "secretos")

    eventos = seeded.scalars(select(TicketEvent).where(TicketEvent.ticket_id == change.ticket_id)).all()
    visibles = [e.note for e in eventos if not e.internal]
    internos = [e.note for e in eventos if e.internal]
    assert visibles == [CLIENT_TEXT_SENSITIVE]
    assert len(internos) == 1 and "corrida" in internos[0]


@pytest.mark.parametrize(
    ("control", "texto"),
    [
        ("vulnerabilidades", CLIENT_TEXT_GENERIC),
        ("firma", CLIENT_TEXT_ORIGIN),
        ("verificacion", CLIENT_TEXT_ORIGIN),
        ("construccion", CLIENT_TEXT_GENERIC),
    ],
)
def test_cada_control_usa_su_texto_del_glosario(seeded, ferreteria, control, texto):
    change = _cambio_pendiente(seeded, ferreteria)

    _fallar(seeded, ferreteria, control)

    evento = seeded.scalars(
        select(TicketEvent).where(TicketEvent.ticket_id == change.ticket_id, TicketEvent.internal.is_(False))
    ).one()
    assert evento.note == texto


@pytest.mark.parametrize(
    ("estado", "version", "esperado"),
    [
        ("pendiente", "v1.1", "rechazada"),      # pendiente de la versión que falló
        ("pendiente", "v1.2", "pendiente"),      # pendiente de otra versión
        ("en_validacion", "v1.1", "en_validacion"),  # de la misma versión pero ya aprobada
    ],
)
def test_solo_se_rechazan_las_pendientes_de_esa_version(seeded, ferreteria, estado, version, esperado):
    # Un servicio solo puede tener un cambio abierto a la vez (índice único, spec 022 T06): cada caso se prueba por separado
    change = _cambio_pendiente(seeded, ferreteria, version)
    change.status = estado
    seeded.commit()

    _fallar(seeded, ferreteria, "secretos", "v1.1")

    seeded.refresh(change)
    assert change.status == esperado


def test_el_rechazo_automatico_queda_en_la_bitacora_a_nombre_del_sistema(seeded, ferreteria):
    change = _cambio_pendiente(seeded, ferreteria)

    _fallar(seeded, ferreteria, "secretos")

    log = seeded.scalar(select(AuditLog))
    assert (log.action, log.entity_id, log.user_id) == ("rechazar", change.id, None)
    assert log.details["control"] == "secretos"


def test_pedir_un_cambio_hacia_una_version_que_ya_fallo_lo_rechaza_de_una_vez(as_agency, seeded, ferreteria):
    _fallar(seeded, ferreteria, "vulnerabilidades")
    ticket = as_agency.post(
        "/api/tickets",
        json={"service_id": ferreteria.id, "title": "Publicar", "description": "x", "kind": "cambio"},
    ).json()

    response = as_agency.post("/api/change-requests", json={"ticket_id": ticket["id"], "to_version": "v1.1"})

    assert response.status_code == 201
    assert response.json()["status"] == "rechazada"
    assert "vulnerabilidades críticas" in response.json()["rejection_reason"]


def test_si_la_corrida_pasa_la_solicitud_sigue_pendiente(seeded, ferreteria, pass_gate):
    change = _cambio_pendiente(seeded, ferreteria)

    pass_gate("cliente-ferreteria", "v1.1")

    seeded.refresh(change)
    assert change.status == "pendiente"


def test_si_una_corrida_falla_por_el_endpoint_el_cliente_lo_ve_en_su_solicitud(
    anonymous, as_user, seeded, ferreteria
):
    change = _cambio_pendiente(seeded, ferreteria)
    headers = {"Authorization": "Bearer token-del-pipeline-de-pruebas"}
    anonymous.post("/api/pipeline-events", headers=headers, json={"event": "inicio", "site": "ferreteria", "version": "v1.1"})
    anonymous.post(
        "/api/pipeline-events", headers=headers,
        json={"event": "paso", "site": "ferreteria", "version": "v1.1", "step": "secretos", "status": "fallo"},
    )

    detalle = as_user("contacto@eltornillo.test").get(f"/api/tickets/{change.ticket_id}").json()

    textos = [e["note"] for e in detalle["events"] if e["type"] == "cambio"]
    assert CLIENT_TEXT_SENSITIVE in textos
    assert not any("secretos" in (t or "") or "corrida" in (t or "") for t in textos)
    assert [e["to_value"] for e in detalle["events"] if e["type"] == "cambio"][-1] == "Rechazada"

# La consola refresca el estado cada pocos segundos: las consultas no deben crecer con las filas (spec 005).
from sqlalchemy import event, select

from app.models import ChangeRequest, Deployment, Service, Ticket, User
import pytest


@pytest.fixture
def client(seeded, as_user):
    """Estas pruebas operan como Sofía, técnica de la agencia sembrada (spec 007)."""
    return as_user("sofia@forjadigital.test")


def _contar_consultas(session_factory, llamada) -> int:
    engine = session_factory.kw["bind"]
    consultas: list[str] = []

    def registrar(conn, cursor, statement, *args):
        consultas.append(statement)

    event.listen(engine, "before_cursor_execute", registrar)
    try:
        llamada()
    finally:
        event.remove(engine, "before_cursor_execute", registrar)
    return len(consultas)


def _cambio_para(db, service, estado, **extra) -> ChangeRequest:
    ticket = Ticket(service_id=service.id, title="Portada", description="x", kind="cambio")
    db.add(ticket)
    db.flush()
    change = ChangeRequest(
        ticket_id=ticket.id, service_id=service.id, from_version="v1", to_version="v1.1", status=estado, **extra
    )
    db.add(change)
    return change


def test_el_estado_de_los_servicios_no_hace_consultas_por_servicio(client, session_factory, seeded):
    for service in seeded.scalars(select(Service)).all():
        seeded.add(Deployment(service_id=service.id, version="v1.1", author="Sofía", source="cambio"))
        seeded.add(Deployment(service_id=service.id, version="v1.2", author="Sofía", source="cambio"))
        _cambio_para(seeded, service, "pendiente").to_version = "v1.3"
    seeded.commit()

    cantidad = _contar_consultas(session_factory, lambda: client.get("/api/services/status"))

    assert cantidad <= 6  # la sesión + servicios + último despliegue + cambios en curso + puerta de seguridad
    filas = client.get("/api/services/status").json()
    assert {f["open_change_to_version"] for f in filas} == {"v1.3"}
    assert {f["last_author"] for f in filas} == {"Sofía"}


def test_el_ultimo_despliegue_es_el_mas_reciente_de_cada_servicio(client, seeded):
    primero, segundo, _ = seeded.scalars(select(Service).order_by(Service.id)).all()
    seeded.add_all([
        Deployment(service_id=primero.id, version="v1.1", author="Ana", source="cambio"),
        Deployment(service_id=primero.id, version="v1.2", author="Luis", source="cambio"),
        Deployment(service_id=segundo.id, version="v1.1", author="Marta", source="cambio"),
    ])
    seeded.commit()

    filas = {f["service_id"]: f for f in client.get("/api/services/status").json()}

    assert filas[primero.id]["last_author"] == "Luis"
    assert filas[segundo.id]["last_author"] == "Marta"


def test_la_bandeja_de_cambios_no_hace_consultas_por_fila(client, session_factory, seeded):
    tecnico = seeded.scalar(select(User).where(User.role == "agencia"))
    for service in seeded.scalars(select(Service)).all():
        _cambio_para(seeded, service, "en_validacion", requested_by_id=tecnico.id, approved_by_id=tecnico.id)
    seeded.commit()

    cantidad = _contar_consultas(session_factory, lambda: client.get("/api/change-requests"))

    assert cantidad <= 5  # la sesión + la lista + quién pidió + quién aprobó + las solicitudes
    lista = client.get("/api/change-requests").json()
    assert len(lista) == 3 and all(c["approved_by_name"] == tecnico.name for c in lista)


def test_la_bandeja_se_puede_filtrar_por_solicitud(client, seeded):
    service = seeded.scalar(select(Service))
    cambios = [_cambio_para(seeded, service, "rechazada") for _ in range(2)]
    seeded.commit()

    filtrada = client.get("/api/change-requests", params={"ticket_id": cambios[0].ticket_id}).json()

    assert [c["ticket_id"] for c in filtrada] == [cambios[0].ticket_id]
    assert client.get("/api/change-requests", params={"ticket_id": 9999}).json() == []


# --- Auditoría BE-03, BE-04 y BD-03 (spec 022, T19) ---

def test_el_tablero_de_agencia_no_hace_consultas_por_ticket(client, session_factory, seeded):
    """Las horas y los conteos del tablero salen de una suma y de un conteo en la base: más tickets no son más consultas (auditoría BE-03)."""
    def llamar():
        assert client.get("/api/dashboard/agency").status_code == 200

    base = _contar_consultas(session_factory, llamar)
    from app.models import Ticket, WorkLog
    with session_factory() as db:
        servicio = db.scalars(select(Service)).first()
        usuario = db.scalars(select(User)).first()
        for i in range(15):
            ticket = Ticket(service_id=servicio.id, created_by_id=None, title=f"t{i}", description="d", impact="alto", urgency="alta", priority="P2", status="abierto")
            db.add(ticket)
            db.flush()
            db.add(WorkLog(ticket_id=ticket.id, user_id=usuario.id, hours=1, note="x"))
        db.commit()
    con_mas = _contar_consultas(session_factory, llamar)
    assert con_mas <= base + 2, f"{base} consultas con pocos tickets y {con_mas} con 15 tickets más"


def test_los_listados_aceptan_limit_y_offset_y_rechazan_un_limite_enorme(client, seeded):
    assert len(client.get("/api/tickets?limit=1").json()) <= 1
    assert client.get("/api/tickets?limit=0").status_code == 422
    assert client.get("/api/tickets?limit=501").status_code == 422
    assert client.get("/api/tickets?offset=-1").status_code == 422
    for ruta in ("/api/incidents", "/api/change-requests", "/api/reports", "/api/clients"):
        assert client.get(f"{ruta}?limit=1").status_code == 200, ruta
        assert client.get(f"{ruta}?limit=501").status_code == 422, ruta


def test_la_pagina_siguiente_no_repite_filas(client, seeded):
    primeros = client.get("/api/tickets?limit=2&offset=0").json()
    siguientes = client.get("/api/tickets?limit=2&offset=2").json()
    assert not {t["id"] for t in primeros} & {t["id"] for t in siguientes}

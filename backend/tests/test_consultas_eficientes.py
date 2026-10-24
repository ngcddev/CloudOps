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

    assert cantidad <= 4  # servicios + último despliegue + cambios en curso
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

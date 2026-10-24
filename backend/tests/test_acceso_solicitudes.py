# Alcance por cliente en la lectura y creación de solicitudes (spec 007, T09).
from sqlalchemy import select

from app.models import Service, Ticket, User


def _service_de(seeded, host: str) -> int:
    return seeded.scalar(select(Service.id).where(Service.host == host))


def test_sin_sesion_las_solicitudes_responden_401(anonymous, seeded):
    assert anonymous.get("/api/tickets").status_code == 401
    assert anonymous.get("/api/tickets/1").status_code == 401
    assert anonymous.post("/api/tickets", json={"service_id": 1, "title": "x", "description": "y"}).status_code == 401


def test_el_cliente_lista_solo_sus_solicitudes(as_client, seeded):
    tickets = as_client.get("/api/tickets").json()

    assert [t["title"] for t in tickets] == ["Necesito actualizar el horario del menú"]


def test_pedir_viewer_role_o_client_id_ya_no_amplia_lo_que_ve_el_cliente(as_client, seeded):
    otro = seeded.scalar(select(User.client_id).where(User.email == "contacto@eltornillo.test"))

    response = as_client.get("/api/tickets", params={"viewer_role": "agencia", "client_id": otro})

    assert [t["title"] for t in response.json()] == ["Necesito actualizar el horario del menú"]


def test_la_agencia_ve_todas_y_puede_filtrar_por_cliente(as_agency, seeded):
    cliente = seeded.scalar(select(User.client_id).where(User.email == "contacto@eltornillo.test"))

    assert len(as_agency.get("/api/tickets").json()) == 3
    filtradas = as_agency.get("/api/tickets", params={"client_id": cliente}).json()
    assert [t["title"] for t in filtradas] == ["Los productos destacados no cargan"]


def test_el_cliente_ve_el_detalle_de_lo_suyo_y_lo_de_otro_responde_404(as_client, seeded):
    propio = seeded.scalar(select(Ticket.id).where(Ticket.title == "Necesito actualizar el horario del menú"))
    ajeno = seeded.scalar(select(Ticket.id).where(Ticket.title == "Los productos destacados no cargan"))

    assert as_client.get(f"/api/tickets/{propio}").status_code == 200
    assert as_client.get(f"/api/tickets/{ajeno}").status_code == 404


def test_el_cliente_crea_una_solicitud_a_su_nombre_aunque_el_cuerpo_diga_otro(as_client, seeded):
    marta = seeded.scalar(select(User).where(User.email == "contacto@lasazon.test"))
    otro = seeded.scalar(select(User).where(User.email == "contacto@eltornillo.test"))
    service = _service_de(seeded, "restaurante.hub.local")

    response = as_client.post(
        "/api/tickets",
        json={"service_id": service, "title": "Foto nueva", "description": "Cambiar la foto", "created_by_id": otro.id},
    )

    assert response.status_code == 201
    assert response.json()["created_by_id"] == marta.id


def test_el_cliente_no_puede_crear_sobre_el_servicio_de_otro(as_client, seeded):
    ajeno = _service_de(seeded, "ferreteria.hub.local")

    response = as_client.post("/api/tickets", json={"service_id": ajeno, "title": "Intruso", "description": "x"})

    assert response.status_code == 404
    assert seeded.scalar(select(Ticket.id).where(Ticket.title == "Intruso")) is None


def test_la_agencia_crea_una_solicitud_a_su_nombre(as_agency, seeded):
    tecnico = seeded.scalar(select(User).where(User.email == "tecnico.pruebas@forjadigital.test"))
    # as_agency crea su usuario al construirse la fixture, antes de la semilla
    response = as_agency.post(
        "/api/tickets",
        json={"service_id": _service_de(seeded, "ferreteria.hub.local"), "title": "Interna", "description": "x"},
    )

    assert response.status_code == 201
    assert response.json()["created_by_id"] == tecnico.id

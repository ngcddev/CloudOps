# Permisos y alcance por cliente en catálogo y clientes, y su registro en la bitácora (spec 007, T08).
from sqlalchemy import select

from app.models import AuditLog, Client


def _id_de(seeded, name: str) -> int:
    return seeded.scalar(select(Client.id).where(Client.name == name))


def test_sin_sesion_ninguna_ruta_de_clientes_ni_catalogo_responde_datos(anonymous, seeded):
    assert anonymous.get("/api/clients").status_code == 401
    assert anonymous.get("/api/clients/1").status_code == 401
    assert anonymous.get("/api/plans").status_code == 401
    assert anonymous.get("/api/sla-policies").status_code == 401
    assert anonymous.post("/api/clients", json={"name": "X"}).status_code == 401


def test_el_cliente_ve_solo_el_suyo_en_la_lista(as_client, seeded):
    clients = as_client.get("/api/clients").json()

    assert [c["name"] for c in clients] == ["Restaurante La Sazón"]


def test_el_cliente_ve_su_detalle_y_el_de_otro_responde_404(as_client, seeded):
    own = _id_de(seeded, "Restaurante La Sazón")
    other = _id_de(seeded, "Ferretería El Tornillo")

    assert as_client.get(f"/api/clients/{own}").status_code == 200
    assert as_client.get(f"/api/clients/{other}").status_code == 404


def test_la_agencia_ve_todos_los_clientes(as_agency, seeded):
    assert len(as_agency.get("/api/clients").json()) == 3


def test_el_cliente_ve_el_catalogo_de_planes(as_client, seeded):
    assert as_client.get("/api/plans").status_code == 200
    assert as_client.get("/api/sla-policies").status_code == 200


def test_el_cliente_no_puede_crear_ni_editar_clientes_proyectos_ni_servicios(as_client, seeded):
    own = _id_de(seeded, "Restaurante La Sazón")

    assert as_client.post("/api/clients", json={"name": "Nuevo"}).status_code == 403
    assert as_client.patch(f"/api/clients/{own}", json={"phone": "300"}).status_code == 403
    assert as_client.post(f"/api/clients/{own}/projects", json={"name": "P"}).status_code == 403
    assert as_client.post("/api/projects/1/services", json={}).status_code in (403, 422)
    assert seeded.scalar(select(AuditLog)) is None


def test_crear_un_cliente_queda_en_la_bitacora(as_agency, seeded):
    created = as_agency.post("/api/clients", json={"name": "Panadería Luz"}).json()

    log = seeded.scalar(select(AuditLog))
    assert (log.action, log.entity, log.entity_id) == ("crear", "client", created["id"])
    assert log.user_id is not None
    assert log.details == {"name": "Panadería Luz"}


def test_editar_un_cliente_queda_en_la_bitacora_con_los_campos_cambiados(as_agency, seeded):
    own = _id_de(seeded, "Restaurante La Sazón")

    as_agency.patch(f"/api/clients/{own}", json={"phone": "3001112233", "contact_name": "Marta"})

    log = seeded.scalar(select(AuditLog))
    assert (log.action, log.entity, log.entity_id) == ("editar", "client", own)
    assert log.details == {"campos": ["contact_name", "phone"]}


def test_un_cliente_invalido_no_deja_fila_en_la_bitacora(as_agency, seeded):
    assert as_agency.post("/api/clients", json={}).status_code == 422
    assert as_agency.patch("/api/clients/9999", json={"phone": "1"}).status_code == 404

    assert seeded.scalar(select(AuditLog)) is None

# Índices de las claves foráneas y restricciones únicas (spec 022, T06; auditoría BD-01 y BD-02): existen, y dos peticiones que chocan
# ya no crean un cambio abierto ni un control duplicado: la base deja pasar a una y la API responde 409.
import importlib.util
from pathlib import Path

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from app.models import ChangeRequest, SecurityCheck, Service
from app.models import change_request as modelo_cambios
from app.routers import change_requests as router_cambios
from app.services import deploy_watch
from app.services import security_gate as gate
from tests.test_change_requests import _create, _ticket

MIGRACION = Path(__file__).resolve().parents[1] / "alembic" / "versions" / "0015_indices_y_unicos.py"


@pytest.fixture
def client(seeded, as_user):
    """Como Sofía, técnica de la agencia sembrada."""
    return as_user("sofia@forjadigital.test")


@pytest.fixture
def ferreteria(seeded):
    return seeded.scalar(select(Service).where(Service.namespace == "cliente-ferreteria"))


def _cambio(service, estado: str, ticket_id: int = 1, a: str = "v1.1") -> ChangeRequest:
    return ChangeRequest(ticket_id=ticket_id, service_id=service.id, from_version="v1", to_version=a, status=estado)


def test_los_indices_de_las_claves_foraneas_existen(db):
    nombres = {fila[0] for fila in db.execute(text("SELECT name FROM sqlite_master WHERE type = 'index'"))}
    assert {
        "ix_tickets_service_id", "ix_tickets_created_at", "ix_ticket_events_ticket_id", "ix_work_logs_ticket_id", "ix_work_logs_user_id",
        "ix_change_requests_service_status", "ix_change_requests_ticket_id", "ix_deployments_service_id_id", "ix_services_project_id",
        "ix_projects_client_id", "ix_users_client_id", "uq_change_requests_open_per_service", "uq_security_checks_run_step_image",
    } <= nombres


def test_los_estados_abiertos_son_los_mismos_en_el_modelo_el_router_el_vigilante_y_la_migracion():
    assert modelo_cambios.OPEN_STATUSES == router_cambios.OPEN_STATUSES == deploy_watch.OPEN_STATUSES
    especificacion = importlib.util.spec_from_file_location("migracion_0015", MIGRACION)
    migracion = importlib.util.module_from_spec(especificacion)
    especificacion.loader.exec_module(migracion)
    assert migracion.ABIERTOS == modelo_cambios.OPEN_PREDICATE


@pytest.mark.parametrize("segundo", ["pendiente", "aprobada", "en_validacion"])
def test_un_servicio_no_admite_dos_cambios_abiertos(seeded, ferreteria, segundo):
    seeded.add(_cambio(ferreteria, "pendiente"))
    seeded.commit()
    seeded.add(_cambio(ferreteria, segundo, ticket_id=2, a="v1.2"))
    with pytest.raises(IntegrityError):
        seeded.commit()
    seeded.rollback()


def test_los_cambios_cerrados_no_estorban_y_otro_servicio_tiene_el_suyo(seeded, ferreteria):
    otro = seeded.scalar(select(Service).where(Service.namespace == "cliente-restaurante"))
    abierto = _cambio(ferreteria, "en_validacion")
    seeded.add_all([
        abierto,
        _cambio(ferreteria, "desplegada", 2, "v1.2"),
        _cambio(ferreteria, "fallida", 3, "v1.3"),
        _cambio(ferreteria, "rechazada", 4, "v1.4"),
        _cambio(otro, "pendiente", 5),
    ])
    seeded.commit()
    # al cerrarse el abierto, el servicio puede tener otro
    abierto.status = "desplegada"
    seeded.add(_cambio(ferreteria, "pendiente", 6, "v1.5"))
    seeded.commit()


def test_dos_peticiones_a_la_vez_dejan_pasar_solo_una(client, seeded, ferreteria, monkeypatch):
    primero, segundo = _ticket(client, ferreteria.id), _ticket(client, ferreteria.id)
    assert _create(client, primero).status_code == 201
    # La comprobación del router no ve el cambio abierto (lo que pasa en una carrera): el índice único de la base lo para
    monkeypatch.setattr(router_cambios, "OPEN_STATUSES", ("ninguno",))

    respuesta = _create(client, segundo, "v1.2")

    assert respuesta.status_code == 409 and "en curso" in respuesta.json()["detail"]
    assert len(seeded.scalars(select(ChangeRequest).where(ChangeRequest.service_id == ferreteria.id)).all()) == 1


def test_un_control_repetido_se_rechaza(seeded, ferreteria):
    run = gate.open_run(seeded, ferreteria.id, "v9", None, ["ferreteria"])
    gate.add_check(seeded, run, "secretos", "ok", "Sin secretos", None, None)

    with pytest.raises(gate.GateError, match="ya se registró"):
        gate.add_check(seeded, run, "secretos", "ok", "Sin secretos", None, None)


def test_la_base_rechaza_el_control_repetido_aunque_el_codigo_no_lo_vea(seeded, session_factory, ferreteria):
    run = gate.open_run(seeded, ferreteria.id, "v9", None, ["ferreteria"])
    seeded.commit()
    assert list(run.checks) == []   # la colección ya cargada: la comprobación en memoria no verá lo que escriba otra sesión
    with session_factory() as otra:
        otra.add(SecurityCheck(run_id=run.id, step="secretos", image=None, status="ok", summary=""))
        otra.commit()

    with pytest.raises(gate.GateError, match="ya se registró"):
        gate.add_check(seeded, run, "secretos", "ok", "Sin secretos", None, None)

    # el punto de guardado deja la sesión usable
    gate.add_check(seeded, run, "sbom", "ok", "SBOM", None, "ferreteria")


def test_el_mismo_paso_con_otra_imagen_es_otro_control(seeded, ferreteria):
    run = gate.open_run(seeded, ferreteria.id, "v9", None, ["ferreteria", "ferreteria-api"])
    gate.add_check(seeded, run, "sbom", "ok", "", None, "ferreteria")
    gate.add_check(seeded, run, "sbom", "ok", "", None, "ferreteria-api")

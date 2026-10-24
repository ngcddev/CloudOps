# Estado de la puerta de seguridad de una versión (spec 006, T14).
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.models import SecurityRun, Service
from app.services.security_gate import EN_CURSO, FALLO, OK, SIN_CORRIDA, gate_status


@pytest.fixture
def ferreteria(seeded) -> Service:
    return seeded.scalar(select(Service).where(Service.namespace == "cliente-ferreteria"))


def _run(db, service, version, status, failed_step=None, started=None) -> SecurityRun:
    run = SecurityRun(
        service_id=service.id, version=version, images=[service.namespace], status=status,
        failed_step=failed_step, started_at=started or datetime.now(timezone.utc),
    )
    db.add(run)
    db.commit()
    return run


def test_sin_corrida_si_la_version_nunca_paso_por_la_puerta(seeded, ferreteria):
    gate = gate_status(seeded, ferreteria.id, "v1.1")

    assert gate.status == SIN_CORRIDA
    assert gate.run is None and gate.failed_step is None


@pytest.mark.parametrize("status", [EN_CURSO, OK, FALLO])
def test_devuelve_el_estado_de_la_corrida(seeded, ferreteria, status):
    _run(seeded, ferreteria, "v1.1", status, failed_step="secretos" if status == FALLO else None)

    gate = gate_status(seeded, ferreteria.id, "v1.1")

    assert gate.status == status
    assert gate.failed_step == ("secretos" if status == FALLO else None)


def test_vale_la_ultima_corrida_de_la_version(seeded, ferreteria):
    hoy = datetime.now(timezone.utc)
    _run(seeded, ferreteria, "v1.1", FALLO, "vulnerabilidades", hoy - timedelta(hours=2))
    ultima = _run(seeded, ferreteria, "v1.1", OK, started=hoy - timedelta(hours=1))

    assert gate_status(seeded, ferreteria.id, "v1.1").run.id == ultima.id
    assert gate_status(seeded, ferreteria.id, "v1.1").status == OK


def test_cada_version_y_cada_servicio_tiene_su_propia_puerta(seeded, ferreteria):
    restaurante = seeded.scalar(select(Service).where(Service.namespace == "cliente-restaurante"))
    _run(seeded, ferreteria, "v1.1", OK)

    assert gate_status(seeded, ferreteria.id, "v1.2").status == SIN_CORRIDA
    assert gate_status(seeded, restaurante.id, "v1.1").status == SIN_CORRIDA

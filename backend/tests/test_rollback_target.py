# Pruebas de a qué versión se vuelve en un rollback: las tres reglas de la decisión 1 (spec 009, T02).
import pytest
from sqlalchemy import select

from app.models import ChangeRequest, Deployment, Service, Ticket
from app.services.rollback import NO_TARGET, rollback_target, running_version


@pytest.fixture
def sazon(seeded) -> Service:
    return seeded.scalar(select(Service).where(Service.namespace == "cliente-restaurante"))


def _deploy(db, service, version):
    db.add(Deployment(service_id=service.id, version=version, author="Sofía", source="cambio"))
    db.flush()


def test_la_v2_sin_estabilizar_vuelve_a_la_estable(seeded, sazon):
    sazon.current_version, sazon.stable_version = "v2", "v1"

    assert rollback_target(seeded, sazon) == "v1"


def test_un_cambio_en_validacion_ya_esta_en_git_aunque_el_hub_aun_diga_v1(seeded, sazon):
    ticket = Ticket(service_id=sazon.id, title="v2", description="v2", kind="cambio")
    seeded.add(ticket)
    seeded.flush()
    seeded.add(
        ChangeRequest(
            ticket_id=ticket.id, service_id=sazon.id, from_version="v1", to_version="v2",
            status="en_validacion", gitops_commit_sha="a" * 40,
        )
    )
    seeded.flush()

    assert running_version(seeded, sazon) == "v2"
    assert rollback_target(seeded, sazon) == "v1"


def test_una_version_sana_que_se_rompio_vuelve_a_la_anterior_del_historial(seeded, sazon):
    for version in ("v1", "v1.1"):
        _deploy(seeded, sazon, version)
    sazon.current_version = sazon.stable_version = "v1.1"

    assert rollback_target(seeded, sazon) == "v1"


def test_la_anterior_es_la_ultima_distinta_a_la_actual(seeded, sazon):
    # v1 → v1.1 → v1.1 repetida por una reconciliación: la anterior sigue siendo v1
    for version in ("v1", "v1.1", "v1.1"):
        _deploy(seeded, sazon, version)
    sazon.current_version = sazon.stable_version = "v1.1"

    assert rollback_target(seeded, sazon) == "v1"


def test_sin_version_anterior_no_hay_a_donde_volver(seeded, sazon):
    assert (sazon.current_version, sazon.stable_version) == ("v1", "v1")

    assert rollback_target(seeded, sazon) is None
    assert "versión anterior" in NO_TARGET

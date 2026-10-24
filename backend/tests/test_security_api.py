# Consultas de la puerta de seguridad: corridas, controles de un cambio y reportes (spec 006, T17 · CA-4).
import json

import pytest
from sqlalchemy import select

from app.models import ChangeRequest, SecurityCheck, Service, Ticket
from app.services import security_gate as gate

SBOM = {"spdxVersion": "SPDX-2.3", "packages": [{"name": "nginx"}]}


@pytest.fixture
def ferreteria(seeded) -> Service:
    return seeded.scalar(select(Service).where(Service.namespace == "cliente-ferreteria"))


def _corrida_ok(db, service, version="v1.1", sbom=SBOM):
    run = gate.open_run(db, service.id, version, "a" * 40, ["ferreteria"])
    gate.add_check(db, run, "secretos", "ok", "Sin secretos", {"findings": []}, None)
    for step in gate.IMAGE_STEPS:
        gate.add_check(db, run, step, "ok", f"{step} ok", sbom if step == "sbom" else None, "ferreteria")
    gate.close_run(db, run, "ok", image_digests={"ferreteria": "sha256:" + "c" * 64})
    db.commit()
    return run


def _cambio(db, service, version="v1.1") -> ChangeRequest:
    ticket = Ticket(service_id=service.id, title="Publicar", description="x", kind="cambio")
    db.add(ticket)
    db.flush()
    change = ChangeRequest(
        ticket_id=ticket.id, service_id=service.id, from_version="v1", to_version=version, status="pendiente"
    )
    db.add(change)
    db.commit()
    return change


def test_las_corridas_del_servicio_vienen_con_sus_controles_y_la_mas_reciente_primero(as_agency, seeded, ferreteria):
    primera = _corrida_ok(seeded, ferreteria, "v1.1")
    segunda = _corrida_ok(seeded, ferreteria, "v1.2")

    body = as_agency.get(f"/api/services/{ferreteria.id}/security-runs").json()

    assert [r["id"] for r in body] == [segunda.id, primera.id]
    assert [c["step"] for c in body[0]["checks"]] == ["secretos", *gate.IMAGE_STEPS]
    assert body[0]["image_digests"] == {"ferreteria": "sha256:" + "c" * 64}


def test_indica_que_controles_tienen_reporte_descargable(as_agency, seeded, ferreteria):
    _corrida_ok(seeded, ferreteria)

    checks = as_agency.get(f"/api/services/{ferreteria.id}/security-runs").json()[0]["checks"]

    assert {c["step"]: c["has_report"] for c in checks} == {
        "secretos": True, "construccion": False, "vulnerabilidades": False,
        "sbom": True, "firma": False, "verificacion": False,
    }


def test_un_servicio_sin_corridas_devuelve_lista_vacia_y_uno_inexistente_404(as_agency, ferreteria):
    assert as_agency.get(f"/api/services/{ferreteria.id}/security-runs").json() == []
    assert as_agency.get("/api/services/9999/security-runs").status_code == 404


def test_los_controles_de_un_cambio_son_los_de_la_corrida_de_su_version_destino(as_agency, seeded, ferreteria):
    _corrida_ok(seeded, ferreteria, "v1.1")
    cambio = _cambio(seeded, ferreteria, "v1.1")

    body = as_agency.get(f"/api/change-requests/{cambio.id}/checks").json()

    assert (body["version"], body["status"], body["failed_step"]) == ("v1.1", "ok", None)
    assert len(body["run"]["checks"]) == 6


def test_un_cambio_sin_corrida_responde_sin_corrida(as_agency, seeded, ferreteria):
    cambio = _cambio(seeded, ferreteria, "v9")

    body = as_agency.get(f"/api/change-requests/{cambio.id}/checks").json()

    assert (body["status"], body["run"]) == ("sin_corrida", None)
    assert as_agency.get("/api/change-requests/9999/checks").status_code == 404


def test_el_reporte_del_sbom_se_descarga_como_json(as_agency, seeded, ferreteria):
    _corrida_ok(seeded, ferreteria)
    sbom = seeded.scalar(select(SecurityCheck).where(SecurityCheck.step == "sbom"))

    response = as_agency.get(f"/api/security-checks/{sbom.id}/report")

    assert response.status_code == 200
    assert json.loads(response.text) == SBOM
    assert "attachment" in response.headers["content-disposition"]
    assert "sbom-ferreteria" in response.headers["content-disposition"]


def test_un_control_sin_reporte_o_inexistente_responde_404(as_agency, seeded, ferreteria):
    _corrida_ok(seeded, ferreteria)
    firma = seeded.scalar(select(SecurityCheck).where(SecurityCheck.step == "firma"))

    assert as_agency.get(f"/api/security-checks/{firma.id}/report").status_code == 404
    assert as_agency.get("/api/security-checks/9999/report").status_code == 404


def test_el_cliente_no_ve_nada_de_la_puerta(as_client, anonymous, seeded, ferreteria):
    run = _corrida_ok(seeded, ferreteria)
    cambio = _cambio(seeded, ferreteria)
    check_id = run.checks[0].id

    for url in (
        f"/api/services/{ferreteria.id}/security-runs",
        f"/api/change-requests/{cambio.id}/checks",
        f"/api/security-checks/{check_id}/report",
    ):
        assert as_client.get(url).status_code == 403
        assert anonymous.get(url).status_code == 401

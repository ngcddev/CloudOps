# Pruebas de la API de los reportes: generar, listar y ver con alcance por rol (spec 013, T04-T06).
import pytest
from sqlalchemy import select

from app.models import AuditLog, Report
from tests.report_support import busy_october


@pytest.fixture
def client(as_agency):
    return as_agency


# ---------- T04: generar ----------


def test_genera_un_ejecutivo_y_guarda_sus_numeros(client, seeded):
    busy_october(seeded)

    response = client.post("/api/reports", json={"kind": "ejecutivo", "client_id": 1, "month": "2026-10"})

    assert response.status_code == 201, response.text
    report = response.json()
    assert (report["kind"], report["client_id"], report["client_name"]) == ("ejecutivo", 1, "Restaurante La Sazón")
    assert report["data"]["incidents"]["count"] == 1
    assert report["generated_by_name"] == "tecnico.pruebas"
    assert seeded.scalar(select(Report)).data["month_label"] == "octubre de 2026"


def test_genera_un_operativo_sin_cliente(client, seeded):
    response = client.post("/api/reports", json={"kind": "operativo", "client_id": 2, "month": "2026-10"})

    assert response.status_code == 201
    assert response.json()["client_id"] is None
    assert len(response.json()["data"]["clients"]) == 3


def test_el_ejecutivo_necesita_cliente(client, seeded):
    response = client.post("/api/reports", json={"kind": "ejecutivo", "month": "2026-10"})

    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "El reporte ejecutivo necesita un cliente."


@pytest.mark.parametrize("month", ["2026-13", "oct-2026", "2026-1"])
def test_mes_con_otro_formato(client, seeded, month):
    response = client.post("/api/reports", json={"kind": "operativo", "month": month})

    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "El campo «mes» no tiene el formato esperado."


def test_cliente_que_no_existe(client, seeded):
    response = client.post("/api/reports", json={"kind": "ejecutivo", "client_id": 99, "month": "2026-10"})
    assert response.status_code == 404


def test_el_cliente_no_genera(as_client, seeded):
    response = as_client.post("/api/reports", json={"kind": "ejecutivo", "client_id": 1, "month": "2026-10"})
    assert response.status_code == 403


def test_generar_queda_en_la_bitacora(client, seeded):
    report = client.post("/api/reports", json={"kind": "ejecutivo", "client_id": 1, "month": "2026-10"}).json()

    log = seeded.scalar(select(AuditLog).where(AuditLog.entity == "report"))
    assert (log.action, log.entity_id) == ("generar", report["id"])
    assert log.details == {"tipo": "ejecutivo", "cliente": 1, "mes": "2026-10"}

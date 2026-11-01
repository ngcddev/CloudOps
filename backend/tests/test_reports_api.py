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


# ---------- T05: listar y ver con alcance por rol ----------


@pytest.fixture
def tres_reportes(client, seeded):
    """Un operativo, un ejecutivo de La Sazón (cliente 1) y uno de El Tornillo (cliente 2)."""
    ids = {}
    for name, body in (
        ("operativo", {"kind": "operativo", "month": "2026-10"}),
        ("sazon", {"kind": "ejecutivo", "client_id": 1, "month": "2026-10"}),
        ("tornillo", {"kind": "ejecutivo", "client_id": 2, "month": "2026-09"}),
    ):
        ids[name] = client.post("/api/reports", json=body).json()["id"]
    return ids


def test_la_agencia_ve_todos_sin_los_datos(client, tres_reportes):
    rows = client.get("/api/reports").json()

    assert [row["id"] for row in rows] == [tres_reportes[k] for k in ("tornillo", "sazon", "operativo")]
    assert "data" not in rows[0]


def test_la_agencia_filtra_por_tipo_cliente_y_mes(client, tres_reportes):
    assert [r["id"] for r in client.get("/api/reports", params={"kind": "operativo"}).json()] == [
        tres_reportes["operativo"]
    ]
    assert [r["id"] for r in client.get("/api/reports", params={"client_id": 2}).json()] == [tres_reportes["tornillo"]]
    assert [r["id"] for r in client.get("/api/reports", params={"month": "2026-09"}).json()] == [
        tres_reportes["tornillo"]
    ]


def test_el_cliente_ve_solo_sus_ejecutivos(as_client, tres_reportes):
    rows = as_client.get("/api/reports").json()

    assert [row["id"] for row in rows] == [tres_reportes["sazon"]]
    # Ni pidiendo el filtro de otro cliente o del operativo ve más
    assert as_client.get("/api/reports", params={"client_id": 2}).json() == []
    assert as_client.get("/api/reports", params={"kind": "operativo"}).json() == []


def test_el_cliente_abre_el_suyo(as_client, tres_reportes):
    response = as_client.get(f"/api/reports/{tres_reportes['sazon']}")

    assert response.status_code == 200
    assert response.json()["data"]["client_name"] == "Restaurante La Sazón"


def test_el_operativo_y_el_de_otro_cliente_no_existen_para_el_cliente(as_client, tres_reportes):
    assert as_client.get(f"/api/reports/{tres_reportes['operativo']}").status_code == 404
    assert as_client.get(f"/api/reports/{tres_reportes['tornillo']}").status_code == 404


def test_sin_sesion_no_hay_reportes(anonymous, tres_reportes):
    assert anonymous.get("/api/reports").status_code == 401
    assert anonymous.get(f"/api/reports/{tres_reportes['sazon']}").status_code == 401


def test_reporte_que_no_existe(client, seeded):
    assert client.get("/api/reports/999").status_code == 404

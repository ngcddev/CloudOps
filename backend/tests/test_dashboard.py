# Pruebas del panel de la agencia: KPI por cliente, totales y carga por técnico (spec 010, T07).
import pytest


@pytest.fixture
def client(as_agency):
    """El panel es de la agencia; las pruebas de acceso lo hacen con un usuario cliente."""
    return as_agency


def test_agency_dashboard_devuelve_los_clientes_con_sus_kpi(client, seeded):
    response = client.get("/api/dashboard/agency", params={"month": "2026-10"})

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["month"] == "2026-10"
    assert len(data["clients"]) == 3
    primera = data["clients"][0]
    assert primera["client_id"] == 1
    assert primera["client_name"]
    for campo in (
        "service_name",
        "service_status",
        "sla_compliance",
        "mttr",
        "open_tickets",
        "closed_tickets",
        "hours",
        "cost",
    ):
        assert campo in primera, f"Falta el campo {campo} en el KPI del cliente"
    assert isinstance(data["technicians"], list) and data["technicians"]


def test_agency_dashboard_de_un_cliente_en_otro_mes_sigue_respondiendo(client, seeded):
    assert client.get("/api/dashboard/agency").status_code == 200


def test_agency_dashboard_cliente_no_ve_el_panel(as_client, seeded):
    response = as_client.get("/api/dashboard/agency")

    assert response.status_code == 403

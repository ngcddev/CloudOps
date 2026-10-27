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


def test_agency_dashboard_cliente_no_ve_el_panel(as_client, seeded):
    response = as_client.get("/api/dashboard/agency")

    assert response.status_code == 403


def test_agency_dashboard_de_un_cliente_devuelve_solo_su_kpi_sin_costo(client, seeded):
    response = client.get("/api/dashboard/client/1", params={"month": "2026-10"})

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["client_id"] == 1
    assert "cost" not in data
    assert "hours" not in data
    assert "technicians" not in data
    assert "availability" in data and "cumple_objetivo" in data


def test_agency_dashboard_con_prometheus_caido_responde_200_con_null_de_disponibilidad(client, seeded):
    response = client.get("/api/dashboard/agency", params={"month": "2026-11"})

    assert response.status_code == 200, response.text
    data = response.json()
    for item in data["clients"]:
        assert item["availability"] is None
        assert item["cumple_objetivo"] is None


def test_series_del_cliente_devuelve_disponibilidad_y_latencia(client, seeded, monkeypatch):
    from datetime import datetime, timezone

    from app.services import kpi

    def query_range(promql, start, end, step_seconds=300, transport=None):
        assert step_seconds == 300
        valor = 0.98 if promql.startswith("probe_success") else 0.2
        return [(datetime(2026, 10, 1, 5, 0, tzinfo=timezone.utc), valor)]

    monkeypatch.setattr(kpi.prometheus, "query_range", query_range)
    response = client.get("/api/dashboard/client/1/series", params={"month": "2026-10"})

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["client_id"] == 1
    assert data["month"] == "2026-10"
    assert data["slo_availability"] is not None
    assert data["availability"][0]["value"] == 98.0
    assert data["latency_p95"][0]["value"] == 0.2


def test_series_con_prometheus_caido_devuelve_listas_vacias(client, seeded):
    response = client.get("/api/dashboard/client/1/series", params={"month": "2026-12"})

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["availability"] == []
    assert data["latency_p95"] == []


def test_series_de_un_cliente_inexistente_da_404(client, seeded):
    assert client.get("/api/dashboard/client/99/series").status_code == 404


def test_series_son_solo_de_la_agencia(as_client, seeded):
    assert as_client.get("/api/dashboard/client/1/series").status_code == 403


def test_agency_dashboard_de_otro_cliente_responde_404_para_un_cliente_que_pide(as_client, seeded):
    response = as_client.get("/api/dashboard/client/2", params={"month": "2026-10"})

    assert response.status_code == 404


def test_cliente_ve_solo_el_kpi_de_su_propio_cliente(as_client, seeded):
    response = as_client.get("/api/dashboard/client/1", params={"month": "2026-10"})

    assert response.status_code == 200, response.text
    assert response.json()["client_id"] == 1

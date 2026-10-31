# Pruebas de los datos de los reportes operativo y ejecutivo (spec 013, T02-T03).
import pytest

from app.services.reports import operational, previous_month
from tests.report_support import busy_october


@pytest.fixture
def client(as_agency):
    return as_agency


@pytest.mark.parametrize("month, before", [("2026-10", "2026-09"), ("2026-01", "2025-12")])
def test_mes_anterior(month, before):
    assert previous_month(month) == before


# ---------- T02: operativo ----------


def test_cada_cliente_trae_lo_mismo_que_el_dashboard(client, seeded):
    busy_october(seeded)

    report = operational(seeded, "2026-10")

    for month, key in (("2026-10", "current"), ("2026-09", "previous")):
        dashboard = client.get("/api/dashboard/agency", params={"month": month}).json()["clients"]
        assert [row[key] for row in report["clients"]] == dashboard


def test_el_total_suma_y_promedia(seeded):
    busy_october(seeded)

    report = operational(seeded, "2026-10")
    totals = report["totals"]
    for key in ("current", "previous"):
        rows = [row[key] for row in report["clients"]]
        for field in ("hours", "cost", "open_tickets", "closed_tickets"):
            assert totals[key][field] == pytest.approx(sum(row[field] for row in rows))
    # Las horas registradas en las pruebas: 3 + 2 en octubre y 1,5 en septiembre (la semilla no trae horas)
    assert (totals["current"]["hours"], totals["previous"]["hours"]) == (5.0, 1.5)
    assert totals["current"]["cost"] == 5.0 * 25000
    # Solo La Sazón tuvo falla: el MTTR de la agencia es el suyo (7,5 min), no un promedio con ceros
    assert totals["current"]["mttr"] == 7.5
    assert totals["previous"]["mttr"] is None


def test_trae_la_carga_de_los_tecnicos_y_el_costo_por_hora(seeded):
    report = operational(seeded, "2026-10")

    assert report["kind"] == "operativo" and report["previous_month"] == "2026-09"
    assert report["hourly_cost"] == 25000 and report["currency"] == "COP"
    assert report["technicians"] and {"name", "hours", "load"} <= set(report["technicians"][0])

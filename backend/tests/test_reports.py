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


# ---------- T03: ejecutivo ----------


def _with_message(db, incident, status: str = "aprobado", text: str = "Su sitio tuvo una falla y ya funciona.") -> None:
    from app.models import AiDraft

    db.add(AiDraft(
        incident_id=incident.id, kind="mensaje_cliente", status=status, model="manual",
        generated_text=text, final_text=text if status == "aprobado" else None,
    ))
    db.commit()


def _publish(db, namespace: str, source: str, day: int) -> None:
    from datetime import datetime, timezone

    from sqlalchemy import select

    from app.models import Deployment, Service

    service = db.scalar(select(Service).where(Service.namespace == namespace))
    db.add(Deployment(
        service_id=service.id, version="v1.1", author="Técnico", source=source,
        created_at=datetime(2026, 10, day, 16, tzinfo=timezone.utc),
    ))
    db.commit()


def test_la_falla_trae_el_mensaje_aprobado(seeded):
    from app.services.reports import executive

    _with_message(seeded, busy_october(seeded))

    report = executive(seeded, 1, "2026-10")
    assert report["incidents"]["items"] == [
        {"date": "24/10/2026", "time": "14:00", "text": "Su sitio tuvo una falla y ya funciona."}
    ]
    assert report["incidents"]["text"] == "Este mes tuvimos 1 falla."
    assert report["incidents"]["recovery_text"] == "Tiempo que tardamos en recuperar su sitio. 8 min."


def test_sin_mensaje_aprobado_usa_el_glosario_y_nunca_el_borrador(seeded):
    from app.services.reports import executive

    _with_message(seeded, busy_october(seeded), status="borrador_ia", text="BORRADOR que no debe salir")

    report = executive(seeded, 1, "2026-10")
    assert [item["text"] for item in report["incidents"]["items"]] == [
        "Se detectó una falla temporal y se activó el proceso de recuperación."
    ]
    assert "BORRADOR" not in repr(report)


def test_cuenta_cambios_publicados_sin_las_recuperaciones(seeded):
    from app.services.reports import executive

    _publish(seeded, "cliente-restaurante", "cambio", 12)
    _publish(seeded, "cliente-restaurante", "rollback", 24)
    _publish(seeded, "cliente-ferreteria", "cambio", 13)

    changes = executive(seeded, 1, "2026-10")["changes"]
    assert changes["count"] == 1
    assert changes["text"] == "Este mes publicamos 1 actualización de su sitio."
    assert changes["items"] == [{"date": "12/10/2026", "text": "Publicamos la actualización que usted solicitó."}]


def test_un_mes_sin_nada_lo_dice_con_el_glosario(seeded):
    from app.services.reports import executive

    report = executive(seeded, 1, "2026-03")
    assert report["month_label"] == "marzo de 2026"
    assert report["availability"]["text"] == "Todavía no tenemos datos de su sitio este mes."
    assert report["incidents"]["text"] == "No tuvimos fallas que afectaran su sitio este mes."
    assert report["incidents"]["recovery_text"] is None
    assert report["changes"]["text"] == "Este mes no hubo actualizaciones de su sitio."
    assert report["tickets"]["text"] == "Este mes no abrió solicitudes."


def test_la_disponibilidad_se_compara_con_el_objetivo(seeded, monkeypatch):
    from app.services import kpi
    from app.services.reports import executive

    monkeypatch.setattr(kpi, "disponibilidad_del_mes", lambda db, client_id, month, transport=None: 99.95)

    availability = executive(seeded, 1, "2026-10")["availability"]
    assert availability["objective"] == 99.9 and availability["meets_objective"] is True
    assert availability["text"] == "Su sitio se mantuvo disponible dentro del objetivo acordado."


def test_ningun_texto_del_ejecutivo_tiene_jerga(seeded):
    from app.services.ai_checks import forbidden_terms
    from app.services.reports import client_texts, executive

    _with_message(seeded, busy_october(seeded))
    _publish(seeded, "cliente-restaurante", "cambio", 12)

    report = executive(seeded, 1, "2026-10")
    texts = client_texts(report)
    assert len(texts) >= 7
    assert forbidden_terms(" ".join(texts)) == []
    assert report["tickets"]["text"].startswith("Este mes abrió")

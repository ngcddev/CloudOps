# Pruebas del cálculo de SLA 24/7 para P1 (spec 004, T06).
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from app.models.plan import Plan
from app.services.sla import due_dates, sla_state


def make_plan(support_hours: str = "24x7") -> Plan:
    return Plan(
        code="premium",
        name="Premium",
        slo_availability=99.9,
        support_hours=support_hours,
        cpu_quota="1000m",
        memory_quota="1Gi",
    )


def test_p1_a_las_14_horas_vence_a_las_1415_y_1800():
    created_at = datetime(2026, 10, 4, 14, 0, tzinfo=timezone.utc)

    response_due_at, resolution_due_at = due_dates(created_at, "P1", make_plan())

    assert response_due_at == datetime(2026, 10, 4, 14, 15, tzinfo=timezone.utc)
    assert resolution_due_at == datetime(2026, 10, 4, 18, 0, tzinfo=timezone.utc)


def test_due_dates_normaliza_la_fecha_a_utc():
    created_at = datetime(2026, 10, 4, 9, 0, tzinfo=timezone(timedelta(hours=-5)))

    response_due_at, resolution_due_at = due_dates(created_at, "P1", make_plan())

    assert response_due_at.hour == 14
    assert resolution_due_at.hour == 18
    assert response_due_at.tzinfo == timezone.utc


def test_due_dates_rechaza_prioridad_distinta_de_p1():
    with pytest.raises(ValueError, match="Prioridad inválida"):
        due_dates(datetime.now(timezone.utc), "P5", make_plan())


def test_due_dates_rechaza_fecha_sin_zona_horaria():
    with pytest.raises(ValueError, match="debe incluir zona horaria"):
        due_dates(datetime(2026, 10, 4, 14, 0), "P1", make_plan())


def test_p2_el_viernes_en_horario_habil_termina_el_lunes():
    created_at = datetime(2026, 10, 2, 17, 0, tzinfo=ZoneInfo("America/Bogota"))

    response_due_at, resolution_due_at = due_dates(
        created_at, "P2", make_plan("lun-vie 08:00-18:00")
    )

    assert response_due_at == datetime(2026, 10, 2, 23, 0, tzinfo=timezone.utc)
    assert resolution_due_at == datetime(2026, 10, 5, 20, 0, tzinfo=timezone.utc)


def test_p2_el_sabado_fuera_de_horario_empieza_el_lunes():
    created_at = datetime(2026, 10, 3, 12, 0, tzinfo=ZoneInfo("America/Bogota"))

    response_due_at, _ = due_dates(created_at, "P2", make_plan("lun-vie 08:00-18:00"))

    assert response_due_at == datetime(2026, 10, 5, 14, 0, tzinfo=timezone.utc)


def test_estandar_incluye_el_sabado():
    created_at = datetime(2026, 10, 3, 12, 0, tzinfo=ZoneInfo("America/Bogota"))

    response_due_at, _ = due_dates(created_at, "P2", make_plan("lun-sab 07:00-20:00"))

    assert response_due_at == datetime(2026, 10, 3, 18, 0, tzinfo=timezone.utc)


def make_ticket(created_at, response_due_at, resolution_due_at, first_response_at=None):
    from app.models.ticket import Ticket

    return Ticket(
        service_id=1,
        title="Solicitud",
        description="Descripción",
        created_at=created_at,
        response_due_at=response_due_at,
        resolution_due_at=resolution_due_at,
        first_response_at=first_response_at,
    )


def test_sla_state_respuesta_a_tiempo():
    created_at = datetime(2026, 10, 4, 14, 0, tzinfo=timezone.utc)
    ticket = make_ticket(created_at, datetime(2026, 10, 4, 14, 15, tzinfo=timezone.utc), None)

    assert sla_state(ticket, datetime(2026, 10, 4, 14, 11, tzinfo=timezone.utc)) == "a_tiempo"


def test_sla_state_en_riesgo_en_el_borde_exactamente_del_80_por_ciento():
    created_at = datetime(2026, 10, 4, 14, 0, tzinfo=timezone.utc)
    ticket = make_ticket(created_at, datetime(2026, 10, 4, 14, 15, tzinfo=timezone.utc), None)

    assert sla_state(ticket, datetime(2026, 10, 4, 14, 12, tzinfo=timezone.utc)) == "en_riesgo"


def test_sla_state_vencido_al_llegar_a_la_fecha_limite():
    created_at = datetime(2026, 10, 4, 14, 0, tzinfo=timezone.utc)
    due_at = datetime(2026, 10, 4, 14, 15, tzinfo=timezone.utc)
    ticket = make_ticket(created_at, due_at, None)

    assert sla_state(ticket, due_at) == "vencido"


def test_sla_state_cambia_a_solucion_despues_de_la_primera_respuesta():
    created_at = datetime(2026, 10, 4, 14, 0, tzinfo=timezone.utc)
    first_response_at = datetime(2026, 10, 4, 14, 10, tzinfo=timezone.utc)
    resolution_due_at = datetime(2026, 10, 4, 18, 0, tzinfo=timezone.utc)
    ticket = make_ticket(
        created_at,
        datetime(2026, 10, 4, 14, 15, tzinfo=timezone.utc),
        resolution_due_at,
        first_response_at,
    )

    assert sla_state(ticket, datetime(2026, 10, 4, 17, 12, tzinfo=timezone.utc)) == "en_riesgo"

# --- Reloj genérico e incidentes (spec 008, T03) ---

from app.services.sla import clock_state, incident_clocks  # noqa: E402

INICIO = datetime(2026, 10, 24, 14, 0, tzinfo=timezone.utc)


def test_clock_state_cumplido_si_se_hizo_antes_del_limite():
    assert clock_state(INICIO, INICIO + timedelta(minutes=15), INICIO + timedelta(minutes=10)) == "cumplido"


def test_clock_state_vencido_si_se_hizo_despues_del_limite():
    assert clock_state(INICIO, INICIO + timedelta(hours=4), INICIO + timedelta(hours=5)) == "vencido"


def test_clock_state_corriendo():
    due = INICIO + timedelta(minutes=15)
    assert clock_state(INICIO, due, None, INICIO + timedelta(minutes=5)) == "a_tiempo"
    assert clock_state(INICIO, due, None, INICIO + timedelta(minutes=12)) == "en_riesgo"
    assert clock_state(INICIO, due, None, due) == "vencido"


def make_incident(acknowledged_at=None, mitigated_at=None):
    from app.models.incident import Incident

    response_due_at, resolution_due_at = due_dates(INICIO, "P1", make_plan("lun-vie 08:00-18:00"))
    return Incident(
        service_id=1, priority="P1", status="abierto", source="alerta", title="Sitio caído",
        started_at=INICIO, response_due_at=response_due_at, resolution_due_at=resolution_due_at,
        acknowledged_at=acknowledged_at, mitigated_at=mitigated_at,
    )


def test_incidente_tomado_a_los_10_min_y_mitigado_a_las_5_h():
    incident = make_incident(INICIO + timedelta(minutes=10), INICIO + timedelta(hours=5))

    assert incident_clocks(incident) == ("cumplido", "vencido")


def test_incidente_p1_es_24_7_aunque_el_plan_sea_en_horario_habil():
    incident = make_incident()

    assert incident.response_due_at == INICIO + timedelta(minutes=15)
    assert incident.resolution_due_at == INICIO + timedelta(hours=4)
    assert incident_clocks(incident, INICIO + timedelta(minutes=13)) == ("en_riesgo", "a_tiempo")


def test_incidente_sin_tomar_y_vencida_la_respuesta():
    incident = make_incident()

    assert incident_clocks(incident, INICIO + timedelta(minutes=20)) == ("vencido", "a_tiempo")


def test_incidente_con_fechas_sin_zona_de_sqlite():
    incident = make_incident(datetime(2026, 10, 24, 14, 5), None)
    incident.started_at = datetime(2026, 10, 24, 14, 0)

    assert incident_clocks(incident, INICIO + timedelta(minutes=30))[0] == "cumplido"


def test_mitigar_sin_tomar_detiene_tambien_el_reloj_de_respuesta():
    # El sitio volvió a los 5 min (resolved) antes de que alguien lo tomara: la respuesta no sigue corriendo
    incident = make_incident(None, INICIO + timedelta(minutes=5))
    assert incident_clocks(incident, INICIO + timedelta(hours=1)) == ("cumplido", "cumplido")

    # Si se mitigó cuando la respuesta ya estaba vencida, queda vencida
    late = make_incident(None, INICIO + timedelta(minutes=40))
    assert incident_clocks(late, INICIO + timedelta(hours=1)) == ("vencido", "cumplido")

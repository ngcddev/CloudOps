# Pruebas del cálculo de SLA 24/7 para P1 (spec 004, T06).
from datetime import datetime, timedelta, timezone

import pytest

from app.models.plan import Plan
from app.services.sla import due_dates


def make_plan() -> Plan:
    return Plan(
        code="premium",
        name="Premium",
        slo_availability=99.9,
        support_hours="24x7",
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
    with pytest.raises(ValueError, match="solo calcula fechas para la prioridad P1"):
        due_dates(datetime.now(timezone.utc), "P2", make_plan())


def test_due_dates_rechaza_fecha_sin_zona_horaria():
    with pytest.raises(ValueError, match="debe incluir zona horaria"):
        due_dates(datetime(2026, 10, 4, 14, 0), "P1", make_plan())
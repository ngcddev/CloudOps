# Pruebas del mensaje al cliente y del MTTR calculado (spec 009, T08-T09).
from datetime import datetime, timedelta, timezone

import pytest

from app.models import Incident
from app.services.incident_flow import IncidentFlowError, mttr_minutes
from app.services.messages import client_message

# 14:00 en Colombia
INICIO = datetime(2026, 10, 24, 19, 0, tzinfo=timezone.utc)


def incidente(minutos: float | None) -> Incident:
    return Incident(
        service_id=1, priority="P1", status="abierto", source="alerta", title="Sitio caído",
        started_at=INICIO, response_due_at=INICIO, resolution_due_at=INICIO,
        mitigated_at=None if minutos is None else INICIO + timedelta(minutes=minutos),
    )


@pytest.mark.parametrize(
    "minutos, esperado",
    [(7.5, "7 minutos"), (1, "1 minuto"), (0.4, "menos de 1 minuto"), (75, "75 minutos")],
)
def test_la_duracion_sale_de_las_horas_mostradas(minutos, esperado):
    assert f"Tiempo total: {esperado}." in client_message(incidente(minutos))


def test_las_horas_son_de_colombia_aunque_la_base_este_en_utc():
    message = client_message(incidente(7.5))

    assert "a las 14:00." in message and "a las 14:07 el servicio" in message


def test_las_fechas_sin_zona_de_sqlite_se_tratan_como_utc():
    sin_zona = incidente(7.5)
    sin_zona.started_at = INICIO.replace(tzinfo=None)
    sin_zona.mitigated_at = (INICIO + timedelta(minutes=7.5)).replace(tzinfo=None)

    assert "a las 14:00." in client_message(sin_zona)
    assert mttr_minutes(sin_zona) == 7.5


def test_sin_mitigar_no_hay_mensaje_ni_mttr():
    with pytest.raises(IncidentFlowError, match="mitigado"):
        client_message(incidente(None))
    assert mttr_minutes(incidente(None)) is None


def test_el_mttr_lleva_un_decimal():
    assert mttr_minutes(incidente(7.5)) == 7.5
    assert mttr_minutes(incidente(10.04)) == 10.0

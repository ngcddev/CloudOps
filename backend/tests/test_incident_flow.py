# Pruebas del ciclo de vida de un incidente (spec 008, T02).
from datetime import datetime, timezone

import pytest

from app.models.incident import Incident
from app.models.user import User
from app.services.incident_flow import IncidentFlowError, acknowledge, add_event, close, mitigate

T0 = datetime(2026, 10, 24, 14, 0, tzinfo=timezone.utc)


def make_incident(source: str = "manual", status: str = "abierto") -> Incident:
    return Incident(service_id=1, priority="P1", status=status, source=source, title="Sitio caído", started_at=T0,
                    response_due_at=T0, resolution_due_at=T0)


def tecnico() -> User:
    return User(id=7, name="Técnico", email="t@x.test", role="agencia")


def test_ciclo_manual_completo():
    incident = make_incident()
    mitigate(incident, now=datetime(2026, 10, 24, 14, 30, tzinfo=timezone.utc))
    assert incident.status == "mitigado"
    assert incident.mitigated_at.minute == 30

    close(incident, "  Se llenó el disco  ", now=datetime(2026, 10, 24, 15, 0, tzinfo=timezone.utc))
    assert incident.status == "cerrado"
    assert incident.root_cause == "Se llenó el disco"
    assert incident.closed_at.hour == 15


def test_no_se_cierra_un_incidente_abierto():
    with pytest.raises(IncidentFlowError, match="«abierto» a «cerrado»"):
        close(make_incident(), "Causa")


@pytest.mark.parametrize("causa", [None, "", "   "])
def test_cerrar_exige_causa_raiz(causa):
    incident = make_incident(status="mitigado")
    with pytest.raises(IncidentFlowError, match="causa raíz"):
        close(incident, causa)
    assert incident.status == "mitigado"


def test_no_se_mitiga_a_mano_uno_de_alerta():
    incident = make_incident(source="alerta")
    with pytest.raises(IncidentFlowError, match="monitoreo"):
        mitigate(incident)
    assert incident.status == "abierto"


def test_el_aviso_resolved_si_mitiga_uno_de_alerta():
    incident = make_incident(source="alerta")
    mitigate(incident, now=T0, by_alert=True)
    assert incident.status == "mitigado"


def test_no_se_mitiga_dos_veces():
    incident = make_incident(status="mitigado")
    with pytest.raises(IncidentFlowError):
        mitigate(incident)


def test_tomar_fija_respuesta_y_responsable_una_sola_vez():
    incident = make_incident()
    acknowledge(incident, tecnico(), now=datetime(2026, 10, 24, 14, 5, tzinfo=timezone.utc))
    assert incident.acknowledged_at.minute == 5
    assert incident.assignee_id == 7
    assert incident.status == "abierto"

    with pytest.raises(IncidentFlowError, match="ya fue tomado"):
        acknowledge(incident, tecnico())


def test_no_se_toma_uno_cerrado():
    with pytest.raises(IncidentFlowError, match="cerrado"):
        acknowledge(make_incident(status="cerrado"), tecnico())


def test_add_event_sin_actor_es_del_sistema():
    incident = make_incident()
    event = add_event(incident, "detectado", "El sitio no responde")
    assert event.actor_id is None
    assert incident.events == [event]

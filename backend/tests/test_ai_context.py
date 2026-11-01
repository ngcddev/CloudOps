# Pruebas del contexto cerrado que recibe el asistente: hechos reales y sin datos personales (spec 012, T02).
from datetime import timedelta

import pytest
from sqlalchemy import select

from app.models import Client, Service, User
from app.services.ai_context import incident_facts
from tests.rollback_support import T0, open_incident


@pytest.fixture
def mitigado(seeded):
    """Incidente de La Sazón de 14:00 a 14:07 (Colombia), recuperado con rollback de v2 a v1 por un técnico."""
    sazon = seeded.scalar(select(Service).where(Service.namespace == "cliente-restaurante"))
    tecnico = User(name="Laura Técnica", email="laura@forjadigital.test", role="agencia")
    seeded.add(tecnico)
    incident = open_incident(seeded, sazon)
    incident.assignee_id = tecnico.id
    incident.acknowledged_at = T0 + timedelta(minutes=2)
    incident.rollback_from_version, incident.rollback_to_version = "v2", "v1"
    incident.rollback_by_id = tecnico.id
    incident.rollback_at = T0 + timedelta(minutes=3)
    incident.rollback_confirmed_at = T0 + timedelta(minutes=6)
    incident.mitigated_at = T0 + timedelta(minutes=7, seconds=30)
    incident.status = "mitigado"
    seeded.commit()
    return incident


def test_trae_los_hechos_reales_del_incidente(mitigado):
    facts = incident_facts(mitigado)

    assert facts["client"] == "Restaurante La Sazón"
    assert facts["priority"] == "P1"
    assert facts["date"] == "2026-10-24"
    assert (facts["start_time"], facts["end_time"], facts["duration_minutes"]) == ("14:00", "14:07", 7)
    assert (facts["recovery"], facts["from_version"], facts["to_version"]) == ("rollback", "v2", "v1")
    assert facts["times"] == ["14:00", "14:02", "14:03", "14:06", "14:07"]


def test_no_lleva_correos_telefonos_ni_tecnicos(seeded, mitigado):
    cliente = seeded.get(Client, mitigado.service.project.client_id)
    texto = repr(incident_facts(mitigado)).lower()

    for dato in (cliente.email, cliente.phone, cliente.contact_name, "laura", "forjadigital.test", "@"):
        if dato:
            assert dato.lower() not in texto
    assert not {"assignee", "email", "phone", "rollback_by"} & set(incident_facts(mitigado))


def test_sin_mitigar_no_hay_hora_de_fin_ni_recuperacion(seeded):
    sazon = seeded.scalar(select(Service).where(Service.namespace == "cliente-restaurante"))
    facts = incident_facts(open_incident(seeded, sazon))

    assert (facts["end_time"], facts["duration_minutes"], facts["recovery"]) == (None, None, None)
    assert facts["times"] == ["14:00"]


def test_mitigado_a_mano_sin_rollback(seeded):
    sazon = seeded.scalar(select(Service).where(Service.namespace == "cliente-restaurante"))
    incident = open_incident(seeded, sazon, source="manual")
    incident.mitigated_at = T0 + timedelta(minutes=20)
    seeded.commit()

    facts = incident_facts(incident)
    assert (facts["recovery"], facts["from_version"], facts["duration_minutes"]) == ("manual", None, 20)

# Pruebas del webhook de Alertmanager con los payloads guardados en fixtures/ (spec 008, T10-T12).
import json
from pathlib import Path

import pytest
from sqlalchemy import select

from app.config import settings
from app.models import AuditLog, Incident, Service

FIXTURES = Path(__file__).parent / "fixtures"
TOKEN = "token-de-alertmanager-de-pruebas"
URL = "/api/alerts/alertmanager"


@pytest.fixture(autouse=True)
def alertmanager_token(monkeypatch):
    monkeypatch.setattr(settings, "alertmanager_token", TOKEN)


def payload(name: str) -> dict:
    return json.loads((FIXTURES / f"alertmanager_{name}.json").read_text(encoding="utf-8"))


def send(anonymous, name: str, token: str | None = TOKEN):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return anonymous.post(URL, json=payload(name), headers=headers)


def incidents(session_factory) -> list[Incident]:
    with session_factory() as db:
        return list(db.scalars(select(Incident).order_by(Incident.id)))


def service_status(session_factory, namespace="cliente-restaurante") -> str:
    with session_factory() as db:
        return db.scalar(select(Service.status).where(Service.namespace == namespace))


def test_firing_abre_un_p1_de_la_sazon_30_s_antes_de_startsat(anonymous, seeded, session_factory):
    response = send(anonymous, "firing")

    assert response.status_code == 200, response.text
    assert response.json()["results"][0]["result"] == "creado"
    [incident] = incidents(session_factory)
    assert (incident.source, incident.priority, incident.status) == ("alerta", "P1", "abierto")
    assert incident.fingerprint == "5f1c2a9e8b7d6c43"
    # startsAt 19:00:30 − 30 s del `for` = la caída empezó a las 19:00:00
    assert incident.started_at.replace(tzinfo=None).isoformat() == "2026-10-24T19:00:00"
    assert incident.response_due_at.replace(tzinfo=None).isoformat() == "2026-10-24T19:15:00"
    assert incident.resolution_due_at.replace(tzinfo=None).isoformat() == "2026-10-24T23:00:00"
    assert service_status(session_factory) == "caido"
    with session_factory() as db:
        saved = db.get(Incident, incident.id)
        assert [(e.type, e.actor_id) for e in saved.events] == [("detectado", None)]
        log = db.scalar(select(AuditLog).where(AuditLog.entity == "incident"))
        assert (log.action, log.user_id, log.details["origen"]) == ("crear", None, "alerta")


def test_sin_token_o_con_otro_responde_401(anonymous, seeded, session_factory):
    assert send(anonymous, "firing", token=None).status_code == 401
    assert send(anonymous, "firing", token="otro-token").status_code == 401
    assert incidents(session_factory) == []


def test_sin_token_configurado_no_acepta_avisos(anonymous, seeded, monkeypatch):
    monkeypatch.setattr(settings, "alertmanager_token", "")

    assert send(anonymous, "firing", token="").status_code == 401
    assert send(anonymous, "firing", token="cualquiera").status_code == 401


def test_el_token_de_sesion_o_del_pipeline_no_sirve(anonymous, seeded):
    assert send(anonymous, "firing", token=settings.pipeline_token).status_code == 401


def test_el_mismo_firing_tres_veces_deja_un_solo_incidente(anonymous, seeded, session_factory):
    first = send(anonymous, "firing").json()["results"][0]
    for name in ("firing_repetido", "firing"):
        repeated = send(anonymous, name).json()["results"][0]
        assert (repeated["result"], repeated["incident_id"]) == ("duplicado", first["incident_id"])

    assert len(incidents(session_factory)) == 1
    with session_factory() as db:
        assert len(list(db.scalars(select(AuditLog).where(AuditLog.entity == "incident")))) == 1


def test_un_firing_despues_de_mitigado_abre_un_incidente_nuevo(anonymous, seeded, session_factory):
    send(anonymous, "firing")
    with session_factory() as db:
        db.scalar(select(Incident)).status = "mitigado"
        db.commit()

    assert send(anonymous, "firing").json()["results"][0]["result"] == "creado"
    assert [i.status for i in incidents(session_factory)] == ["mitigado", "abierto"]


def test_dos_avisos_simultaneos_no_rompen_el_indice_unico(anonymous, seeded, session_factory, monkeypatch):
    from app.services import incident_alerts

    send(anonymous, "firing")
    # Simula la carrera: el segundo aviso no alcanza a ver el incidente que el primero acaba de guardar
    real = incident_alerts._open_incident
    calls = {"n": 0}

    def blind_first(db, fingerprint):
        calls["n"] += 1
        return None if calls["n"] == 1 else real(db, fingerprint)

    monkeypatch.setattr(incident_alerts, "_open_incident", blind_first)

    response = send(anonymous, "firing_repetido")

    assert response.status_code == 200
    assert response.json()["results"][0]["result"] == "duplicado"
    assert calls["n"] == 2  # la primera consulta no lo vio y el índice único lo frenó
    assert len(incidents(session_factory)) == 1


def test_resolved_mitiga_con_endsat_y_devuelve_el_servicio_a_operativo(anonymous, seeded, session_factory):
    send(anonymous, "firing")

    response = send(anonymous, "resolved")

    assert response.status_code == 200
    assert response.json()["results"][0]["result"] == "mitigado"
    [incident] = incidents(session_factory)
    assert incident.status == "mitigado"
    assert incident.mitigated_at.replace(tzinfo=None).isoformat() == "2026-10-24T19:04:10"
    assert service_status(session_factory) == "operativo"
    with session_factory() as db:
        saved = db.get(Incident, incident.id)
        assert [(e.type, e.actor_id) for e in saved.events] == [("detectado", None), ("recuperado", None)]
        actions = [log.action for log in db.scalars(select(AuditLog).where(AuditLog.entity == "incident"))]
        assert actions == ["crear", "mitigar"]


def test_un_resolved_repetido_o_sin_incidente_se_ignora_con_200(anonymous, seeded, session_factory):
    assert send(anonymous, "resolved").json()["results"][0]["result"] == "ignorado"
    send(anonymous, "firing")
    send(anonymous, "resolved")

    assert send(anonymous, "resolved").json()["results"][0]["result"] == "ignorado"
    assert [i.status for i in incidents(session_factory)] == ["mitigado"]


def test_un_namespace_desconocido_responde_200_y_avisa_en_el_log(anonymous, seeded, session_factory, caplog):
    response = send(anonymous, "firing_desconocido")

    assert response.status_code == 200
    assert response.json()["results"][0]["result"] == "ignorado"
    assert incidents(session_factory) == []
    assert "cliente-desconocido" in caplog.text

# Pruebas de la API del rollback: plan, pedido, un solo rollback a la vez, MTTR y mensaje (spec 009, T04-T09).
from datetime import timedelta

import pytest
from sqlalchemy import select

from app.integrations.argocd import AppStatus
from app.integrations.gitea import GiteaClient
from app.main import app
from app.models import AuditLog, ChangeRequest, Incident, Service, Ticket
from app.routers import incidents as incidents_router
from app.routers.change_requests import get_gitea
from app.routers.incidents import get_argocd
from tests.fake_gitea import FakeGitea
from tests.rollback_support import RUTA, T0, kustomization, open_incident


@pytest.fixture
def client(as_agency):
    return as_agency


@pytest.fixture
def gitea():
    """Gitea con La Sazón ya en la v2 rota."""
    with FakeGitea({RUTA: kustomization("v2")}) as fake:
        app.dependency_overrides[get_gitea] = lambda: GiteaClient(fake.url, fake.repo, fake.token)
        yield fake
        app.dependency_overrides.pop(get_gitea, None)


@pytest.fixture
def clock(monkeypatch):
    class Clock:
        now = T0

        def at(self, minutes: float) -> None:
            self.now = T0 + timedelta(minutes=minutes)

    fake = Clock()
    monkeypatch.setattr(incidents_router, "utcnow", lambda: fake.now)
    return fake


@pytest.fixture
def sazon(seeded) -> Service:
    """La Sazón con la v2 corriendo y la v1 como última estable."""
    service = seeded.scalar(select(Service).where(Service.namespace == "cliente-restaurante"))
    service.current_version, service.stable_version = "v2", "v1"
    seeded.commit()
    return service


@pytest.fixture
def incidente(seeded, sazon) -> Incident:
    return open_incident(seeded, sazon)


# ---------- T04: rollback-plan ----------


def test_el_plan_muestra_v2_a_v1(client, incidente):
    body = client.get(f"/api/incidents/{incidente.id}/rollback-plan").json()

    assert body == {"current_version": "v2", "target_version": "v1", "can_rollback": True, "reason": None}


def test_sin_version_anterior_el_boton_queda_deshabilitado_con_su_razon(client, seeded, sazon):
    sazon.current_version = sazon.stable_version = "v1"
    seeded.commit()
    incident = open_incident(seeded, sazon)

    body = client.get(f"/api/incidents/{incident.id}/rollback-plan").json()

    assert body["can_rollback"] is False
    assert body["reason"] == "No hay una versión anterior a la que volver."


def test_un_incidente_cerrado_no_se_puede_revertir(client, seeded, sazon):
    incident = open_incident(seeded, sazon, status="cerrado")

    body = client.get(f"/api/incidents/{incident.id}/rollback-plan").json()

    assert (body["can_rollback"], body["reason"]) == (False, "El incidente ya no está abierto.")


def test_el_plan_de_un_incidente_inexistente_es_404(client):
    assert client.get("/api/incidents/999/rollback-plan").status_code == 404


def test_un_cliente_no_ve_ni_pide_el_rollback(as_client, seeded, incidente, gitea):
    assert as_client.get(f"/api/incidents/{incidente.id}/rollback-plan").status_code == 403
    assert as_client.post(f"/api/incidents/{incidente.id}/rollback").status_code == 403
    assert as_client.get(f"/api/incidents/{incidente.id}/client-message").status_code == 403
    assert gitea.commits == []


def test_sin_sesion_es_401(anonymous, incidente):
    assert anonymous.get(f"/api/incidents/{incidente.id}/rollback-plan").status_code == 401
    assert anonymous.post(f"/api/incidents/{incidente.id}/rollback").status_code == 401


# ---------- T05: pedir el rollback ----------


def test_el_rollback_escribe_el_commit_y_deja_el_rastro(client, session_factory, incidente, gitea, clock):
    clock.at(2)
    response = client.post(f"/api/incidents/{incidente.id}/rollback", json={"rollback_by_id": 999, "actor": "otro"})

    assert response.status_code == 200, response.text
    body = response.json()
    assert gitea.files[RUTA] == kustomization("v1")
    commit = gitea.commits[-1]
    assert commit["message"] == f"revert(restaurante): volver a v1 (incidente #{incidente.id})"
    assert commit["author"]["name"] == "tecnico.pruebas"
    assert body["rollback"]["status"] == "enviado"
    assert (body["rollback"]["from_version"], body["rollback"]["to_version"]) == ("v2", "v1")
    assert body["rollback"]["by_name"] == "tecnico.pruebas"
    assert body["rollback"]["commit_sha"] == commit["sha"]
    assert body["status"] == "abierto"  # lo mitiga la sonda, no el commit
    assert [e["type"] for e in body["events"]] == ["rollback_enviado"]

    with session_factory() as db:
        saved = db.get(Incident, incidente.id)
        # El actor sale de la sesión: el cuerpo no puede cambiarlo
        assert saved.rollback_by.email == "tecnico.pruebas@forjadigital.test"
        assert saved.rollback_commit_sha == commit["sha"]
        log = db.scalar(select(AuditLog).where(AuditLog.action == "rollback"))
        assert (log.entity, log.entity_id, log.user_id) == ("incident", incidente.id, saved.rollback_by_id)
        assert log.details["desde"] == "v2" and log.details["hacia"] == "v1"


def test_el_segundo_rollback_es_409_y_no_hay_otro_commit(client, incidente, gitea):
    assert client.post(f"/api/incidents/{incidente.id}/rollback").status_code == 200

    second = client.post(f"/api/incidents/{incidente.id}/rollback")

    assert second.status_code == 409
    assert "en curso" in second.json()["detail"]
    assert len(gitea.commits) == 1


def test_el_plan_de_un_rollback_en_curso_dice_por_que_no(client, incidente, gitea):
    client.post(f"/api/incidents/{incidente.id}/rollback")

    body = client.get(f"/api/incidents/{incidente.id}/rollback-plan").json()

    assert (body["can_rollback"], body["reason"]) == (False, "Ya hay un rollback en curso.")
    assert (body["current_version"], body["target_version"]) == ("v2", "v1")


def test_dos_incidentes_del_mismo_servicio_no_lanzan_dos_rollbacks(client, seeded, sazon, incidente, gitea):
    otro = open_incident(seeded, sazon, source="manual")
    assert client.post(f"/api/incidents/{incidente.id}/rollback").status_code == 200

    response = client.post(f"/api/incidents/{otro.id}/rollback")

    assert response.status_code == 409
    assert "este servicio" in response.json()["detail"]
    assert len(gitea.commits) == 1


def test_si_git_ya_tiene_la_version_de_destino_es_409(client, incidente, gitea):
    gitea.files[RUTA] = kustomization("v1")  # alguien revirtió a mano

    response = client.post(f"/api/incidents/{incidente.id}/rollback")

    assert response.status_code == 409
    assert "Argo CD" in response.json()["detail"]
    assert gitea.commits == []


def test_sin_version_anterior_el_post_es_409(client, seeded, sazon, gitea):
    sazon.current_version = sazon.stable_version = "v1"
    seeded.commit()
    incident = open_incident(seeded, sazon)

    response = client.post(f"/api/incidents/{incident.id}/rollback")

    assert response.status_code == 409
    assert gitea.commits == []


def test_un_incidente_mitigado_no_se_revierte(client, seeded, sazon, gitea):
    incident = open_incident(seeded, sazon, status="mitigado")

    assert client.post(f"/api/incidents/{incident.id}/rollback").status_code == 409
    assert gitea.commits == []


def test_si_gitea_falla_no_queda_nada_guardado(client, session_factory, incidente, gitea):
    # El token del Hub ya no es válido en Gitea
    app.dependency_overrides[get_gitea] = lambda: GiteaClient(gitea.url, gitea.repo, "token-vencido")

    response = client.post(f"/api/incidents/{incidente.id}/rollback")

    assert response.status_code == 502
    with session_factory() as db:
        assert db.get(Incident, incidente.id).rollback_commit_sha is None
        assert db.scalar(select(AuditLog).where(AuditLog.action == "rollback")) is None


# ---------- T06: el cambio en validación hacia la versión rota ----------


@pytest.fixture
def cambio_en_validacion(seeded, sazon) -> ChangeRequest:
    ticket = Ticket(service_id=sazon.id, title="Publicar v2", description="v2", kind="cambio")
    seeded.add(ticket)
    seeded.flush()
    change = ChangeRequest(
        ticket_id=ticket.id, service_id=sazon.id, from_version="v1", to_version="v2",
        status="en_validacion", gitops_commit_sha="b" * 40, approved_at=T0,
    )
    seeded.add(change)
    seeded.commit()
    return change


def test_el_cambio_hacia_la_version_rota_queda_fallido_con_nota_y_no_bloquea_otros(
    client, session_factory, seeded, sazon, incidente, cambio_en_validacion, gitea
):
    # Con el cambio en validación el Hub aún dice v1, pero Git ya tiene v2
    sazon.current_version = "v1"
    seeded.commit()
    assert client.get(f"/api/incidents/{incidente.id}/rollback-plan").json()["current_version"] == "v2"

    assert client.post(f"/api/incidents/{incidente.id}/rollback").status_code == 200

    with session_factory() as db:
        change = db.get(ChangeRequest, cambio_en_validacion.id)
        assert change.status == "fallida"
        events = [e for e in db.get(Ticket, change.ticket_id).events if e.type == "cambio"]
        assert f"Revertido por el incidente #{incidente.id}" in [e.note for e in events]
        # Lo que ve el cliente va en el lenguaje del glosario
        public = [e.note for e in events if not e.internal]
        assert public == ["Se restauró una versión estable para mantener la continuidad."]

    # Un cambio posterior se puede pedir: «fallida» no cuenta como cambio abierto
    ticket = client.post(
        "/api/tickets",
        json={"service_id": sazon.id, "title": "Corregir v2", "description": "Arreglo", "kind": "cambio"},
    ).json()
    created = client.post("/api/change-requests", json={"ticket_id": ticket["id"], "to_version": "v2.1"})
    assert created.status_code == 201, created.text


# ---------- T08: MTTR y mitigación a mano (CA-9) ----------


def test_el_mttr_sale_de_las_horas_reales(client, seeded, sazon, clock):
    incident = open_incident(seeded, sazon, source="manual")
    clock.at(7.5)

    body = client.post(f"/api/incidents/{incident.id}/mitigate").json()

    assert body["mitigated_at"].startswith("2026-10-24T19:07:30")
    assert body["mttr_minutes"] == 7.5
    assert client.get("/api/incidents").json()[0]["mttr_minutes"] == 7.5


def test_el_mttr_es_nulo_mientras_el_incidente_sigue_abierto(client, incidente):
    assert client.get(f"/api/incidents/{incidente.id}").json()["mttr_minutes"] is None


def test_mitigar_a_mano_una_alerta_sin_rollback_confirmado_es_409(client, incidente):
    response = client.post(f"/api/incidents/{incidente.id}/mitigate")

    assert response.status_code == 409
    assert "monitoreo" in response.json()["detail"]


def test_mitigar_a_mano_con_el_rollback_confirmado_vale_y_deja_operativo_el_sitio(
    client, session_factory, sazon, incidente, gitea, clock
):
    client.post(f"/api/incidents/{incidente.id}/rollback")
    with session_factory() as db:
        db.get(Incident, incidente.id).rollback_confirmed_at = T0 + timedelta(minutes=3)
        db.commit()
    clock.at(6)

    response = client.post(f"/api/incidents/{incidente.id}/mitigate")

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "mitigado"
    assert response.json()["mttr_minutes"] == 6.0
    with session_factory() as db:
        assert db.get(Service, sazon.id).status == "operativo"
        log = db.scalar(select(AuditLog).where(AuditLog.action == "mitigar"))
        assert log.details["origen"] == "rollback_confirmado"


# ---------- Avance del rollback ----------


def test_el_avance_pasa_de_enviado_a_sincronizando_y_recuperado(client, session_factory, incidente, gitea):
    argo = {"estado": AppStatus("OutOfSync", "Healthy", "0" * 40)}

    class ArgoSimulado:
        def get_application(self, name):
            return argo["estado"]

    app.dependency_overrides[get_argocd] = lambda: ArgoSimulado()
    try:
        sha = client.post(f"/api/incidents/{incidente.id}/rollback").json()["rollback"]["commit_sha"]
        assert client.get(f"/api/incidents/{incidente.id}").json()["rollback"]["status"] == "enviado"

        argo["estado"] = AppStatus("OutOfSync", "Progressing", sha)
        assert client.get(f"/api/incidents/{incidente.id}").json()["rollback"]["status"] == "sincronizando"

        with session_factory() as db:
            db.get(Incident, incidente.id).rollback_confirmed_at = T0
            db.commit()
        assert client.get(f"/api/incidents/{incidente.id}").json()["rollback"]["status"] == "recuperado"
    finally:
        app.dependency_overrides.pop(get_argocd, None)


def test_un_incidente_sin_rollback_se_lee_igual(client, incidente):
    body = client.get(f"/api/incidents/{incidente.id}").json()

    assert body["rollback"]["status"] == "sin_rollback"
    assert body["rollback"]["by_name"] is None


# ---------- T09: mensaje al cliente ----------


def _mitigado_a_las_1407(client, seeded, sazon, clock):
    incident = open_incident(seeded, sazon, source="manual")
    clock.at(7.5)
    client.post(f"/api/incidents/{incident.id}/mitigate")
    return incident


def test_el_mensaje_trae_las_horas_de_colombia_y_los_minutos(client, seeded, sazon, clock):
    incident = _mitigado_a_las_1407(client, seeded, sazon, clock)

    response = client.get(f"/api/incidents/{incident.id}/client-message")

    assert response.status_code == 200
    message = response.json()["message"]
    assert "14:00" in message and "14:07" in message and "7 minutos" in message
    assert message.startswith("Detectamos una falla temporal en su sitio a las 14:00.")


def test_el_mensaje_no_lleva_jerga(client, seeded, sazon, clock):
    incident = _mitigado_a_las_1407(client, seeded, sazon, clock)

    message = client.get(f"/api/incidents/{incident.id}/client-message").json()["message"].lower()

    for jerga in ("rollback", "incidente", "p1", "mttr", "argo", "commit", "namespace", "pod", "clúster", "v1", "v2"):
        assert jerga not in message


def test_antes_de_mitigar_no_hay_mensaje(client, incidente):
    response = client.get(f"/api/incidents/{incidente.id}/client-message")

    assert response.status_code == 409

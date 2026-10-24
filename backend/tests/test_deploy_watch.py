# Pruebas del seguimiento de publicaciones con Argo CD simulado (spec 005, T15).
import asyncio
from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.integrations.argocd import AppStatus, ArgoCDError
from app.models import AuditLog, ChangeRequest, Deployment, Service, Ticket, TicketEvent, User
from app.services import deploy_watch
from app.services.deploy_watch import check_cycle, is_published

SHA = "a" * 40
AHORA = datetime(2026, 10, 11, 15, 0, tzinfo=timezone.utc)


class ArgoSimulado:
    """Responde con el estado que la prueba fije para cada aplicación."""

    def __init__(self, **apps):
        self.apps = apps
        self.consultas: list[str] = []

    def get_application(self, name: str) -> AppStatus:
        self.consultas.append(name)
        app = self.apps.get(name)
        if isinstance(app, Exception):
            raise app
        return app or AppStatus("Synced", "Healthy", None)


@pytest.fixture
def en_validacion(seeded):
    """Un cambio de El Tornillo aprobado y esperando a Argo CD, con el commit SHA."""
    service = seeded.scalar(select(Service).where(Service.namespace == "cliente-ferreteria"))
    tecnico = seeded.scalar(select(User).where(User.role == "agencia"))
    ticket = Ticket(service_id=service.id, title="Portada", description="Nueva portada", kind="cambio")
    seeded.add(ticket)
    seeded.flush()
    change = ChangeRequest(
        ticket_id=ticket.id,
        service_id=service.id,
        from_version="v1",
        to_version="v1.1",
        status="en_validacion",
        approved_by_id=tecnico.id,
        gitops_commit_sha=SHA,
    )
    seeded.add(change)
    seeded.commit()
    return change


def test_is_published_exige_synced_healthy_y_la_revision_del_commit():
    assert is_published(AppStatus("Synced", "Healthy", SHA), SHA)
    assert is_published(AppStatus("Synced", "Healthy", SHA.upper()), SHA)
    assert not is_published(AppStatus("OutOfSync", "Healthy", SHA), SHA)
    assert not is_published(AppStatus("Synced", "Degraded", SHA), SHA)
    assert not is_published(AppStatus("Synced", "Healthy", "b" * 40), SHA)
    assert not is_published(AppStatus("Synced", "Healthy", SHA), None)


def test_pasa_a_desplegada_y_registra_el_despliegue(seeded, en_validacion):
    argo = ArgoSimulado(**{"cliente-ferreteria": AppStatus("Synced", "Healthy", SHA)})

    deployed = check_cycle(seeded, argo, now=AHORA)

    assert deployed == [en_validacion.id]
    seeded.refresh(en_validacion)
    assert en_validacion.status == "desplegada"
    assert en_validacion.deployed_at is not None
    service = seeded.get(Service, en_validacion.service_id)
    assert (service.current_version, service.stable_version) == ("v1.1", "v1.1")
    assert (service.sync_status, service.health_status) == ("Synced", "Healthy")
    deployment = seeded.scalar(select(Deployment).where(Deployment.service_id == service.id))
    assert (deployment.version, deployment.commit_sha, deployment.source) == ("v1.1", SHA, "cambio")
    assert deployment.author == seeded.get(User, en_validacion.approved_by_id).name


def test_el_paso_a_desplegada_queda_en_el_historial(seeded, en_validacion):
    check_cycle(seeded, ArgoSimulado(**{"cliente-ferreteria": AppStatus("Synced", "Healthy", SHA)}), now=AHORA)

    event = seeded.scalars(
        select(TicketEvent).where(TicketEvent.ticket_id == en_validacion.ticket_id).order_by(TicketEvent.id)
    ).all()[-1]
    assert (event.type, event.from_value, event.to_value) == ("cambio", "en_validacion", "desplegada")
    assert event.actor_id == en_validacion.approved_by_id


@pytest.mark.parametrize(
    "estado",
    [
        AppStatus("OutOfSync", "Healthy", "b" * 40),  # sincronización pendiente
        AppStatus("Synced", "Progressing", SHA),  # aún arrancando
        AppStatus("Synced", "Degraded", SHA),  # falla de salud
        AppStatus("Synced", "Healthy", "b" * 40),  # sano, pero en otra revisión
    ],
)
def test_sigue_en_validacion_si_no_esta_sincronizado_sano_y_en_la_revision(seeded, en_validacion, estado):
    check_cycle(seeded, ArgoSimulado(**{"cliente-ferreteria": estado}), now=AHORA)

    seeded.refresh(en_validacion)
    assert en_validacion.status == "en_validacion"
    assert seeded.scalars(select(Deployment)).all() == []
    service = seeded.get(Service, en_validacion.service_id)
    assert service.current_version == "v1"
    # el estado que informa Argo CD sí se refleja
    assert (service.sync_status, service.health_status) == (estado.sync, estado.health)


def test_no_duplica_el_despliegue_en_vueltas_siguientes(seeded, en_validacion):
    argo = ArgoSimulado(**{"cliente-ferreteria": AppStatus("Synced", "Healthy", SHA)})

    check_cycle(seeded, argo, now=AHORA)
    second = check_cycle(seeded, argo, now=AHORA)

    assert second == []
    assert len(seeded.scalars(select(Deployment)).all()) == 1


def test_un_fallo_con_un_servicio_no_frena_a_los_demas(seeded, en_validacion):
    argo = ArgoSimulado(
        **{
            "cliente-restaurante": ArgoCDError("sin conexión"),
            "cliente-ferreteria": AppStatus("Synced", "Healthy", SHA),
        }
    )

    deployed = check_cycle(seeded, argo, now=AHORA)

    assert deployed == [en_validacion.id]
    restaurante = seeded.scalar(select(Service).where(Service.namespace == "cliente-restaurante"))
    assert restaurante.sync_status == "Unknown"


def test_refresca_los_tres_clientes_en_cada_vuelta(seeded):
    argo = ArgoSimulado()

    check_cycle(seeded, argo, now=AHORA)

    assert sorted(argo.consultas) == ["cliente-consultorio", "cliente-ferreteria", "cliente-restaurante"]
    assert {s.sync_status for s in seeded.scalars(select(Service)).all()} == {"Synced"}


def test_watch_forever_sigue_aunque_una_vuelta_falle(session_factory, monkeypatch):
    llamadas = []

    def vuelta(db, argocd, gitea=None):
        llamadas.append(1)
        if len(llamadas) == 1:
            raise RuntimeError("base caída")

    monkeypatch.setattr(deploy_watch, "check_cycle", vuelta)

    async def correr():
        tarea = asyncio.create_task(deploy_watch.watch_forever(session_factory, object(), interval=0.01))
        await asyncio.sleep(0.2)
        tarea.cancel()
        try:
            await tarea
        except asyncio.CancelledError:
            pass

    asyncio.run(correr())

    assert len(llamadas) >= 2


# ---------- Reconciliar con Git cuando alguien cambia la versión a mano (spec 005, T25) ----------

from app.integrations.gitea import GiteaClient  # noqa: E402
from tests.fake_gitea import FakeGitea  # noqa: E402

KUSTOMIZATION = "images:\n  - name: x\n    newName: gitea.hub.local/forja-digital/ferreteria\n    newTag: {tag}\n"
RUTA = "clients/ferreteria/kustomization.yaml"
FERRETERIA = "cliente-ferreteria"


def _con_git(tag: str):
    """Gitea falso con el tag indicado en el kustomization de El Tornillo."""
    fake = FakeGitea({
        RUTA: KUSTOMIZATION.format(tag=tag),
        "clients/restaurante/kustomization.yaml": KUSTOMIZATION.format(tag="v1"),
        "clients/consultorio/kustomization.yaml": KUSTOMIZATION.format(tag="v1"),
    })
    return fake


def _reconciliar(db, fake, status=AppStatus("Synced", "Healthy", SHA)):
    # Por defecto Argo CD ya aplicó el último commit de la rama; las pruebas de revisión atrasada lo cambian
    fake.head = fake.head or status.revision
    argo = ArgoSimulado(**{FERRETERIA: status})
    return check_cycle(db, argo, now=AHORA, gitea=GiteaClient(fake.url, fake.repo, fake.token))


def test_un_revert_manual_en_git_devuelve_la_consola_a_v1(seeded, en_validacion):
    # El cambio del Hub ya se publicó: la consola está en v1.1
    check_cycle(seeded, ArgoSimulado(**{FERRETERIA: AppStatus("Synced", "Healthy", SHA)}), now=AHORA)
    with _con_git("v1") as fake:  # alguien hizo `git revert` y Argo CD ya sincronizó
        _reconciliar(seeded, fake, AppStatus("Synced", "Healthy", "c" * 40))

    service = seeded.scalar(select(Service).where(Service.namespace == FERRETERIA))
    assert (service.current_version, service.stable_version) == ("v1", "v1")
    last = seeded.scalars(select(Deployment).order_by(Deployment.id)).all()[-1]
    assert (last.version, last.source, last.author, last.commit_sha) == (
        "v1", "rollback", "Cambio manual en Git", "c" * 40
    )


def test_un_cambio_manual_hacia_una_version_nueva_es_un_cambio(seeded):
    with _con_git("v2") as fake:
        _reconciliar(seeded, fake)

    service = seeded.scalar(select(Service).where(Service.namespace == FERRETERIA))
    assert service.current_version == "v2"
    deployment = seeded.scalar(select(Deployment).where(Deployment.service_id == service.id))
    assert (deployment.source, deployment.author) == ("cambio", "Cambio manual en Git")


def test_no_toca_la_version_si_hay_un_cambio_del_hub_en_curso(seeded, en_validacion):
    with _con_git("v1.1") as fake:
        _reconciliar(seeded, fake, AppStatus("OutOfSync", "Healthy", "d" * 40))
    with _con_git("v9") as fake:
        _reconciliar(seeded, fake, AppStatus("Synced", "Healthy", "d" * 40))

    service = seeded.get(Service, en_validacion.service_id)
    assert service.current_version == "v1"


def test_espera_a_que_argocd_sincronice_antes_de_alinear(seeded):
    with _con_git("v2") as fake:
        _reconciliar(seeded, fake, AppStatus("OutOfSync", "Healthy", SHA))

    service = seeded.scalar(select(Service).where(Service.namespace == FERRETERIA))
    assert service.current_version == "v1"
    assert seeded.scalars(select(Deployment)).all() == []


def test_con_la_aplicacion_degradada_cambia_la_activa_pero_no_la_estable(seeded):
    with _con_git("v2") as fake:
        _reconciliar(seeded, fake, AppStatus("Synced", "Degraded", SHA))

    service = seeded.scalar(select(Service).where(Service.namespace == FERRETERIA))
    assert (service.current_version, service.stable_version) == ("v2", "v1")


def test_sin_diferencias_no_registra_nada(seeded):
    with _con_git("v1") as fake:
        _reconciliar(seeded, fake)

    assert seeded.scalars(select(Deployment)).all() == []


def test_si_gitea_no_responde_la_vuelta_sigue(seeded):
    sin_conexion = GiteaClient("http://127.0.0.1:9", "forja-digital/hub-gitops", "t", timeout=1)
    argo = ArgoSimulado(**{FERRETERIA: AppStatus("Synced", "Healthy", SHA)})

    check_cycle(seeded, argo, now=AHORA, gitea=sin_conexion)

    service = seeded.scalar(select(Service).where(Service.namespace == FERRETERIA))
    assert service.current_version == "v1"
    assert service.sync_status == "Synced"


def test_no_alinea_si_argocd_sigue_en_una_revision_anterior_a_la_rama(seeded):
    # Alguien empuja v2 a mano: Git ya está en el commit nuevo pero Argo CD sigue `Synced` en el anterior
    with _con_git("v2") as fake:
        fake.head = "e" * 40
        _reconciliar(seeded, fake, AppStatus("Synced", "Healthy", "d" * 40))

    service = seeded.scalar(select(Service).where(Service.namespace == FERRETERIA))
    assert (service.current_version, service.stable_version) == ("v1", "v1")
    assert seeded.scalars(select(Deployment)).all() == []


def test_el_despliegue_manual_guarda_el_commit_que_trajo_la_version(seeded):
    with _con_git("v2") as fake:
        fake.head = "f" * 40
        _reconciliar(seeded, fake, AppStatus("Synced", "Healthy", "f" * 40))

    assert seeded.scalar(select(Deployment)).commit_sha == "f" * 40


def test_si_no_se_puede_leer_la_rama_no_se_reconcilia_pero_la_vuelta_sigue(seeded):
    sin_conexion = GiteaClient("http://127.0.0.1:9", "forja-digital/hub-gitops", "t", timeout=1)
    argo = ArgoSimulado(**{FERRETERIA: AppStatus("Synced", "Healthy", SHA)})

    check_cycle(seeded, argo, now=AHORA, gitea=sin_conexion)

    service = seeded.scalar(select(Service).where(Service.namespace == FERRETERIA))
    assert (service.sync_status, service.current_version) == ("Synced", "v1")


# ---------- Cambios que no llegan a publicarse (estado fallida) ----------

from datetime import timedelta  # noqa: E402


@pytest.fixture
def client(seeded, as_user):
    """Estas pruebas operan como Sofía, técnica de la agencia sembrada (spec 007)."""
    return as_user("sofia@forjadigital.test")


def _aprobado_hace(db, change, minutos: int):
    change.approved_at = AHORA - timedelta(minutes=minutos)
    db.commit()


def test_un_cambio_que_no_se_publica_a_tiempo_pasa_a_fallida_y_libera_el_sitio(seeded, en_validacion):
    _aprobado_hace(seeded, en_validacion, 11)
    argo = ArgoSimulado(**{FERRETERIA: AppStatus("Synced", "Degraded", SHA)})

    deployed = check_cycle(seeded, argo, now=AHORA)

    seeded.refresh(en_validacion)
    assert deployed == []
    assert en_validacion.status == "fallida"
    assert en_validacion.deployed_at is None
    event = seeded.scalars(
        select(TicketEvent).where(TicketEvent.ticket_id == en_validacion.ticket_id).order_by(TicketEvent.id)
    ).all()[-1]
    assert (event.from_value, event.to_value, event.internal) == ("en_validacion", "fallida", False)
    assert "Argo" not in event.note and "commit" not in event.note.lower()
    service = seeded.get(Service, en_validacion.service_id)
    assert service.current_version == "v1"


def test_dentro_del_tiempo_de_validacion_sigue_esperando(seeded, en_validacion):
    _aprobado_hace(seeded, en_validacion, 9)

    check_cycle(seeded, ArgoSimulado(**{FERRETERIA: AppStatus("Synced", "Progressing", SHA)}), now=AHORA)

    seeded.refresh(en_validacion)
    assert en_validacion.status == "en_validacion"


def test_un_cambio_publicado_a_tiempo_no_falla_aunque_haya_pasado_el_limite(seeded, en_validacion):
    _aprobado_hace(seeded, en_validacion, 30)

    check_cycle(seeded, ArgoSimulado(**{FERRETERIA: AppStatus("Synced", "Healthy", SHA)}), now=AHORA)

    seeded.refresh(en_validacion)
    assert en_validacion.status == "desplegada"


def test_tras_fallar_se_puede_pedir_otro_cambio_para_el_sitio(client, seeded, en_validacion):
    _aprobado_hace(seeded, en_validacion, 11)
    check_cycle(seeded, ArgoSimulado(**{FERRETERIA: AppStatus("Synced", "Degraded", SHA)}), now=AHORA)
    ticket = client.post(
        "/api/tickets",
        json={"service_id": en_validacion.service_id, "title": "Corregir", "description": "x", "kind": "cambio"},
    ).json()

    response = client.post("/api/change-requests", json={"ticket_id": ticket["id"], "to_version": "v1.2"})

    assert response.status_code == 201


def test_publicar_queda_en_la_bitacora_a_nombre_del_sistema(seeded, en_validacion):
    check_cycle(seeded, ArgoSimulado(**{"cliente-ferreteria": AppStatus("Synced", "Healthy", SHA)}), now=AHORA)

    log = seeded.scalar(select(AuditLog))
    assert (log.action, log.entity, log.entity_id, log.user_id) == ("desplegar", "change_request", en_validacion.id, None)
    assert log.details == {"a": "v1.1", "commit": SHA[:7]}


def test_fallar_queda_en_la_bitacora_a_nombre_del_sistema(seeded, en_validacion):
    _aprobado_hace(seeded, en_validacion, 11)
    check_cycle(seeded, ArgoSimulado(**{FERRETERIA: AppStatus("Synced", "Degraded", SHA)}), now=AHORA)

    log = seeded.scalar(select(AuditLog))
    assert (log.action, log.entity_id, log.user_id) == ("fallar", en_validacion.id, None)
    assert log.details["salud"] == "Degraded"


def test_si_todavia_no_se_publica_no_hay_registro_en_la_bitacora(seeded, en_validacion):
    check_cycle(seeded, ArgoSimulado(**{FERRETERIA: AppStatus("OutOfSync", "Healthy", SHA)}), now=AHORA)

    assert seeded.scalar(select(AuditLog)) is None

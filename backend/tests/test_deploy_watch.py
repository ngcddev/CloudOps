# Pruebas del seguimiento de publicaciones con Argo CD simulado (spec 005, T15).
import asyncio
from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.integrations.argocd import AppStatus, ArgoCDError
from app.models import ChangeRequest, Deployment, Service, Ticket, TicketEvent, User
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

    def vuelta(db, argocd):
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

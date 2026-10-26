# Pruebas de la confirmación del rollback en el seguimiento de Argo CD, con Gitea y Argo CD simulados (spec 009, T07).
from datetime import timedelta

import pytest
from sqlalchemy import select

from app.integrations.argocd import AppStatus
from app.integrations.gitea import GiteaClient
from app.models import AuditLog, Deployment, Service, User
from app.services.deploy_watch import check_cycle
from app.services.gitops_publish import publish_rollback
from tests.fake_gitea import FakeGitea
from tests.rollback_support import RUTA, T0, kustomization, open_incident


class ArgoSimulado:
    """Responde con el estado que la prueba fije para cada aplicación."""

    def __init__(self):
        self.estado = AppStatus("Synced", "Healthy", None)

    def get_application(self, name: str) -> AppStatus:
        return self.estado


@pytest.fixture
def gitea():
    with FakeGitea({RUTA: kustomization("v2")}) as fake:
        yield fake


@pytest.fixture
def con_rollback(seeded, gitea):
    """La Sazón con la v2 rota y un incidente cuyo rollback ya escribió el commit hacia v1."""
    service = seeded.scalar(select(Service).where(Service.namespace == "cliente-restaurante"))
    service.current_version, service.stable_version = "v2", "v1"
    incident = open_incident(seeded, service)
    cliente = GiteaClient(gitea.url, gitea.repo, gitea.token)
    sha = publish_rollback(cliente, service.namespace, "v1", incident.id, "Sofía", "sofia@forjadigital.test")
    incident.rollback_from_version, incident.rollback_to_version = "v2", "v1"
    incident.rollback_commit_sha = sha
    incident.rollback_by_id = seeded.scalar(select(User).where(User.role == "agencia")).id
    incident.rollback_at = T0
    seeded.commit()
    return incident, sha, cliente


def test_el_rollback_se_confirma_con_synced_healthy_y_la_revision_del_commit(seeded, con_rollback):
    incident, sha, cliente = con_rollback
    argo = ArgoSimulado()
    argo.estado = AppStatus("Synced", "Healthy", sha)

    check_cycle(seeded, argo, now=T0 + timedelta(minutes=3), gitea=cliente)

    seeded.refresh(incident)
    service = seeded.get(Service, incident.service_id)
    assert incident.rollback_confirmed_at is not None
    assert (service.current_version, service.stable_version) == ("v1", "v1")
    # Un solo Deployment, como restauración y a nombre de quien la pidió
    historial = seeded.scalars(select(Deployment).where(Deployment.service_id == service.id)).all()
    assert [(d.version, d.source, d.author, d.commit_sha) for d in historial] == [
        ("v1", "rollback", incident.rollback_by.name, sha)
    ]
    assert incident.events[-1].type == "rollback_confirmado"
    assert incident.events[-1].actor_name == "Sistema"
    log = seeded.scalar(select(AuditLog).where(AuditLog.action == "confirmar_rollback"))
    assert (log.user_id, log.entity, log.entity_id) == (None, "incident", incident.id)


def test_sin_salud_el_rollback_sigue_pendiente_y_reconcile_no_duplica_el_historial(seeded, con_rollback, gitea):
    incident, sha, cliente = con_rollback
    argo = ArgoSimulado()
    # Argo CD ya está en el commit del rollback (que además es la cabeza de la rama) pero aún no está sano
    argo.estado = AppStatus("Synced", "Progressing", sha)
    gitea.head = sha

    check_cycle(seeded, argo, now=T0 + timedelta(minutes=2), gitea=cliente)

    seeded.refresh(incident)
    assert incident.rollback_confirmed_at is None
    assert seeded.scalars(select(Deployment)).all() == []  # reconcile_version se saltó el servicio

    # Un ciclo después, ya sano: se confirma y queda UN solo Deployment
    argo.estado = AppStatus("Synced", "Healthy", sha)
    check_cycle(seeded, argo, now=T0 + timedelta(minutes=3), gitea=cliente)
    check_cycle(seeded, argo, now=T0 + timedelta(minutes=4), gitea=cliente)

    assert len(seeded.scalars(select(Deployment)).all()) == 1


def test_con_otra_revision_no_se_confirma(seeded, con_rollback):
    incident, sha, cliente = con_rollback
    argo = ArgoSimulado()
    argo.estado = AppStatus("Synced", "Healthy", "f" * 40)

    check_cycle(seeded, argo, now=T0 + timedelta(minutes=3), gitea=cliente)

    seeded.refresh(incident)
    assert incident.rollback_confirmed_at is None
    assert seeded.get(Service, incident.service_id).current_version == "v2"


def test_confirmar_no_depende_de_que_el_incidente_siga_abierto(seeded, con_rollback):
    # La sonda puede ver el sitio sano antes que Argo CD: el incidente ya está mitigado y el historial se completa después
    incident, sha, cliente = con_rollback
    incident.status = "mitigado"
    incident.mitigated_at = T0 + timedelta(minutes=2)
    seeded.commit()
    argo = ArgoSimulado()
    argo.estado = AppStatus("Synced", "Healthy", sha)

    check_cycle(seeded, argo, now=T0 + timedelta(minutes=3), gitea=cliente)

    seeded.refresh(incident)
    assert incident.rollback_confirmed_at is not None
    assert incident.status == "mitigado"

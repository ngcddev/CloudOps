# Prueba de integración del ciclo GitOps (spec 005, T17): aprobar un cambio crea exactamente un
# commit y Argo CD lo confirma. Corre contra Gitea y Argo CD falsos que hablan HTTP de verdad; si
# GITEA_TEST_URL, GITEA_TEST_TOKEN y GITEA_TEST_REPO están definidos, repite la aprobación contra un
# Gitea local real (usa un repo de pruebas: la prueba hace commits en él).
import json
import os
import urllib.request

import pytest
from sqlalchemy import select

from app.integrations.argocd import ArgoCDClient
from app.integrations.gitea import GiteaClient
from app.main import app
from app.models import Service, User
from app.routers.change_requests import get_gitea
from app.services.deploy_watch import check_cycle
from app.services.kustomization import get_tags
from tests.fake_argocd import FakeArgoCD
from tests.fake_gitea import FakeGitea

PATH = "clients/ferreteria/kustomization.yaml"
KUSTOMIZATION = (
    "apiVersion: kustomize.config.k8s.io/v1beta1\n"
    "kind: Kustomization\n"
    "namespace: cliente-ferreteria\n"
    "images:\n"
    "  - name: gitea.hub.local/forja-digital/plantilla\n"
    "    newName: gitea.hub.local/forja-digital/ferreteria\n"
    "    newTag: v1\n"
)


def _pedir_y_aprobar(client, db, gitea_client: GiteaClient, to_version: str) -> dict:
    """Crea la solicitud de cambio de El Tornillo y la aprueba con el cliente de Gitea indicado."""
    service = db.scalar(select(Service).where(Service.namespace == "cliente-ferreteria"))
    tecnico = db.scalar(select(User).where(User.role == "agencia"))
    ticket = client.post(
        "/api/tickets",
        json={"service_id": service.id, "title": "Publicar la nueva portada", "description": "Portada", "kind": "cambio"},
    ).json()
    change = client.post("/api/change-requests", json={"ticket_id": ticket["id"], "to_version": to_version})
    assert change.status_code == 201, change.text
    app.dependency_overrides[get_gitea] = lambda: gitea_client
    approved = client.post(f"/api/change-requests/{change.json()['id']}/approve", json={"actor_id": tecnico.id})
    assert approved.status_code == 200, approved.text
    return approved.json()


def test_ciclo_completo_aprobar_commit_argocd_y_consola(client, seeded):
    with FakeGitea({PATH: KUSTOMIZATION}) as gitea, FakeArgoCD({}) as argocd:
        gitea_client = GiteaClient(gitea.url, gitea.repo, gitea.token)

        change = _pedir_y_aprobar(client, seeded, gitea_client, "v1.1")

        # Aprobar crea exactamente un commit y cambia solo el tag
        assert len(gitea.commits) == 1
        assert change["status"] == "en_validacion"
        assert change["gitops_commit_sha"] == gitea.commits[0]["sha"]
        assert get_tags(gitea.files[PATH]) == ["v1.1"]

        # Argo CD aún no aplicó el commit: la solicitud sigue en validación
        argocd.apps["cliente-ferreteria"] = {"sync": "OutOfSync", "health": "Healthy", "revision": "0" * 40}
        reader = ArgoCDClient(argocd.url, argocd.token)
        assert check_cycle(seeded, reader) == []

        # Argo CD sincroniza el commit del Hub: la solicitud queda desplegada y la consola lo muestra
        argocd.apps["cliente-ferreteria"] = {
            "sync": "Synced", "health": "Healthy", "revision": change["gitops_commit_sha"],
        }
        assert check_cycle(seeded, reader) == [change["id"]]

    status = {s["namespace"]: s for s in client.get("/api/services/status").json()}["cliente-ferreteria"]
    assert status["current_version"] == "v1.1"
    assert (status["sync_status"], status["health_status"]) == ("Synced", "Healthy")
    assert status["last_author"] == seeded.scalar(select(User).where(User.role == "agencia")).name
    history = client.get(f"/api/services/{status['service_id']}/deployments").json()
    assert [(d["version"], d["source"]) for d in history] == [("v1.1", "cambio")]


@pytest.mark.skipif(
    not all(os.getenv(v) for v in ("GITEA_TEST_URL", "GITEA_TEST_TOKEN", "GITEA_TEST_REPO")),
    reason="Define GITEA_TEST_URL, GITEA_TEST_TOKEN y GITEA_TEST_REPO para probar contra un Gitea real",
)
def test_contra_gitea_local_aprobar_crea_exactamente_un_commit(client, seeded):
    url = os.environ["GITEA_TEST_URL"].rstrip("/")
    repo, token = os.environ["GITEA_TEST_REPO"], os.environ["GITEA_TEST_TOKEN"]
    gitea_client = GiteaClient(url, repo, token)

    def commits() -> list[dict]:
        request = urllib.request.Request(
            f"{url}/api/v1/repos/{repo}/commits?path={PATH}&limit=50", headers={"Authorization": f"token {token}"}
        )
        with urllib.request.urlopen(request, timeout=10) as response:  # noqa: S310
            return json.load(response)

    # El Hub se alinea con lo que tiene el repo y pide la otra versión
    tag_actual = get_tags(gitea_client.get_file(PATH).text)[0]
    destino = "v1.1" if tag_actual != "v1.1" else "v1"
    service = seeded.scalar(select(Service).where(Service.namespace == "cliente-ferreteria"))
    service.current_version = tag_actual
    seeded.commit()
    antes = commits()

    change = _pedir_y_aprobar(client, seeded, gitea_client, destino)

    despues = commits()
    assert len(despues) == len(antes) + 1
    assert despues[0]["sha"] == change["gitops_commit_sha"]
    assert despues[0]["commit"]["message"].startswith(f"chore(ferreteria): versión {destino} (cambio #")
    assert get_tags(gitea_client.get_file(PATH).text) == [destino]

# Pruebas del commit de rollback en hub-gitops: solo cambian los newTag (spec 009, T03 · CA-2).
import pytest

from app.integrations.gitea import GiteaClient, GiteaError
from app.services.gitops_publish import (
    NothingToPublish,
    find_existing_rollback,
    publish_rollback,
    publish_version,
)
from tests.fake_gitea import FakeGitea

RUTA = "clients/restaurante/kustomization.yaml"


def _kustomization(tag: str) -> str:
    return (
        "# Cliente restaurante\n"
        "apiVersion: kustomize.config.k8s.io/v1beta1\n"
        "kind: Kustomization\n"
        "namespace: cliente-restaurante\n"
        "images:\n"
        "  - name: gitea.hub.local/forja-digital/plantilla\n"
        "    newName: gitea.hub.local/forja-digital/restaurante\n"
        f"    newTag: {tag}  # versión publicada\n"
        "patches:\n"
        "  - target: { kind: Namespace }\n"
    )


@pytest.fixture
def gitea():
    with FakeGitea({RUTA: _kustomization("v1")}) as fake:
        yield fake


@pytest.fixture
def cliente(gitea):
    return GiteaClient(gitea.url, gitea.repo, gitea.token)


def test_el_rollback_deja_el_archivo_identico_al_de_la_version_de_destino(gitea, cliente):
    publish_version(cliente, "cliente-restaurante", "v2", 7, "Sofía", "sofia@forjadigital.test")
    assert gitea.files[RUTA] == _kustomization("v2")

    sha = publish_rollback(cliente, "cliente-restaurante", "v1", 3, "Sofía", "sofia@forjadigital.test")

    # Idéntico, byte a byte, al de la v1: solo cambió el newTag y los comentarios siguen
    assert gitea.files[RUTA] == _kustomization("v1")
    commit = gitea.commits[-1]
    assert commit["sha"] == sha
    assert commit["message"] == "revert(restaurante): volver a v1 (incidente #3)"
    assert commit["author"] == {"name": "Sofía", "email": "sofia@forjadigital.test"}
    assert len(gitea.commits) == 2


def test_si_git_ya_tiene_la_version_de_destino_no_hay_commit(gitea, cliente):
    with pytest.raises(NothingToPublish, match="ya tiene la versión v1"):
        publish_rollback(cliente, "cliente-restaurante", "v1", 3, "Sofía", "s@x.test")
    assert gitea.commits == []


def test_un_namespace_que_no_es_de_cliente_no_escribe_nada(gitea, cliente):
    with pytest.raises(ValueError, match="no corresponde a un cliente"):
        publish_rollback(cliente, "hub", "v1", 3, "Sofía", "s@x.test")
    assert gitea.requests == []


def test_si_gitea_falla_el_error_sube(gitea):
    malo = GiteaClient(gitea.url, gitea.repo, "otro-token")
    with pytest.raises(GiteaError):
        publish_rollback(malo, "cliente-restaurante", "v1", 3, "Sofía", "s@x.test")


def test_un_rollback_escrito_antes_de_guardarse_se_reconoce(gitea, cliente):
    publish_version(cliente, "cliente-restaurante", "v2", 7, "Sofía", "s@x.test")
    sha = publish_rollback(cliente, "cliente-restaurante", "v1", 3, "Sofía", "s@x.test")

    assert find_existing_rollback(cliente, "cliente-restaurante", "v1", 3) == sha
    # Otro incidente no puede adoptar el commit ajeno
    assert find_existing_rollback(cliente, "cliente-restaurante", "v1", 4) is None

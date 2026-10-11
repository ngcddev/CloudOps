# Pruebas del cliente de Gitea contra un Gitea falso local (spec 005, T11).
import pytest

from app.integrations.gitea import GiteaClient, GiteaError, version_commit_message
from tests.fake_gitea import FakeGitea

KUSTOMIZATION = "images:\n  - name: x\n    newTag: v1\n"
PATH = "clients/ferreteria/kustomization.yaml"


@pytest.fixture
def gitea():
    with FakeGitea({PATH: KUSTOMIZATION}) as fake:
        yield fake


def _client(fake: FakeGitea, **kwargs) -> GiteaClient:
    return GiteaClient(fake.url, fake.repo, kwargs.pop("token", fake.token), **kwargs)


def test_mensaje_del_commit():
    assert version_commit_message("ferreteria", "v1.1", 7) == "chore(ferreteria): versión v1.1 (cambio #7)"


def test_lee_un_archivo(gitea):
    file = _client(gitea).get_file(PATH)

    assert file.text == KUSTOMIZATION
    assert len(file.sha) == 40


def test_actualiza_con_exactamente_un_commit_con_mensaje_y_autor(gitea):
    client = _client(gitea)
    file = client.get_file(PATH)
    message = version_commit_message("ferreteria", "v1.1", 7)

    sha = client.update_file(
        PATH, file.text.replace("v1", "v1.1"), file.sha, message, "Sofía Técnica", "sofia@forjadigital.test"
    )

    assert len(gitea.commits) == 1
    assert gitea.commits[0]["message"] == "chore(ferreteria): versión v1.1 (cambio #7)"
    assert gitea.commits[0]["author"] == {"name": "Sofía Técnica", "email": "sofia@forjadigital.test"}
    assert sha == gitea.commits[0]["sha"]
    assert gitea.files[PATH].endswith("newTag: v1.1\n")


def test_un_sha_viejo_es_conflicto(gitea):
    client = _client(gitea)
    file = client.get_file(PATH)
    client.update_file(PATH, "images: []\n", file.sha, "primero", "A", "a@x.test")

    with pytest.raises(GiteaError) as error:
        client.update_file(PATH, "images: [1]\n", file.sha, "segundo", "A", "a@x.test")

    assert error.value.status == 409
    assert len(gitea.commits) == 1


def test_token_incorrecto_es_401(gitea):
    with pytest.raises(GiteaError) as error:
        _client(gitea, token="otro").get_file(PATH)

    assert error.value.status == 401


def test_archivo_inexistente_es_404(gitea):
    with pytest.raises(GiteaError) as error:
        _client(gitea).get_file("clients/nada.yaml")

    assert error.value.status == 404


def test_sin_conexion_explica_el_problema():
    client = GiteaClient("http://127.0.0.1:9", "forja-digital/hub-gitops", "t", timeout=1)

    with pytest.raises(GiteaError, match="No hay conexión con Gitea") as error:
        client.get_file(PATH)

    assert error.value.status is None


def test_sin_configuracion_falla_antes_de_llamar():
    with pytest.raises(GiteaError, match="no está configurado"):
        GiteaClient("", "forja-digital/hub-gitops", "")

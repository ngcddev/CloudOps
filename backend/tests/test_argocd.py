# Pruebas del cliente de Argo CD contra un Argo CD falso local (spec 005, T12).
import pytest

from app.integrations.argocd import AppStatus, ArgoCDClient, ArgoCDError
from tests.fake_argocd import FakeArgoCD

SHA = "9f2c1d0e7a8b4c5d6e7f8091a2b3c4d5e6f70812"


@pytest.fixture
def argocd():
    apps = {
        "cliente-restaurante": {"sync": "Synced", "health": "Healthy", "revision": SHA},
        "cliente-ferreteria": {"sync": "OutOfSync", "health": "Progressing", "revision": "0" * 40},
    }
    with FakeArgoCD(apps) as fake:
        yield fake


def test_lee_sincronizacion_salud_y_revision_de_la_sazon(argocd):
    status = ArgoCDClient(argocd.url, argocd.token).get_application("cliente-restaurante")

    assert status == AppStatus(sync="Synced", health="Healthy", revision=SHA)


def test_lee_una_aplicacion_pendiente(argocd):
    status = ArgoCDClient(argocd.url, argocd.token).get_application("cliente-ferreteria")

    assert (status.sync, status.health) == ("OutOfSync", "Progressing")


def test_respuesta_sin_estado_queda_como_unknown():
    def transport(request, timeout):
        return 200, b'{"metadata": {"name": "cliente-x"}}'

    status = ArgoCDClient("http://argocd.test", "t", transport=transport).get_application("cliente-x")

    assert status == AppStatus(sync="Unknown", health="Unknown", revision=None)


def test_aplicacion_inexistente_es_404(argocd):
    with pytest.raises(ArgoCDError, match="no tiene la aplicación") as error:
        ArgoCDClient(argocd.url, argocd.token).get_application("cliente-nada")

    assert error.value.status == 404


def test_token_incorrecto_es_401(argocd):
    with pytest.raises(ArgoCDError) as error:
        ArgoCDClient(argocd.url, "otro").get_application("cliente-restaurante")

    assert error.value.status == 401


def test_sin_conexion_explica_el_problema():
    client = ArgoCDClient("http://127.0.0.1:9", "t", timeout=1)

    with pytest.raises(ArgoCDError, match="No hay conexión con Argo CD"):
        client.get_application("cliente-restaurante")


def test_sin_configuracion_falla_antes_de_llamar():
    with pytest.raises(ArgoCDError, match="no está configurado"):
        ArgoCDClient("", "")

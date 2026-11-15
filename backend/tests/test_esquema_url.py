# Pruebas del esquema de las URL de las integraciones (spec 018, T01): solo http y https. urllib también abre file:// y esquemas propios, y una URL de
# configuración mal escrita no debe poder leer archivos del servidor (bandit B310).
import urllib.request

import pytest

from app.integrations import http, ollama, prometheus
from app.services.assistant_gate import RemoteGate, load_model


@pytest.mark.parametrize("url", ["file:///etc/passwd", "ftp://servidor/archivo", "gopher://x", "//sin-esquema", "javascript:alert(1)"])
def test_validar_esquema_rechaza_lo_que_no_es_http(url):
    with pytest.raises(ValueError):
        http.validar_esquema(url)


@pytest.mark.parametrize("url", ["http://gitea.gitea.svc:3000", "https://hub.local/api", "HTTP://MAYUSCULAS"])
def test_validar_esquema_acepta_http_y_https(url):
    assert http.validar_esquema(url) == url


def test_el_transporte_comun_no_abre_un_archivo_local():
    peticion = urllib.request.Request("file:///etc/passwd")

    with pytest.raises(ValueError):
        http.urllib_transport(peticion, 1.0)


def test_ollama_y_prometheus_tampoco_abren_archivos():
    with pytest.raises(ValueError):
        ollama.urllib_transport("file:///etc/passwd", b"{}", 1.0)
    with pytest.raises(ValueError):
        prometheus.urllib_transport("file:///etc/passwd", 1.0)


def test_la_compuerta_remota_rechaza_una_url_que_no_es_http():
    with pytest.raises(ValueError):
        RemoteGate("file:///etc/passwd", load_model())

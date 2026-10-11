# Transporte HTTP común de las integraciones (Gitea y Argo CD): urllib, sin dependencias nuevas.
# Las pruebas lo reemplazan por una función falsa o por un servidor local.
import urllib.error
import urllib.request
from collections.abc import Callable

# transporte(request, timeout) -> (código HTTP, cuerpo)
Transport = Callable[[urllib.request.Request, float], tuple[int, bytes]]


def urllib_transport(request: urllib.request.Request, timeout: float) -> tuple[int, bytes]:
    """Envía la petición; un error HTTP (4xx/5xx) se devuelve como código, no como excepción."""
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()

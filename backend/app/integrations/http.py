# Transporte HTTP común de las integraciones (Gitea y Argo CD): urllib, sin dependencias nuevas.
# Las pruebas lo reemplazan por una función falsa o por un servidor local.
import urllib.error
import urllib.request
from collections.abc import Callable

# transporte(request, timeout) -> (código HTTP, cuerpo)
Transport = Callable[[urllib.request.Request, float], tuple[int, bytes]]


def validate_scheme(url: str) -> str:
    """Solo http y https: urllib también abre file:// y esquemas propios, y una URL de configuración mal escrita no debe poder leer archivos (bandit B310)."""
    if not url.lower().startswith(("http://", "https://")):
        raise ValueError(f"La URL «{url[:60]}» no es http ni https.")
    return url


def urllib_transport(request: urllib.request.Request, timeout: float) -> tuple[int, bytes]:
    """Envía la petición; un error HTTP (4xx/5xx) se devuelve como código, no como excepción."""
    validate_scheme(request.full_url)
    try:
        # bandit B310: el esquema se validó arriba
        with urllib.request.urlopen(request, timeout=timeout) as response:  # nosec B310
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()

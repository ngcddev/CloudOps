# Consulta HTTP a Prometheus para los dashboards (spec 010, T09): el job `sitios` expone el Blackbox
# y el job `traefik` la latencia; la API las consulta y las convierte en KPI.
import json
import time
from collections.abc import Callable
from urllib.parse import quote

from app.config import settings

# Timeout de la consulta: si Prometheus no responde, el dashboard sigue vivo con «sin datos».
PROMETHEUS_TIMEOUT_SECONDS = 2.0
# Caché en memoria de la última respuesta por consulta y mes.
PROMETHEUS_CACHE_SECONDS = 60
_cache: dict[str, tuple[float, float | None]] = {}

# transport(url, timeout) -> (código HTTP, cuerpo)
Transport = Callable[[str, float], tuple[int, bytes]]


def urllib_transport(url: str, timeout: float) -> tuple[int, bytes]:
    """GET a la URL con urllib; un error HTTP (4xx/5xx) se devuelve como código, no como excepción."""
    import urllib.error
    import urllib.request

    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error_:
        return error_.code, error_.read()


def query(promql: str, at: str, transport: Transport = urllib_transport) -> float | None:
    """Devuelve el valor numérico de una consulta PromQL para el mes `at` (formato `YYYY-MM`).

    Si Prometheus no responde, la respuesta está vacía o hay error, devuelve `None` («sin datos»): la
    consulta nunca lanza para que la pantalla siga funcionando.
    """
    key = f"{at}|{promql}"
    ahora = time.monotonic()
    cacheada = _cache.get(key)
    if cacheada is not None and cacheada[0] > ahora:
        return cacheada[1]

    url = f"{settings.prometheus_url}/api/v1/query?query={quote(promql)}"
    valor = None
    try:
        status, body = transport(url, PROMETHEUS_TIMEOUT_SECONDS)
        if status == 200:
            payload = json.loads(body)
            resultados = payload.get("data", {}).get("result") or []
            if resultados:
                valor = float(resultados[0]["value"][1])
    except Exception:
        valor = None

    _cache[key] = (ahora + PROMETHEUS_CACHE_SECONDS, valor)
    return valor

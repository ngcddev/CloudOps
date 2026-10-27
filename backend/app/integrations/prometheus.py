# Consulta HTTP a Prometheus para los dashboards (spec 010, T09 y T11): el job `sitios` expone el
# Blackbox y el job `traefik` la latencia; la API las consulta y las convierte en KPI y series.
import json
import time
from collections.abc import Callable
from datetime import datetime, timezone
from urllib.parse import quote

from app.config import settings

# Timeout de la consulta: si Prometheus no responde, el dashboard sigue vivo con «sin datos».
PROMETHEUS_TIMEOUT_SECONDS = 2.0
# Caché en memoria de la última respuesta por consulta y mes.
PROMETHEUS_CACHE_SECONDS = 60
_cache: dict[str, tuple[float, object]] = {}

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


def query(promql: str, at: str, transport: Transport | None = None) -> float | None:
    """Devuelve el valor numérico de una consulta PromQL para el mes `at` (formato `YYYY-MM`).

    Si Prometheus no responde, la respuesta está vacía o hay error, devuelve `None` («sin datos»): la
    consulta nunca lanza para que la pantalla siga funcionando.
    """
    key = f"{at}|{promql}"
    ahora = time.monotonic()
    cacheada = _cache.get(key)
    if cacheada is not None and cacheada[0] > ahora:
        return cacheada[1]  # type: ignore[return-value]

    transport = transport or urllib_transport
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


def _unix(valor: datetime) -> float:
    """Segundos desde epoch; Prometheus recibe las fechas así."""
    if valor.tzinfo is None:
        valor = valor.replace(tzinfo=timezone.utc)
    return valor.timestamp()


def query_range(
    promql: str,
    start: datetime,
    end: datetime,
    step_seconds: int = 300,
    transport: Transport | None = None,
) -> list[tuple[datetime, float]] | None:
    """Puntos de una consulta PromQL entre `start` y `end`, cada `step_seconds` (5 min por omisión).

    Devuelve `None` si Prometheus falla (la gráfica muestra «sin datos») y `[]` si no hay serie.
    """
    key = f"range|{_unix(start)}|{_unix(end)}|{step_seconds}|{promql}"
    ahora = time.monotonic()
    cacheada = _cache.get(key)
    if cacheada is not None and cacheada[0] > ahora:
        return cacheada[1]  # type: ignore[return-value]

    transport = transport or urllib_transport
    url = (
        f"{settings.prometheus_url}/api/v1/query_range?query={quote(promql)}"
        f"&start={_unix(start):.0f}&end={_unix(end):.0f}&step={step_seconds}"
    )
    puntos: list[tuple[datetime, float]] | None = None
    try:
        status, body = transport(url, PROMETHEUS_TIMEOUT_SECONDS)
        if status == 200:
            payload = json.loads(body)
            resultados = payload.get("data", {}).get("result") or []
            puntos = []
            if resultados:
                for marca, valor in resultados[0].get("values") or []:
                    puntos.append(
                        (datetime.fromtimestamp(float(marca), tz=timezone.utc), float(valor))
                    )
    except Exception:
        puntos = None

    _cache[key] = (ahora + PROMETHEUS_CACHE_SECONDS, puntos)
    return puntos

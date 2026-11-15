# Consulta HTTP a Loki (spec 019, T05): las últimas líneas de registro de los Pods de un namespace de cliente, para darle evidencia a la IA que ayuda
# a diagnosticar un incidente. Igual que las demás integraciones, nunca lanza: sin Loki (URL vacía) o con un error devuelve una lista vacía.
import json
from collections.abc import Callable
from urllib.parse import quote

from app.config import settings
from app.integrations.prometheus import urllib_transport

LOKI_TIMEOUT_SECONDS = 3.0
MAX_LINEAS = 15
MAX_LARGO_LINEA = 220

# transport(url, timeout) -> (código HTTP, cuerpo)
Transport = Callable[[str, float], tuple[int, bytes]]


def lineas(namespace: str, desde_ns: int, hasta_ns: int, transport: Transport | None = None) -> list[str]:
    """Líneas de registro del namespace entre dos instantes (nanosegundos desde 1970), de la más vieja a la más nueva; recortadas."""
    if not settings.loki_url:
        return []
    consulta = quote(f'{{namespace="{namespace}"}}')
    url = f"{settings.loki_url}/loki/api/v1/query_range?query={consulta}&start={desde_ns}&end={hasta_ns}&limit={MAX_LINEAS}&direction=backward"
    try:
        status, cuerpo = (transport or urllib_transport)(url, LOKI_TIMEOUT_SECONDS)
        if status != 200:
            return []
        encontradas: list[tuple[int, str]] = []
        for flujo in json.loads(cuerpo).get("data", {}).get("result", []):
            encontradas += [(int(ts), linea.strip()[:MAX_LARGO_LINEA]) for ts, linea in flujo.get("values", []) if linea.strip()]
        return [linea for _, linea in sorted(encontradas)][-MAX_LINEAS:]
    except Exception:
        return []

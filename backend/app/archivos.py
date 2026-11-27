# Lectura de archivos pequeños con caché por fecha de modificación (spec 022, T34; auditoría BE-10): los términos prohibidos, los parámetros de KPI y el prompt del asistente se
# leían del disco en cada llamada (una por cliente en el tablero). Se vuelven a leer solo si el archivo cambia, así que editarlos en caliente sigue funcionando.
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

T = TypeVar("T")
_cache: dict[tuple[str, Callable], tuple[tuple[int, int], object]] = {}


def read_cached(ruta: Path, transformar: Callable[[str], T]) -> T:
    """`transformar(texto)` del archivo, calculado una vez por versión del archivo (fecha y tamaño). Si el archivo no existe, lanza OSError como `read_text`."""
    estado = ruta.stat()
    version = (estado.st_mtime_ns, estado.st_size)
    clave = (str(ruta), transformar)
    guardado = _cache.get(clave)
    if guardado is not None and guardado[0] == version:
        return guardado[1]  # type: ignore[return-value]
    valor = transformar(ruta.read_text(encoding="utf-8"))
    _cache[clave] = (version, valor)
    return valor

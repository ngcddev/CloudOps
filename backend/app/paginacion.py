# Paginación común de los listados (spec 022, T19; auditoría BE-04): `limit` (por defecto 100, máximo 500) y `offset`. La respuesta sigue siendo una lista,
# así que el frontend no cambia; solo deja de recibir todas las filas cuando la tabla crece.
from dataclasses import dataclass

from fastapi import Query

DEFAULT_LIMIT = 100
MAX_LIMIT = 500


@dataclass(frozen=True)
class Page:
    limit: int
    offset: int


def paginate(
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT, description="Filas por página (máximo 500)."),
    offset: int = Query(default=0, ge=0, description="Filas a saltar."),
) -> Page:
    return Page(limit=limit, offset=offset)

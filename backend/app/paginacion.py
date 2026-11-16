# Paginación común de los listados (spec 022, T19; auditoría BE-04): `limit` (por defecto 100, máximo 500) y `offset`. La respuesta sigue siendo una lista,
# así que el frontend no cambia; solo deja de recibir todas las filas cuando la tabla crece.
from dataclasses import dataclass

from fastapi import Query

LIMITE_POR_DEFECTO = 100
LIMITE_MAXIMO = 500


@dataclass(frozen=True)
class Pagina:
    limit: int
    offset: int


def pagina(
    limit: int = Query(default=LIMITE_POR_DEFECTO, ge=1, le=LIMITE_MAXIMO, description="Filas por página (máximo 500)."),
    offset: int = Query(default=0, ge=0, description="Filas a saltar."),
) -> Pagina:
    return Pagina(limit=limit, offset=offset)

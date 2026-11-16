# Candados de PostgreSQL para que varias réplicas de la API no repitan trabajo (auditoría K8-04): el vigilante de Argo CD corre en una sola a la vez, y
# las migraciones y la semilla del arranque esperan su turno. Son candados de sesión sobre una conexión aparte y en modo AUTOCOMMIT: no abren transacción
# (así el tiempo límite de transacciones inactivas no los suelta) y los libera la base sola si la réplica muere. Con SQLite (pruebas) no hacen nada.
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

CLAVE_ARRANQUE = 7_022_001    # migraciones y semilla
CLAVE_VIGILANTE = 7_022_002   # una vuelta del seguimiento de Argo CD
CLAVE_REINDEXAR = 7_022_003   # reemplazo del índice del RAG (auditoría BE-07)


def _usa_candados(engine: Engine) -> bool:
    return engine.dialect.name == "postgresql"


@contextmanager
def esperar_turno(engine: Engine, clave: int) -> Iterator[None]:
    """Espera su turno (sin límite) y lo retiene dentro del bloque: quien llegue después espera a que termine."""
    if not _usa_candados(engine):
        yield
        return
    with engine.connect() as conexion:
        conexion.execution_options(isolation_level="AUTOCOMMIT")
        conexion.execute(text("SELECT pg_advisory_lock(:clave)"), {"clave": clave})
        try:
            yield
        finally:
            conexion.execute(text("SELECT pg_advisory_unlock(:clave)"), {"clave": clave})


@contextmanager
def turno_si_libre(engine: Engine, clave: int) -> Iterator[bool]:
    """Toma el turno si nadie lo tiene y dice si lo consiguió; quien no lo consigue no espera: se salta el trabajo."""
    if not _usa_candados(engine):
        yield True
        return
    with engine.connect() as conexion:
        conexion.execution_options(isolation_level="AUTOCOMMIT")
        tomado = bool(conexion.execute(text("SELECT pg_try_advisory_lock(:clave)"), {"clave": clave}).scalar())
        try:
            yield tomado
        finally:
            if tomado:
                conexion.execute(text("SELECT pg_advisory_unlock(:clave)"), {"clave": clave})


def candado_de_transaccion(db: Session, clave: int) -> None:
    """Toma un candado que dura lo que la transacción de la sesión (se suelta solo al confirmar o deshacer): quien llegue después espera a que ella termine.

    A diferencia de `esperar_turno`, va en la misma transacción que las escrituras que protege. Con SQLite (pruebas) no hace nada.
    """
    if _usa_candados(db.get_bind()):
        db.execute(text("SELECT pg_advisory_xact_lock(:clave)"), {"clave": clave})

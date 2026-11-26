# Conexión a PostgreSQL: engine, sesión, Base de los modelos y get_db() para los endpoints.
from collections.abc import Iterator

from sqlalchemy import JSON, create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


def engine_options(url: str) -> dict:
    """Opciones de `create_engine` según la base. Solo PostgreSQL recibe el pool y los tiempos límite: SQLite (pruebas y scripts de ai/) usa otro
    tipo de pool que no admite esos argumentos."""
    opciones: dict = {"pool_pre_ping": True}
    if url.startswith("postgresql"):
        opciones.update(
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_timeout=settings.db_pool_timeout,
            connect_args={
                "options": f"-c statement_timeout={settings.db_statement_timeout_ms} "
                f"-c idle_in_transaction_session_timeout={settings.db_idle_in_transaction_timeout_ms}"
            },
        )
    return opciones


engine = create_engine(settings.database_url, **engine_options(settings.database_url))
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    pass


# Columnas de documentos: `jsonb` en PostgreSQL (se puede indexar y consultar por contenido, y no se vuelve a analizar el texto en cada lectura) y `JSON` en SQLite,
# que usan las pruebas (auditoría BD-04). La migración 0017 las convierte en la base real.
JSON_DOC = JSON().with_variant(JSONB(), "postgresql")


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def release_connection(db: Session) -> None:
    """Termina la transacción de lectura y devuelve la conexión al pool antes de una llamada lenta (Ollama, Gitea…), para que esperar no sostenga
    una conexión (auditoría BE-02). Los objetos cargados quedan caducados: guarde antes lo que vaya a necesitar. Falla si hay cambios sin guardar,
    para no tirarlos en silencio."""
    if db.new or db.dirty or db.deleted:
        raise RuntimeError("Hay cambios sin guardar: guárdelos (commit) antes de soltar la conexión.")
    db.rollback()

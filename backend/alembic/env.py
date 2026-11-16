# Entorno de Alembic: toma DATABASE_URL de la configuración de la API y los modelos de app.models.
from alembic import context
from sqlalchemy import create_engine

from app import models  # noqa: F401  (registra los modelos en Base.metadata)
from app.config import settings
from app.db import Base
from app.services.bloqueos import CLAVE_ARRANQUE, esperar_turno

target_metadata = Base.metadata


def run_migrations_online() -> None:
    """Aplica las migraciones contra la base real."""
    # Las pruebas pasan su propia conexión (sqlite en memoria) por config.attributes.
    connection = context.config.attributes.get("connection")
    if connection is not None:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
        return
    engine = create_engine(settings.database_url)
    # Varias réplicas arrancan a la vez (HPA, actualización continua): migran de a una; la que llega después ya no encuentra nada que hacer (auditoría K8-04)
    with esperar_turno(engine, CLAVE_ARRANQUE), engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()

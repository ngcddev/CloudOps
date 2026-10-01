# Entorno de Alembic: toma DATABASE_URL de la configuración de la API y los modelos de app.models.
from alembic import context
from sqlalchemy import create_engine

from app import models  # noqa: F401  (registra los modelos en Base.metadata)
from app.config import settings
from app.db import Base

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
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()

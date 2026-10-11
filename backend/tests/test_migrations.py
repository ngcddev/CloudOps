# Prueba de las migraciones de Alembic: sube y baja sobre una base vacía (specs 001 y 004).
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

BACKEND = Path(__file__).resolve().parents[1]
TABLES = {
    "agencies",
    "plans",
    "sla_policies",
    "clients",
    "projects",
    "services",
    "users",
    "tickets",
    "ticket_events",
    "work_logs",
}


def _config(connection) -> Config:
    config = Config(str(BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND / "alembic"))
    config.attributes["connection"] = connection
    return config


def test_upgrade_creates_all_tables_and_downgrade_removes_them():
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        command.upgrade(_config(connection), "head")
        assert TABLES <= set(inspect(connection).get_table_names())

        command.downgrade(_config(connection), "-1")
        remaining_tables = set(inspect(connection).get_table_names())
        assert not {"tickets", "ticket_events", "work_logs"} & remaining_tables
        assert {"agencies", "plans", "sla_policies", "clients", "projects", "services", "users"} <= remaining_tables

        command.downgrade(_config(connection), "base")
        assert not TABLES & set(inspect(connection).get_table_names())

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
    "change_requests",
    "deployments",
    "audit_logs",
    "security_runs",
    "security_checks",
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

        service_columns = {c["name"] for c in inspect(connection).get_columns("services")}
        assert {"current_version", "stable_version", "sync_status", "health_status"} <= service_columns
        assert {"password_hash", "is_active", "last_login_at"} <= {
            c["name"] for c in inspect(connection).get_columns("users")
        }

        # 0007 (spec 006): quita las corridas y los controles de seguridad
        command.downgrade(_config(connection), "-1")
        assert not {"security_runs", "security_checks"} & set(inspect(connection).get_table_names())
        assert "audit_logs" in set(inspect(connection).get_table_names())

        # 0006 (spec 007): quita la bitácora
        command.downgrade(_config(connection), "-1")
        assert "audit_logs" not in set(inspect(connection).get_table_names())

        # 0005 (spec 007): quita las columnas de sesión de users
        command.downgrade(_config(connection), "-1")
        user_columns = {c["name"] for c in inspect(connection).get_columns("users")}
        assert not {"password_hash", "is_active", "last_login_at"} & user_columns
        assert "email" in user_columns

        # 0004 (spec 005): quita las tablas de cambios y las columnas nuevas de services
        command.downgrade(_config(connection), "-1")
        remaining_tables = set(inspect(connection).get_table_names())
        assert not {"change_requests", "deployments"} & remaining_tables
        service_columns = {c["name"] for c in inspect(connection).get_columns("services")}
        assert not {"current_version", "stable_version", "sync_status", "health_status"} & service_columns
        assert {"tickets", "ticket_events", "work_logs"} <= remaining_tables

        command.downgrade(_config(connection), "-1")
        remaining_tables = set(inspect(connection).get_table_names())
        assert not {"tickets", "ticket_events", "work_logs"} & remaining_tables
        assert {"agencies", "plans", "sla_policies", "clients", "projects", "services", "users"} <= remaining_tables

        command.downgrade(_config(connection), "base")
        assert not TABLES & set(inspect(connection).get_table_names())

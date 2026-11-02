# Prueba de las migraciones de Alembic: sube y baja sobre una base vacía (specs 001 y 004).
from pathlib import Path

from alembic import command
from alembic.config import Config
import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

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
    "incidents",
    "incident_events",
    "ai_drafts",
    "reports",
}


ROLLBACK_COLUMNS = {
    "rollback_from_version",
    "rollback_to_version",
    "rollback_commit_sha",
    "rollback_by_id",
    "rollback_at",
    "rollback_confirmed_at",
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

        # 0011 (spec 013): quita los reportes; los borradores de la 012 siguen ahí
        command.downgrade(_config(connection), "-1")
        assert "reports" not in set(inspect(connection).get_table_names())
        assert "ai_drafts" in set(inspect(connection).get_table_names())

        # 0010 (spec 012): quita los borradores; los incidentes y su rollback siguen ahí
        command.downgrade(_config(connection), "-1")
        assert "ai_drafts" not in set(inspect(connection).get_table_names())
        assert "incidents" in set(inspect(connection).get_table_names())

        # 0009 (spec 009): quita las columnas del rollback; los incidentes de la 008 siguen ahí
        incident_columns = {c["name"] for c in inspect(connection).get_columns("incidents")}
        assert ROLLBACK_COLUMNS <= incident_columns
        command.downgrade(_config(connection), "-1")
        incident_columns = {c["name"] for c in inspect(connection).get_columns("incidents")}
        assert not ROLLBACK_COLUMNS & incident_columns
        assert {"incidents", "incident_events"} <= set(inspect(connection).get_table_names())
        assert "mitigated_at" in incident_columns

        # 0008 (spec 008): quita los incidentes y su línea de tiempo
        command.downgrade(_config(connection), "-1")
        assert not {"incidents", "incident_events"} & set(inspect(connection).get_table_names())
        assert "security_runs" in set(inspect(connection).get_table_names())

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


def _insert_incident(connection, fingerprint: str | None, status: str = "abierto") -> None:
    connection.execute(
        text(
            "INSERT INTO incidents (service_id, priority, status, source, fingerprint, title, started_at,"
            " response_due_at, resolution_due_at)"
            " VALUES (1, 'P1', :status, 'alerta', :fingerprint, 'Sitio caído', :at, :at, :at)"
        ),
        {"status": status, "fingerprint": fingerprint, "at": "2026-10-24 14:00:00+00:00"},
    )


def test_0008_no_deja_dos_incidentes_abiertos_con_el_mismo_fingerprint():
    """El índice único parcial de la migración 0008 (spec 008, T01 · CA-3)."""
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        command.upgrade(_config(connection), "head")
        _insert_incident(connection, "abc123")
        _insert_incident(connection, "otro")
        # Uno ya mitigado con la misma huella no estorba: la falla volvió y es un incidente nuevo
        _insert_incident(connection, "otro", status="mitigado")
        # Los manuales no tienen huella y pueden ser varios
        _insert_incident(connection, None)
        _insert_incident(connection, None)

        with pytest.raises(IntegrityError):
            with connection.begin_nested():
                _insert_incident(connection, "abc123")

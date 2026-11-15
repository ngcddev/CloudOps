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
    "ai_queries",
    "kb_documents",
    "kb_chunks",
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

        # 0015 (spec 022, T06): quita los índices de las claves foráneas y los dos únicos; las tablas siguen
        nuevos = {
            "tickets": {"ix_tickets_service_id", "ix_tickets_created_at"},
            "ticket_events": {"ix_ticket_events_ticket_id"},
            "work_logs": {"ix_work_logs_ticket_id", "ix_work_logs_user_id"},
            "change_requests": {"ix_change_requests_service_status", "ix_change_requests_ticket_id", "uq_change_requests_open_per_service"},
            "deployments": {"ix_deployments_service_id_id"},
            "services": {"ix_services_project_id"},
            "projects": {"ix_projects_client_id"},
            "users": {"ix_users_client_id"},
            "security_checks": {"uq_security_checks_run_step_image"},
        }
        indices = {
            nombre: {fila[0] for fila in connection.execute(text("SELECT name FROM sqlite_master WHERE type = 'index' AND tbl_name = :t"), {"t": nombre})}
            for nombre in nuevos
        }
        assert all(esperados <= indices[tabla] for tabla, esperados in nuevos.items())
        command.downgrade(_config(connection), "-1")
        indices = {
            nombre: {fila[0] for fila in connection.execute(text("SELECT name FROM sqlite_master WHERE type = 'index' AND tbl_name = :t"), {"t": nombre})}
            for nombre in nuevos
        }
        assert all(not (esperados & indices[tabla]) for tabla, esperados in nuevos.items())
        assert TABLES <= set(inspect(connection).get_table_names())

        # 0014 (spec 013): quita los reportes; lo anterior sigue ahí
        assert "reports" in set(inspect(connection).get_table_names())
        command.downgrade(_config(connection), "-1")
        assert "reports" not in set(inspect(connection).get_table_names())

        # 0013 (spec 012): quita los borradores del asistente; lo anterior sigue ahí
        assert "ai_drafts" in set(inspect(connection).get_table_names())
        command.downgrade(_config(connection), "-1")
        assert "ai_drafts" not in set(inspect(connection).get_table_names())

        # 0012 (spec 012): quita la base de conocimiento del RAG y las dos columnas de ai_queries; la tabla sigue
        consultas = {c["name"] for c in inspect(connection).get_columns("ai_queries")}
        assert {"context_mode", "retrieval_score", "context_sections"} <= consultas
        command.downgrade(_config(connection), "-1")
        consultas = {c["name"] for c in inspect(connection).get_columns("ai_queries")}
        assert not {"context_mode", "retrieval_score"} & consultas and "context_sections" in consultas
        assert not {"kb_documents", "kb_chunks"} & set(inspect(connection).get_table_names())

        # 0011 (spec 012): quita las secciones de ayuda de cada consulta; la tabla sigue
        assert "context_sections" in {c["name"] for c in inspect(connection).get_columns("ai_queries")}
        command.downgrade(_config(connection), "-1")
        assert "context_sections" not in {c["name"] for c in inspect(connection).get_columns("ai_queries")}

        # 0010 (spec 012): quita el registro de preguntas al asistente
        command.downgrade(_config(connection), "-1")
        assert "ai_queries" not in set(inspect(connection).get_table_names())

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


def test_0015_se_detiene_con_un_mensaje_claro_si_ya_hay_cambios_abiertos_repetidos():
    """Un índice único no se crea sobre datos que ya lo violan: la migración dice cuáles son (spec 022, T06)."""
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        command.upgrade(_config(connection), "0014")
        connection.execute(text(
            "INSERT INTO change_requests (ticket_id, service_id, from_version, to_version, status)"
            " VALUES (1, 7, 'v1', 'v1.1', 'pendiente'), (2, 7, 'v1', 'v1.2', 'en_validacion'),"
            " (3, 8, 'v1', 'v1.1', 'pendiente'), (4, 7, 'v1', 'v1.3', 'desplegada')"
        ))
        with pytest.raises(RuntimeError, match="duplicados") as error:
            command.upgrade(_config(connection), "head")
        assert "(7, 2)" in str(error.value) and "(8," not in str(error.value)


def test_0015_acepta_controles_distintos_y_se_detiene_si_hay_repetidos():
    insertar = "INSERT INTO security_checks (run_id, step, image, status, summary) VALUES (:r, :s, :i, 'ok', '')"
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        command.upgrade(_config(connection), "0014")
        connection.execute(text(insertar), [{"r": 1, "s": "secretos", "i": None}, {"r": 1, "s": "sbom", "i": "a"}, {"r": 1, "s": "sbom", "i": "b"}])
        command.upgrade(_config(connection), "head")   # sin repetidos: no se queja
        # Con NULL pasa lo mismo que con una imagen: dos controles de secretos en la misma corrida chocan
        with pytest.raises(IntegrityError):
            with connection.begin_nested():
                connection.execute(text(insertar), {"r": 1, "s": "secretos", "i": None})

    with engine.begin() as connection:
        command.downgrade(_config(connection), "0014")
        connection.execute(text(insertar), {"r": 1, "s": "secretos", "i": None})   # ya repetido
        with pytest.raises(RuntimeError, match=r"duplicados.*secretos"):
            command.upgrade(_config(connection), "head")

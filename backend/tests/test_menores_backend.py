# Hallazgos menores del backend y la base de datos (spec 022, T34): BD-04 a BD-08, BE-09 a BE-12 y BE-15 a BE-18.
import os
import time
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.archivos import leer_con_cache
from app.integrations import prometheus
from app.integrations.argocd import ArgoCDClient, ArgoCDError
from app.integrations.gitea import GiteaClient, GiteaError
from app.models import User
from app.schemas.client import ClientCreate
from app.schemas.ticket import WorkLogCreate


# ---------- BE-12: una respuesta que no es JSON es un error de la integración, no un 500 ----------


def test_gitea_con_una_respuesta_que_no_es_json_lanza_gitea_error():
    cliente = GiteaClient("http://gitea.test", "org/repo", "token", transport=lambda request, timeout: (200, b"<html>502 Bad Gateway</html>"))
    with pytest.raises(GiteaError, match="no es JSON"):
        cliente.head_sha()


def test_argocd_con_una_respuesta_que_no_es_json_lanza_argocd_error():
    cliente = ArgoCDClient("http://argocd.test", "token", transport=lambda request, timeout: (200, b"<html>proxy</html>"))
    with pytest.raises(ArgoCDError, match="no es JSON"):
        cliente.get_application("cliente-restaurante")


# ---------- BE-11: la caché de Prometheus tiene tope ----------


def test_la_cache_de_prometheus_no_pasa_de_su_tope_y_conserva_lo_vigente(monkeypatch):
    monkeypatch.setattr(prometheus, "MAX_ENTRADAS_CACHE", 5)
    prometheus._cache.clear()
    ahora = time.monotonic()
    prometheus._guardar("vencida", ahora - 10, 1.0)
    for i in range(10):
        prometheus._guardar(f"viva-{i}", ahora + 60 + i, float(i))
    assert len(prometheus._cache) <= 5
    assert "vencida" not in prometheus._cache and "viva-9" in prometheus._cache   # lo más nuevo se queda; lo vencido y lo más viejo salen


# ---------- BE-10: lectura de archivos con caché por fecha ----------


def test_un_archivo_se_lee_una_vez_y_otra_vez_solo_si_cambia(tmp_path):
    ruta = tmp_path / "terminos.txt"
    ruta.write_text("uno\ndos\n", encoding="utf-8")
    llamadas = []

    def transformar(texto: str) -> list[str]:
        llamadas.append(1)
        return texto.split()

    assert leer_con_cache(ruta, transformar) == ["uno", "dos"] and leer_con_cache(ruta, transformar) == ["uno", "dos"]
    assert len(llamadas) == 1   # la segunda lectura salió de la caché
    ruta.write_text("uno\ndos\ntres\n", encoding="utf-8")
    assert leer_con_cache(ruta, transformar) == ["uno", "dos", "tres"] and len(llamadas) == 2   # editarlo en caliente sigue funcionando


def test_un_archivo_que_no_existe_lanza_oserror_como_read_text(tmp_path):
    with pytest.raises(OSError):
        leer_con_cache(tmp_path / "no-existe.txt", str)


# ---------- BE-15: horas y correo ----------


@pytest.mark.parametrize("horas", ["0", "-1", "24.01", "25", "1000000", "1.234"])
def test_las_horas_fuera_de_rango_o_con_mas_de_dos_decimales_se_rechazan(horas):
    with pytest.raises(ValueError):
        WorkLogCreate(hours=Decimal(horas))


@pytest.mark.parametrize("horas", ["0.25", "1.5", "8", "24"])
def test_las_horas_razonables_se_aceptan(horas):
    assert WorkLogCreate(hours=Decimal(horas)).hours == Decimal(horas)


@pytest.mark.parametrize("correo", ["sin-arroba", "dos@@x.com", "con espacio@x.com", "a@b", "@x.com"])
def test_un_correo_sin_forma_de_correo_se_rechaza(correo):
    with pytest.raises(ValueError):
        ClientCreate(name="Cliente", email=correo)


def test_un_correo_con_forma_de_correo_o_vacio_se_acepta():
    assert ClientCreate(name="Cliente", email="contacto@cliente.test").email == "contacto@cliente.test"
    assert ClientCreate(name="Cliente", email="  ").email is None and ClientCreate(name="Cliente").email is None


def test_el_api_responde_422_con_un_correo_malo(as_agency):
    assert as_agency.post("/api/clients", json={"name": "Cliente nuevo", "email": "no-es-correo"}).status_code == 422
    assert as_agency.post("/api/clients", json={"name": "Cliente nuevo", "email": "ok@cliente.test"}).status_code == 201


# ---------- BD-07: el correo es único sin distinguir mayúsculas ----------


def test_dos_correos_que_solo_se_distinguen_por_mayusculas_no_pueden_coexistir(db):
    db.add(User(name="Ana", email="Ana@x.test", role="agencia"))
    db.commit()
    db.add(User(name="Otra Ana", email="ana@x.test", role="agencia"))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
    assert [u.email for u in db.scalars(select(User))] == ["Ana@x.test"]


# ---------- BE-18 y BE-17: consultas sin joins ni cargas perezosas de más ----------


def test_los_tickets_se_filtran_por_cliente_sin_unir_la_tabla_de_clientes(as_agency, seeded):
    from sqlalchemy import event

    consultas: list[str] = []
    motor = seeded.get_bind()

    def registrar(conn, cursor, statement, *args):
        consultas.append(statement)

    event.listen(motor, "before_cursor_execute", registrar)
    try:
        as_agency.get("/api/tickets?client_id=1")
    finally:
        event.remove(motor, "before_cursor_execute", registrar)
    sql = " ".join(c for c in consultas if "FROM tickets" in c)
    assert sql and "JOIN clients" not in sql and "projects.client_id" in sql


def test_el_detalle_del_cliente_trae_proyectos_servicios_y_planes_en_bloque(as_agency, seeded):
    from sqlalchemy import event

    consultas: list[str] = []
    motor = seeded.get_bind()

    def registrar(conn, cursor, statement, *args):
        consultas.append(statement)

    event.listen(motor, "before_cursor_execute", registrar)
    try:
        respuesta = as_agency.get("/api/clients/1")
    finally:
        event.remove(motor, "before_cursor_execute", registrar)
    assert respuesta.status_code == 200 and respuesta.json()["projects"][0]["services"][0]["plan"]
    assert len([c for c in consultas if "FROM plans" in c]) == 1   # un solo SELECT de planes, no uno por servicio


# ---------- BD-04, BD-06: los modelos declaran lo que la base tiene ----------


def test_las_columnas_de_documentos_son_jsonb_en_postgresql():
    from sqlalchemy.dialects import postgresql

    from app.models import AuditLog, Report, SecurityCheck

    for columna in (AuditLog.__table__.c.details, Report.__table__.c.data, SecurityCheck.__table__.c.report):
        assert columna.type.dialect_impl(postgresql.dialect()).__class__.__name__.endswith("JSONB")


def test_los_indices_que_solo_estaban_en_las_migraciones_ahora_estan_en_los_modelos():
    from app.db import Base

    esperados = {
        "ix_audit_logs_created_at", "ix_audit_logs_entity", "ix_incidents_service_status", "ix_incident_events_incident",
        "ix_security_runs_service_version", "ix_security_checks_run", "ix_ai_queries_created_at", "uq_users_email_lower",
    }
    declarados = {i.name for t in Base.metadata.tables.values() for i in t.indexes}
    assert esperados <= declarados, esperados - declarados


@pytest.mark.skipif(not os.environ.get("TEST_POSTGRES_URL"), reason="TEST_POSTGRES_URL no está definida (hace falta un PostgreSQL desechable)")
def test_alembic_check_no_ve_diferencias_entre_los_modelos_y_las_migraciones_en_postgresql():
    """Contra PostgreSQL de verdad (en SQLite las columnas NOT NULL y los índices de expresión no se pueden comparar): con los índices en los modelos y
    `compare_type`, `--autogenerate` no propone borrar ni cambiar nada. La corre quien tenga un PostgreSQL desechable; en CI se omite."""
    from alembic import command
    from sqlalchemy import create_engine, text

    from tests.test_migrations import _config

    motor = create_engine(os.environ["TEST_POSTGRES_URL"])
    with motor.begin() as conexion:
        conexion.execute(text("DROP SCHEMA public CASCADE"))
        conexion.execute(text("CREATE SCHEMA public"))
    with motor.connect() as conexion:
        config = _config(conexion)
        command.upgrade(config, "head")
        command.check(config)   # lanza CommandError si hay diferencias

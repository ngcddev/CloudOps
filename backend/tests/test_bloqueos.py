# Candados de PostgreSQL entre réplicas (spec 022, T08; auditoría K8-04). Con SQLite (estas pruebas) no hacen nada y no estorban; lo que hacen de verdad se
# prueba contra PostgreSQL (ver la bitácora). Aquí: que no estorban, que el vigilante salta la vuelta si otra réplica la tiene y que el arranque los usa.
import asyncio
from contextlib import contextmanager
from pathlib import Path

import pytest
from sqlalchemy import create_engine

from app.services import bloqueos, deploy_watch

RAIZ = Path(__file__).resolve().parents[1]


def test_con_sqlite_los_candados_no_hacen_nada():
    motor = create_engine("sqlite://")

    with bloqueos.esperar_turno(motor, 1):
        pass
    with bloqueos.turno_si_libre(motor, 1) as primero, bloqueos.turno_si_libre(motor, 1) as segundo:
        assert primero is True and segundo is True   # sin candado nadie queda fuera


def test_las_claves_de_los_candados_son_distintas():
    assert bloqueos.CLAVE_ARRANQUE != bloqueos.CLAVE_VIGILANTE


def _correr_el_vigilante(session_factory, monkeypatch, turno_libre: bool) -> int:
    vueltas = []

    @contextmanager
    def turno(engine, clave):
        assert clave == bloqueos.CLAVE_VIGILANTE
        yield turno_libre

    monkeypatch.setattr(deploy_watch, "turno_si_libre", turno)
    monkeypatch.setattr(deploy_watch, "check_cycle", lambda db, argocd, gitea=None: vueltas.append(1))

    async def correr():
        tarea = asyncio.create_task(deploy_watch.watch_forever(session_factory, object(), interval=0.01))
        await asyncio.sleep(0.15)
        tarea.cancel()
        try:
            await tarea
        except asyncio.CancelledError:
            pass

    asyncio.run(correr())
    return len(vueltas)


def test_el_vigilante_hace_la_vuelta_cuando_tiene_el_turno(session_factory, monkeypatch):
    assert _correr_el_vigilante(session_factory, monkeypatch, turno_libre=True) >= 2


def test_el_vigilante_salta_la_vuelta_si_otra_replica_la_tiene(session_factory, monkeypatch):
    assert _correr_el_vigilante(session_factory, monkeypatch, turno_libre=False) == 0


def test_la_api_arranca_de_verdad_con_el_candado_de_arranque(session_factory, monkeypatch):
    """Ejecuta el `lifespan` completo (clave, candado, semilla): un nombre sin importar en main.py solo se ve al arrancar, no al importar."""
    from fastapi.testclient import TestClient

    from app import main
    from app.models import Client

    monkeypatch.setattr(main, "SessionLocal", session_factory)   # las tablas de la prueba, no la base global sin tablas

    with TestClient(main.app):
        pass

    with session_factory() as db:
        assert db.query(Client).count() == 3   # la semilla corrió dentro del turno


def test_alembic_usa_el_mismo_candado_de_arranque():
    # Una réplica migra y las demás esperan: el mismo candado que la semilla del arranque
    assert "esperar_turno(engine, CLAVE_ARRANQUE)" in (RAIZ / "alembic" / "env.py").read_text(encoding="utf-8")


DOCKERFILE = Path("/repo/backend/Dockerfile")   # el Dockerfile no entra a la imagen: se lee del repositorio montado


@pytest.mark.skipif(not DOCKERFILE.exists(), reason="el repositorio no está montado en /repo")
def test_el_contenedor_recibe_sigterm_en_uvicorn():
    comandos = [l for l in DOCKERFILE.read_text(encoding="utf-8").splitlines() if l.startswith("CMD")]
    assert len(comandos) == 2 and all("&& exec uvicorn" in c for c in comandos)

# Utilidades compartidas de las pruebas de la API: base SQLite en memoria y cliente HTTP.
import os

# Las pruebas nunca tocan la base real: se fuerza SQLite antes de importar la app.
os.environ["DATABASE_URL"] = "sqlite://"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.db import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Plan  # noqa: E402
from app.seed import seed_if_empty  # noqa: E402


@pytest.fixture
def session_factory():
    """Base nueva en memoria para cada prueba, con todas las tablas creadas."""
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, autoflush=False)
    engine.dispose()


@pytest.fixture
def db(session_factory) -> Session:
    with session_factory() as session:
        yield session


@pytest.fixture
def client(session_factory):
    """Cliente HTTP contra la app, apuntando a la base en memoria."""

    def override_get_db():
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def plan(db) -> Plan:
    """Un plan mínimo para las pruebas que no necesitan la semilla completa."""
    plan = Plan(
        code="basico",
        name="Básico",
        slo_availability=99,
        support_hours="lun-vie 08:00-18:00",
        cpu_quota="250m",
        memory_quota="256Mi",
    )
    db.add(plan)
    db.commit()
    return plan


@pytest.fixture
def seeded(db):
    """La base con los datos reales de seed/ (agencia, planes, SLA y 3 clientes)."""
    assert seed_if_empty(db) is True
    return db

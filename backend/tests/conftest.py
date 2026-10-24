# Utilidades compartidas de las pruebas de la API: base SQLite en memoria y cliente HTTP.
import os

# Las pruebas nunca tocan la base real: se fuerza SQLite antes de importar la app.
os.environ["DATABASE_URL"] = "sqlite://"
# Valores de prueba (spec 007): no son secretos reales
os.environ["JWT_SECRET"] = "clave-de-pruebas-que-no-es-secreta-0123456789"
os.environ["SEED_USER_PASSWORD"] = "clave-de-desarrollo"
os.environ["BCRYPT_ROUNDS"] = "4"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, select  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.db import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Plan, User  # noqa: E402
from app.seed import seed_if_empty  # noqa: E402
from app.services.auth import create_token  # noqa: E402


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


def _authenticated(session_factory, email: str, role: str, client_id: int | None = None) -> TestClient:
    """Cliente HTTP con el token de `email`; si el usuario no existe lo crea (sin contraseña)."""
    with session_factory() as session:
        user = session.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(name=email.split("@")[0], email=email, role=role, client_id=client_id)
            session.add(user)
            session.commit()
        token = create_token(user)
    http = TestClient(app)
    http.headers.update({"Authorization": f"Bearer {token}"})
    return http


@pytest.fixture
def as_user(client, session_factory):
    """Fábrica: `as_user("correo@x.test")` devuelve un cliente HTTP con la sesión de ese usuario sembrado."""

    def make(email: str) -> TestClient:
        with session_factory() as session:
            user = session.scalar(select(User).where(User.email == email))
            assert user is not None, f"El usuario {email} no está sembrado"
            return _authenticated(session_factory, email, user.role, user.client_id)

    return make


@pytest.fixture
def as_agency(client, session_factory):
    """Cliente HTTP con la sesión de un técnico de la agencia (se crea si no hay semilla)."""
    return _authenticated(session_factory, "sofia@forjadigital.test", "agencia")


@pytest.fixture
def as_client(client, seeded, as_user):
    """Cliente HTTP con la sesión de Marta Ríos, de La Sazón (usa la semilla)."""
    return as_user("contacto@lasazon.test")

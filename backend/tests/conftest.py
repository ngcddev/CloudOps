# Utilidades compartidas de las pruebas de la API: base SQLite en memoria y cliente HTTP.
import os

# Las pruebas nunca tocan la base real: se fuerza SQLite antes de importar la app.
os.environ["DATABASE_URL"] = "sqlite://"
# Valores de prueba (spec 007): no son secretos reales
os.environ["JWT_SECRET"] = "clave-de-pruebas-que-no-es-secreta-0123456789"
os.environ["SEED_USER_PASSWORD"] = "clave-de-desarrollo"
os.environ["BCRYPT_ROUNDS"] = "4"
os.environ["PIPELINE_TOKEN"] = "token-del-pipeline-de-pruebas"

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
def api_db(session_factory):
    """Apunta la app a la base en memoria. Lo usan `client` y las fixtures de sesión."""

    def override_get_db():
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client(api_db):
    """Cliente HTTP SIN sesión contra la app, apuntando a la base en memoria.

    Los módulos de pruebas de rutas protegidas (spec 007) lo redefinen para que entregue la sesión
    de la agencia: `def client(as_agency): return as_agency`. Las pruebas de 401/403/404 usan
    `anonymous`, `as_client` o `as_user`.
    """
    return TestClient(app)


@pytest.fixture
def anonymous(api_db):
    """Cliente HTTP sin sesión (no se redefine en ningún módulo)."""
    return TestClient(app)


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
def as_user(api_db, session_factory):
    """Fábrica: `as_user("correo@x.test")` devuelve un cliente HTTP con la sesión de ese usuario sembrado."""

    def make(email: str) -> TestClient:
        with session_factory() as session:
            user = session.scalar(select(User).where(User.email == email))
            assert user is not None, f"El usuario {email} no está sembrado"
            return _authenticated(session_factory, email, user.role, user.client_id)

    return make


@pytest.fixture
def as_agency(api_db, session_factory):
    """Cliente HTTP con la sesión de un técnico de la agencia (usuario propio de las pruebas, no choca con la semilla)."""
    return _authenticated(session_factory, "tecnico.pruebas@forjadigital.test", "agencia")


@pytest.fixture
def as_client(api_db, seeded, as_user):
    """Cliente HTTP con la sesión de Marta Ríos, de La Sazón (usa la semilla)."""
    return as_user("contacto@lasazon.test")

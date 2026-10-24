# Pruebas de las dependencias de sesión y permisos con una app mínima (spec 007, T05).
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.db import get_db
from app.deps import client_scope, current_user, require_agency
from app.models import User
from app.services.auth import create_token


@pytest.fixture
def users(db):
    agency = User(name="Sofía", email="s@x.test", role="agencia")
    client = User(name="Marta", email="m@x.test", role="cliente", client_id=None)
    inactive = User(name="Baja", email="b@x.test", role="agencia", is_active=False)
    db.add_all([agency, client, inactive])
    db.commit()
    return agency, client, inactive


@pytest.fixture
def http(session_factory, users):
    app = FastAPI()

    @app.get("/quien")
    def quien(user: User = Depends(current_user)):
        return {"id": user.id}

    @app.get("/solo-agencia")
    def solo_agencia(user: User = Depends(require_agency)):
        return {"id": user.id}

    @app.get("/alcance")
    def alcance(user: User = Depends(current_user)):
        return {"client_id": client_scope(user)}

    def override_get_db():
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def _auth(user: User) -> dict:
    return {"Authorization": f"Bearer {create_token(user)}"}


def test_sin_token_responde_401(http):
    response = http.get("/quien")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_token_invalido_o_vencido_responde_401(http, users):
    agency, _, _ = users
    old = create_token(agency, now=datetime.now(timezone.utc) - timedelta(hours=3))

    assert http.get("/quien", headers={"Authorization": "Bearer basura"}).status_code == 401
    assert http.get("/quien", headers={"Authorization": f"Bearer {old}"}).status_code == 401


def test_usuario_inactivo_responde_401(http, users):
    _, _, inactive = users

    assert http.get("/quien", headers=_auth(inactive)).status_code == 401


def test_agencia_pasa_y_cliente_recibe_403(http, users):
    agency, client, _ = users

    assert http.get("/solo-agencia", headers=_auth(agency)).status_code == 200
    assert http.get("/solo-agencia", headers=_auth(client)).status_code == 403
    assert http.get("/solo-agencia").status_code == 401


def test_alcance_de_agencia_es_todo_y_el_de_cliente_es_su_id(http, users, db):
    agency, client, _ = users
    client.client_id = 3
    db.commit()

    assert http.get("/alcance", headers=_auth(agency)).json() == {"client_id": None}
    assert http.get("/alcance", headers=_auth(client)).json() == {"client_id": 3}


def test_cliente_sin_cliente_asignado_no_tiene_alcance(http, users):
    _, client, _ = users

    assert http.get("/alcance", headers=_auth(client)).status_code == 403

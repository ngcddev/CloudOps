# Pruebas del inicio de sesión y de GET /api/auth/me (spec 007, T04).
from sqlalchemy import select

from app.config import settings
from app.models import User


def _login(client, email, password=None):
    return client.post(
        "/api/auth/login", json={"email": email, "password": password or settings.seed_user_password}
    )


def test_login_de_un_cliente_devuelve_token_y_su_cliente(client, seeded):
    response = _login(client, "contacto@lasazon.test")

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["role"] == "cliente"
    assert body["user"]["client_id"] is not None
    assert "password" not in str(body)


def test_me_responde_el_usuario_del_token(client, seeded):
    token = _login(client, "contacto@lasazon.test").json()["access_token"]

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert me.status_code == 200
    assert me.json()["email"] == "contacto@lasazon.test"
    assert me.json()["role"] == "cliente"


def test_login_actualiza_el_ultimo_ingreso(client, seeded):
    assert _login(client, "sofia@forjadigital.test").status_code == 200

    user = seeded.scalar(select(User).where(User.email == "sofia@forjadigital.test"))
    seeded.refresh(user)
    assert user.last_login_at is not None


def test_el_correo_no_distingue_mayusculas(client, seeded):
    assert _login(client, "  Sofia@ForjaDigital.test ").status_code == 200


def test_contrasena_errada_correo_inexistente_y_usuario_inactivo_dan_el_mismo_401(client, seeded):
    seeded.scalar(select(User).where(User.email == "contacto@eltornillo.test")).is_active = False
    seeded.commit()

    wrong = _login(client, "sofia@forjadigital.test", "no-es")
    missing = _login(client, "nadie@forjadigital.test")
    inactive = _login(client, "contacto@eltornillo.test")

    assert [r.status_code for r in (wrong, missing, inactive)] == [401, 401, 401]
    assert wrong.json() == missing.json() == inactive.json()


def test_usuario_sin_contrasena_no_puede_entrar(client, seeded):
    seeded.scalar(select(User).where(User.email == "sofia@forjadigital.test")).password_hash = None
    seeded.commit()

    assert _login(client, "sofia@forjadigital.test").status_code == 401


def test_me_sin_token_responde_401(client, seeded):
    assert client.get("/api/auth/me").status_code == 401


def test_login_sin_contrasena_responde_422_en_espanol(client, seeded):
    response = client.post("/api/auth/login", json={"email": "sofia@forjadigital.test"})

    assert response.status_code == 422
    assert "contraseña" in response.json()["detail"][0]["msg"]

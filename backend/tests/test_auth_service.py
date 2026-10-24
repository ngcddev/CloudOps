# Pruebas de contraseñas con hash y tokens de sesión (spec 007, T03).
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.config import settings
from app.models.user import User
from app.services.auth import (
    InvalidToken,
    create_token,
    decode_token,
    hash_password,
    verify_password,
)


def _user() -> User:
    return User(id=7, name="Marta", email="m@x.test", role="cliente", client_id=3)


def test_la_contrasena_correcta_valida_y_la_incorrecta_no():
    hashed = hash_password("clave-de-prueba")

    assert hashed.startswith("$2b$")
    assert "clave-de-prueba" not in hashed
    assert verify_password("clave-de-prueba", hashed) is True
    assert verify_password("otra", hashed) is False


def test_sin_hash_nunca_valida():
    assert verify_password("lo-que-sea", None) is False
    assert verify_password("lo-que-sea", "no-es-un-hash") is False


def test_el_token_lleva_id_rol_y_cliente():
    claims = decode_token(create_token(_user()))

    assert claims["sub"] == "7"
    assert claims["role"] == "cliente"
    assert claims["client_id"] == 3


def test_un_token_vencido_se_rechaza():
    old = datetime.now(timezone.utc) - timedelta(hours=2)

    with pytest.raises(InvalidToken):
        decode_token(create_token(_user(), now=old))


def test_un_token_firmado_con_otra_clave_se_rechaza():
    forged = jwt.encode(
        {"sub": "1", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        "otra-clave-distinta-de-treinta-y-dos-bytes",
        algorithm="HS256",
    )

    with pytest.raises(InvalidToken):
        decode_token(forged)


def test_la_clave_del_token_sale_de_la_configuracion():
    assert settings.jwt_secret

# Pruebas de la regla de arranque sobre JWT_SECRET (T07, auditoría CT-01): ni corta ni la del ejemplo publicado.
import pytest
from fastapi.testclient import TestClient

from app.config import JWT_SECRET_MIN_LENGTH, settings, validate_jwt_secret
from app.main import app


def test_acepta_una_clave_larga_y_propia():
    validate_jwt_secret("x" * JWT_SECRET_MIN_LENGTH)


def test_rechaza_una_clave_corta():
    with pytest.raises(RuntimeError, match="al menos 32"):
        validate_jwt_secret("x" * (JWT_SECRET_MIN_LENGTH - 1))


def test_rechaza_la_clave_del_ejemplo_aunque_sea_larga():
    # El valor de .env.example mide más de 32 caracteres: debe fallar por ser público, no por su largo
    with pytest.raises(RuntimeError, match="valor de ejemplo"):
        validate_jwt_secret("clave-de-desarrollo-cambiala-en-produccion-0123456789")


def test_el_mensaje_dice_como_generarla():
    with pytest.raises(RuntimeError, match="secrets.token_urlsafe"):
        validate_jwt_secret("corta")


def test_la_api_no_arranca_con_una_clave_invalida(monkeypatch):
    monkeypatch.setattr(settings, "jwt_secret", "corta")
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        with TestClient(app):
            pass

# Recorre todas las rutas de la API y exige sesión en cada una (spec 007, T14 · CA-2).
import re

import pytest

from app.main import app

# Únicas rutas que responden sin sesión: la salud del servicio y el inicio de sesión
PUBLICAS = {("GET", "/health"), ("POST", "/api/auth/login")}


def _rutas():
    """(método, ruta) de cada endpoint, leídos del esquema OpenAPI de la app."""
    for path, operations in app.openapi()["paths"].items():
        for method in operations:
            yield method.upper(), path


@pytest.mark.parametrize(("method", "path"), sorted(set(_rutas())))
def test_la_ruta_exige_sesion(anonymous, method, path):
    if (method, path) in PUBLICAS:
        pytest.skip("ruta pública a propósito")
    url = re.sub(r"\{[^}]+\}", "1", path)

    response = anonymous.request(method, url, json={})

    assert response.status_code == 401, f"{method} {path} responde {response.status_code} sin sesión"


def test_las_rutas_publicas_son_solo_las_esperadas():
    existentes = set(_rutas())

    assert PUBLICAS <= existentes
    # Si una ruta nueva debe ser pública, se agrega a PUBLICAS a propósito en este archivo
    assert len(existentes) > len(PUBLICAS)

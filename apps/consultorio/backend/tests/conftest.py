# Utilidades compartidas de las pruebas del backend del formulario de citas.

import pytest
from fastapi.testclient import TestClient

from app import main


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    """Cada prueba usa su propia base SQLite temporal."""
    path = tmp_path / "contact.db"
    monkeypatch.setattr(main, "DB_PATH", str(path))
    return path


@pytest.fixture
def client(db_path):
    """Cliente HTTP contra la app, ya apuntando a la base temporal."""
    return TestClient(main.app)

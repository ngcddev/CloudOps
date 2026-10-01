# Pruebas del modo v2 del backend del formulario de citas: la versión rota responde 500 en /health (spec 002, T09).

from app import main


def test_health_in_v2_returns_500(client, monkeypatch):
    monkeypatch.setattr(main, "APP_VERSION", "v2")

    response = client.get("/health")

    assert response.status_code == 500
    assert response.json() == {"status": "error", "version": "v2"}


def test_health_in_v1_stays_ok(client, monkeypatch):
    monkeypatch.setattr(main, "APP_VERSION", "v1")

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "v1"}

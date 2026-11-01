# Pruebas de las métricas del formulario: recibidos y fallidos con OpenTelemetry, publicados en /metrics (spec 008, T32).

import re
import sqlite3

from fastapi.testclient import TestClient

from app import main

VALID_REQUEST = {"name": "Ana Ruiz", "phone": "3001234567", "reason": "Limpieza dental"}


def serie(client: TestClient, nombre: str) -> float:
    """Valor actual de una serie de /metrics; 0 si todavía no existe (el contador nace con el primer envío)."""
    texto = client.get("/metrics").text
    for linea in texto.splitlines():
        coincide = re.match(rf"^{nombre}(?:\{{.*\}})? ([0-9.e+-]+)$", linea)
        if coincide:
            return float(coincide.group(1))
    return 0.0


def test_valid_form_counts_as_received(client):
    antes_recibidos = serie(client, "contact_forms_received_total")
    antes_fallidos = serie(client, "contact_forms_failed_total")

    assert client.post("/api/contact", json=VALID_REQUEST).status_code == 200

    assert serie(client, "contact_forms_received_total") == antes_recibidos + 1
    assert serie(client, "contact_forms_failed_total") == antes_fallidos


def test_invalid_form_counts_as_failed(client):
    antes_recibidos = serie(client, "contact_forms_received_total")
    antes_fallidos = serie(client, "contact_forms_failed_total")

    assert client.post("/api/contact", json={**VALID_REQUEST, "phone": "123"}).status_code == 422

    assert serie(client, "contact_forms_failed_total") == antes_fallidos + 1
    assert serie(client, "contact_forms_received_total") == antes_recibidos


def test_server_error_counts_as_failed(db_path, monkeypatch):
    def romper() -> sqlite3.Connection:
        raise sqlite3.OperationalError("base no disponible")

    monkeypatch.setattr(main, "get_connection", romper)
    client = TestClient(main.app, raise_server_exceptions=False)
    antes_fallidos = serie(client, "contact_forms_failed_total")

    assert client.post("/api/contact", json=VALID_REQUEST).status_code == 500

    assert serie(client, "contact_forms_failed_total") == antes_fallidos + 1


def test_other_routes_do_not_change_the_counters(client):
    client.post("/api/contact", json=VALID_REQUEST)
    recibidos = serie(client, "contact_forms_received_total")
    fallidos = serie(client, "contact_forms_failed_total")

    client.get("/health")
    client.get("/metrics")

    assert serie(client, "contact_forms_received_total") == recibidos
    assert serie(client, "contact_forms_failed_total") == fallidos

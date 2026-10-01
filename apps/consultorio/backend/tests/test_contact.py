# Pruebas del backend del formulario de citas: /health en v1 y POST /api/contact (spec 002, T09).

import sqlite3
from datetime import datetime

VALID_REQUEST = {"name": "Ana Ruiz", "phone": "3001234567", "reason": "Limpieza dental"}


def test_health_reports_ok_and_version(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "v1"}


def test_contact_returns_ok(client):
    response = client.post("/api/contact", json=VALID_REQUEST)

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_contact_is_saved_with_utc_date(client, db_path):
    client.post("/api/contact", json={**VALID_REQUEST, "name": "  Ana Ruiz  "})

    rows = sqlite3.connect(db_path).execute(
        "SELECT name, phone, reason, created_at FROM contact_requests"
    ).fetchall()
    assert len(rows) == 1
    name, phone, reason, created_at = rows[0]
    assert (name, phone, reason) == ("Ana Ruiz", "3001234567", "Limpieza dental")
    assert datetime.fromisoformat(created_at).utcoffset().total_seconds() == 0


def test_contact_rejects_missing_fields(client, db_path):
    response = client.post("/api/contact", json={"name": "", "phone": "1", "reason": ""})

    assert response.status_code == 422
    assert not db_path.exists()


def test_contact_rejects_incomplete_body(client):
    response = client.post("/api/contact", json={"name": "Ana Ruiz"})

    assert response.status_code == 422


def test_contact_rejects_whitespace_only_fields(client, db_path):
    response = client.post("/api/contact", json={"name": "   ", "phone": "3001234567", "reason": "   "})

    assert response.status_code == 422
    assert not db_path.exists()

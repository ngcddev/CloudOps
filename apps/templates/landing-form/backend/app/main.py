# API mínima del formulario de la plantilla landing-form (spec 002): estado del servicio y versión,
# y recepción de solicitudes de contacto guardadas en SQLite.

import os
import sqlite3
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# La versión se fija en build (--build-arg APP_VERSION) y llega como variable de entorno.
# v1 = versión sana; v2 = versión rota a propósito para provocar una caída controlada en la demo.
APP_VERSION = os.getenv("APP_VERSION", "v1")
BROKEN_VERSION = "v2"

# SQLite dentro del contenedor: dato de demo que se pierde al reiniciar.
# Va en /tmp porque es el único lugar con escritura para un usuario sin root.
DB_PATH = os.getenv("CONTACT_DB_PATH", "/tmp/contact.db")

app = FastAPI(title="Formulario de contacto", version=APP_VERSION)


class ContactRequest(BaseModel):
    """Datos que envía el visitante desde el formulario."""

    name: str = Field(min_length=1, max_length=120)
    phone: str = Field(min_length=7, max_length=20)
    reason: str = Field(min_length=1, max_length=500)


def get_connection() -> sqlite3.Connection:
    """Abre la base y crea la tabla la primera vez."""
    connection = sqlite3.connect(DB_PATH)
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS contact_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            reason TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    return connection


@app.get("/health")
def health() -> JSONResponse:
    """Estado y versión del backend; lo usan el monitoreo y la readiness probe. En v2 responde 500."""
    if APP_VERSION == BROKEN_VERSION:
        return JSONResponse(status_code=500, content={"status": "error", "version": APP_VERSION})
    return JSONResponse(content={"status": "ok", "version": APP_VERSION})


@app.post("/api/contact")
def create_contact(request: ContactRequest) -> dict:
    """Guarda la solicitud del visitante (fecha en UTC) y confirma la recepción."""
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO contact_requests (name, phone, reason, created_at) VALUES (?, ?, ?, ?)",
            (
                request.name.strip(),
                request.phone.strip(),
                request.reason.strip(),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
    connection.close()
    return {"ok": True}

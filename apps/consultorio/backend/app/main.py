# API mínima del formulario de citas de Dental Popayán (spec 002, copia de la plantilla landing-form):
# estado del servicio y versión, y recepción de solicitudes de cita guardadas en SQLite.

import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from typing import Annotated

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, StringConstraints

# La versión se fija en build (--build-arg APP_VERSION) y llega como variable de entorno.
# v1 = versión sana; v2 = versión rota a propósito para provocar una caída controlada en la demo.
APP_VERSION = os.getenv("APP_VERSION", "v1")
BROKEN_VERSION = "v2"

# SQLite dentro del contenedor: dato de demo que se pierde al reiniciar.
# Va en /tmp porque es el único lugar con escritura para un usuario sin root.
DB_PATH = os.getenv("CONTACT_DB_PATH", "/tmp/contact.db")

app = FastAPI(title="Formulario de citas · Dental Popayán", version=APP_VERSION)


class ContactRequest(BaseModel):
    """Datos que envía el visitante desde el formulario."""

    # Se quitan los espacios antes de validar: un texto de solo espacios cuenta como vacío.
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
    phone: Annotated[str, StringConstraints(strip_whitespace=True, min_length=7, max_length=20)]
    reason: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]


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
    # closing() cierra la conexión siempre; el with interno confirma o revierte la transacción.
    with closing(get_connection()) as connection, connection:
        connection.execute(
            "INSERT INTO contact_requests (name, phone, reason, created_at) VALUES (?, ?, ?, ?)",
            (request.name, request.phone, request.reason, datetime.now(timezone.utc).isoformat()),
        )
    return {"ok": True}

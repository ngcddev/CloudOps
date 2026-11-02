# API mínima del formulario de citas de Dental Popayán (spec 002, copia de la plantilla landing-form):
# estado del servicio y versión, y recepción de solicitudes de cita guardadas en SQLite. Cuenta los
# formularios recibidos y fallidos con OpenTelemetry y los publica en /metrics para Prometheus (spec 008, T32).

import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from typing import Annotated

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.metrics import MeterProvider
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel, StringConstraints

# La versión se fija en build (--build-arg APP_VERSION) y llega como variable de entorno.
# v1 = versión sana; v2 = versión rota a propósito para provocar una caída controlada en la demo.
APP_VERSION = os.getenv("APP_VERSION", "v1")
BROKEN_VERSION = "v2"

# SQLite dentro del contenedor: dato de demo que se pierde al reiniciar.
# Va en /tmp porque es el único lugar con escritura para un usuario sin root.
DB_PATH = os.getenv("CONTACT_DB_PATH", "/tmp/contact.db")

app = FastAPI(title="Formulario de citas · Dental Popayán", version=APP_VERSION)

# Métricas (T32): el lector de OpenTelemetry deja las series en el registro de prometheus_client y /metrics
# las entrega. Sin MeterProvider global: así importar el módulo dos veces (pruebas) no lo pisa.
_provider = MeterProvider(metric_readers=[PrometheusMetricReader()])
_meter = _provider.get_meter("consultorio-api")
# recibidos = solicitudes guardadas; fallidos = el formulario se rechazó (datos inválidos) o falló (error del servidor)
forms_received = _meter.create_counter("contact_forms_received", description="Formularios de cita guardados")
forms_failed = _meter.create_counter("contact_forms_failed", description="Formularios de cita rechazados o con error")
CONTACT_PATH = "/api/contact"


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


@app.middleware("http")
async def count_contact_forms(request: Request, call_next):
    """Cuenta cada envío del formulario según cómo se respondió (T32); las demás rutas no se tocan."""
    if request.method != "POST" or request.url.path != CONTACT_PATH:
        return await call_next(request)
    try:
        response = await call_next(request)
    except Exception:
        forms_failed.add(1)
        raise
    (forms_received if response.status_code < 400 else forms_failed).add(1)
    return response


@app.get("/metrics")
def metrics_endpoint() -> Response:
    """Series en formato Prometheus. El Ingress solo enruta /api, así que no sale a internet."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


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

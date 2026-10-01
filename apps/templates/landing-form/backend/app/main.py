# API mínima del formulario de la plantilla landing-form (spec 002): estado del servicio y versión.

import os

from fastapi import FastAPI

# La versión se fija en build (--build-arg APP_VERSION) y llega como variable de entorno.
APP_VERSION = os.getenv("APP_VERSION", "v1")

app = FastAPI(title="Formulario de contacto", version=APP_VERSION)


@app.get("/health")
def health() -> dict:
    """Estado y versión del backend; lo usan el monitoreo y la readiness probe."""
    return {"status": "ok", "version": APP_VERSION}

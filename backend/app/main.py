# Punto de entrada de la API del Hub: crea la app, registra routers y expone GET /health.
import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import models  # noqa: F401  (registra los modelos en Base.metadata)
from app.config import settings
from app.db import SessionLocal, get_db
from app.integrations.argocd import argocd_from_settings
from app.integrations.gitea import gitea_from_settings
from app.routers import audit_logs, auth, catalog, change_requests, clients, pipeline, security, services, tickets
from app.seed import seed_if_empty, seed_passwords
from app.services.deploy_watch import watch_forever


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Las tablas las crea Alembic (alembic upgrade head) al arrancar el contenedor;
    # aquí solo se cargan los datos semilla si la base está vacía.
    with SessionLocal() as db:
        seed_if_empty(db)
        seed_passwords(db)
    # Seguimiento de las publicaciones (spec 005): solo si hay conexión configurada con Argo CD
    watcher = None
    if settings.argocd_url and settings.argocd_token:
        # Con Gitea configurado, el seguimiento también alinea la versión si cambia a mano en Git
        gitea = gitea_from_settings() if settings.gitea_url and settings.gitea_token else None
        watcher = asyncio.create_task(watch_forever(SessionLocal, argocd_from_settings(), gitea=gitea))
    yield
    if watcher is not None:
        watcher.cancel()
        with suppress(asyncio.CancelledError):
            await watcher


app = FastAPI(title="CloudOps Client Hub", lifespan=lifespan)
app.include_router(auth.router)
app.include_router(audit_logs.router)
app.include_router(catalog.router)
app.include_router(clients.router)
app.include_router(clients.projects_router)
app.include_router(tickets.router)
app.include_router(change_requests.router)
app.include_router(services.router)
app.include_router(pipeline.router)
app.include_router(security.router)

# Nombre de cada campo tal como se le muestra a la persona usuaria
_CAMPOS = {
    "name": "nombre",
    "contact_name": "contacto",
    "email": "correo",
    "phone": "teléfono",
    "host": "dirección (host)",
    "template": "plantilla",
    "namespace": "namespace",
    "plan_id": "plan",
    "password": "contraseña",
    "event": "evento",
    "site": "sitio",
    "version": "versión",
    "step": "control",
    "status": "resultado",
    "reason": "motivo",
    "to_version": "versión destino",
    "ticket_id": "solicitud",
}


@app.exception_handler(RequestValidationError)
async def validation_error_es(_: Request, exc: RequestValidationError) -> JSONResponse:
    """Devuelve los errores 422 con mensajes en español (plan 001#api)."""
    detail = []
    for error in exc.errors():
        campo = _CAMPOS.get(str(error["loc"][-1]), str(error["loc"][-1]))
        if error["type"] == "missing":
            msg = f"El campo «{campo}» es obligatorio."
        elif error["type"] == "string_too_long":
            msg = f"El campo «{campo}» es demasiado largo."
        elif error["type"] == "literal_error":
            msg = f"El campo «{campo}» tiene un valor no permitido: {error['ctx']['expected']}."
        else:
            msg = error["msg"].removeprefix("Value error, ")
        detail.append({"loc": error["loc"], "msg": msg})
    return JSONResponse(status_code=422, content={"detail": detail})


@app.get("/health")
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    """Responde ok solo si la base contesta."""
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(status_code=503, detail="No hay conexión con la base de datos")
    return {"status": "ok"}

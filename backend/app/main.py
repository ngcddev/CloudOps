# Punto de entrada de la API del Hub: crea la app, registra routers y expone GET /health.
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import models  # noqa: F401  (registra los modelos en Base.metadata)
from app.db import SessionLocal, get_db
from app.routers import clients
from app.seed import seed_if_empty


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Las tablas las crea Alembic (alembic upgrade head) al arrancar el contenedor;
    # aquí solo se cargan los datos semilla si la base está vacía.
    with SessionLocal() as db:
        seed_if_empty(db)
    yield


app = FastAPI(title="CloudOps Client Hub", lifespan=lifespan)
app.include_router(clients.router)
app.include_router(clients.projects_router)

# Nombre de cada campo tal como se le muestra a la persona usuaria
_CAMPOS = {"name": "nombre", "contact_name": "contacto", "email": "correo", "phone": "teléfono"}


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

# Punto de entrada de la API del Hub: crea la app, registra routers y expone GET /health.
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db

app = FastAPI(title="CloudOps Client Hub")


@app.get("/health")
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    """Responde ok solo si la base contesta."""
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(status_code=503, detail="No hay conexión con la base de datos")
    return {"status": "ok"}

import os

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI(title="Landing Form Backend")


class ContactPayload(BaseModel):
    name: str
    phone: str
    reason: str


@app.get("/health")
def health() -> JSONResponse:
    version = os.getenv("APP_VERSION", "v1")
    if version == "v2":
        return JSONResponse(status_code=500, content={"status": "error", "version": "v2"})
    return JSONResponse(content={"status": "ok", "version": version})


@app.post("/api/contact")
def contact(payload: ContactPayload) -> dict[str, bool]:
    _ = payload
    return {"ok": True}

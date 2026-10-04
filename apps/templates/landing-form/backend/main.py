from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Landing Form Backend")


class ContactPayload(BaseModel):
    name: str
    phone: str
    reason: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "v1"}


@app.post("/api/contact")
def contact(payload: ContactPayload) -> dict[str, bool]:
    _ = payload
    return {"ok": True}

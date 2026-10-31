# Endpoints de los borradores de un incidente: generarlos con el asistente (spec 012). Solo agencia.
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.deps import require_agency
from app.models.ai_draft import AiDraft
from app.models.incident import Incident
from app.models.project import Project
from app.models.service import Service
from app.schemas.ai_draft import AiDraftOut, AiDraftsGenerated
from app.services.ai_drafts import DraftWriter, WriterError, generate_drafts

incident_router = APIRouter(
    prefix="/api/incidents", tags=["borradores"], dependencies=[Depends(require_agency)]
)

# Mientras no haya asistente en el PC B (módulo 5), el botón avisa que se escriba a mano
MANUAL_HINT = "Escribe el texto a mano: el borrador se prellena con los datos reales del incidente."


def get_writer() -> DraftWriter | None:
    """Asistente configurado, o None si no hay (las pruebas lo reemplazan por tests/fake_ollama.py)."""
    return None


def _as_utc(value: datetime | None) -> datetime | None:
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def present_draft(draft: AiDraft) -> dict:
    return {
        "id": draft.id,
        "incident_id": draft.incident_id,
        "kind": draft.kind,
        "status": draft.status,
        "model": draft.model,
        "prompt_version": draft.prompt_version,
        "generated_text": draft.generated_text,
        "final_text": draft.final_text,
        "created_by_name": draft.created_by.name if draft.created_by else None,
        "approved_by_name": draft.approved_by.name if draft.approved_by else None,
        "approved_at": _as_utc(draft.approved_at),
        "latency_ms": draft.latency_ms,
        "created_at": _as_utc(draft.created_at),
    }


def _load_incident(db: Session, incident_id: int) -> Incident:
    """Incidente con su servicio y cliente (los hechos del contexto), o 404."""
    incident = db.scalar(
        select(Incident)
        .options(selectinload(Incident.service).selectinload(Service.project).selectinload(Project.client))
        .where(Incident.id == incident_id)
    )
    if incident is None:
        raise HTTPException(status_code=404, detail="El incidente no existe.")
    return incident


def _require_mitigated(incident: Incident) -> None:
    """Los borradores cuentan qué pasó y cómo se recuperó: hace falta que el incidente esté mitigado."""
    if incident.mitigated_at is None:
        raise HTTPException(
            status_code=409, detail="Los borradores se generan cuando el incidente está mitigado."
        )


@incident_router.post(
    "/{incident_id}/ai-drafts", response_model=AiDraftsGenerated, status_code=status.HTTP_201_CREATED
)
def create_ai_drafts(
    incident_id: int,
    db: Session = Depends(get_db),
    writer: DraftWriter | None = Depends(get_writer),
):
    """Pide al asistente el resumen y el mensaje. Si no está o no responde a tiempo, 503 y se escribe a mano.

    El tiempo de espera (60 s) lo pone el asistente al llamar al PC B; el incidente no cambia en ningún caso.
    """
    incident = _load_incident(db, incident_id)
    _require_mitigated(incident)
    if writer is None:
        raise HTTPException(status_code=503, detail=f"El asistente no está disponible. {MANUAL_HINT}")
    try:
        result = generate_drafts(db, incident, writer)
    except WriterError as error:
        db.rollback()
        raise HTTPException(status_code=503, detail=f"{error} {MANUAL_HINT}") from error
    db.commit()
    return {"drafts": [present_draft(draft) for draft in result.drafts], "problems": result.problems}

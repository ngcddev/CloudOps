# Endpoints de los borradores de un incidente: generarlos con el asistente, listarlos, escribirlos a mano,
# aprobarlos y descartarlos (spec 012). Solo agencia.
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.deps import require_agency
from app.models.ai_draft import AiDraft
from app.models.incident import Incident
from app.models.project import Project
from app.models.service import Service
from app.models.user import User
from app.schemas.ai_draft import AiDraftOut, AiDraftsGenerated, ApproveDraftIn, IncidentDrafts, ManualDraftIn
from app.services import audit
from app.services.ai_context import incident_facts, manual_summary
from app.services.ai_drafts import DraftWriter, WriterError, check_text, generate_drafts
from app.services.messages import client_message

incident_router = APIRouter(
    prefix="/api/incidents", tags=["borradores"], dependencies=[Depends(require_agency)]
)
drafts_router = APIRouter(prefix="/api/ai-drafts", tags=["borradores"], dependencies=[Depends(require_agency)])

# Mientras no haya asistente en el PC B (módulo 5), el botón avisa que se escriba a mano
MANUAL_HINT = "Escribe el texto a mano: el borrador se prellena con los datos reales del incidente."


def utcnow() -> datetime:
    """Hora actual en UTC; las pruebas la reemplazan para fijar el reloj."""
    return datetime.now(timezone.utc)


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


@incident_router.get("/{incident_id}/drafts", response_model=IncidentDrafts)
def list_drafts(incident_id: int, db: Session = Depends(get_db)):
    """Borradores del incidente en orden, con las plantillas prellenadas para escribir a mano (CA-5)."""
    incident = _load_incident(db, incident_id)
    drafts = db.scalars(
        select(AiDraft)
        .options(selectinload(AiDraft.created_by), selectinload(AiDraft.approved_by))
        .where(AiDraft.incident_id == incident.id)
        .order_by(AiDraft.id)
    ).all()
    templates = {"resumen": None, "mensaje_cliente": None}
    if incident.mitigated_at is not None:
        templates = {
            "resumen": manual_summary(incident_facts(incident)),
            "mensaje_cliente": client_message(incident),
        }
    return {"drafts": [present_draft(draft) for draft in drafts], "manual_templates": templates}


@incident_router.post("/{incident_id}/drafts", response_model=AiDraftOut, status_code=status.HTTP_201_CREATED)
def create_manual_draft(
    incident_id: int,
    data: ManualDraftIn,
    db: Session = Depends(get_db),
    actor: User = Depends(require_agency),
):
    """Guarda un borrador escrito a mano; pasa por los mismos controles que el del asistente (CA-3, CA-5)."""
    incident = _load_incident(db, incident_id)
    _require_mitigated(incident)
    problem = check_text(data.kind, data.text, incident_facts(incident))
    if problem is not None:
        raise HTTPException(status_code=422, detail=problem)
    draft = AiDraft(
        incident_id=incident.id,
        kind=data.kind,
        status="borrador_ia",
        model="manual",
        generated_text=data.text,
        created_by_id=actor.id,
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return present_draft(draft)


def _load_draft(db: Session, draft_id: int) -> AiDraft:
    """Borrador con su incidente (para revisar las horas), o 404."""
    draft = db.scalar(
        select(AiDraft)
        .options(
            selectinload(AiDraft.incident)
            .selectinload(Incident.service)
            .selectinload(Service.project)
            .selectinload(Project.client)
        )
        .where(AiDraft.id == draft_id)
    )
    if draft is None:
        raise HTTPException(status_code=404, detail="El borrador no existe.")
    return draft


def _require_pending(draft: AiDraft) -> None:
    if draft.status != "borrador_ia":
        estado = "aprobado" if draft.status == "aprobado" else "descartado"
        raise HTTPException(status_code=409, detail=f"El borrador ya está {estado}.")


@drafts_router.post("/{draft_id}/approve", response_model=AiDraftOut)
def approve_draft(
    draft_id: int,
    data: ApproveDraftIn,
    request: Request,
    db: Session = Depends(get_db),
    actor: User = Depends(require_agency),
):
    """Aprueba el borrador con el texto final; desde aquí el mensaje al cliente se ve en su portal (CA-4).

    El texto final pasa otra vez los controles: una edición no puede meter jerga ni horas inventadas. Un
    incidente tiene un solo texto aprobado por tipo: el anterior queda descartado.
    """
    draft = _load_draft(db, draft_id)
    _require_pending(draft)
    final_text = data.text if data.text is not None else draft.generated_text
    problem = check_text(draft.kind, final_text, incident_facts(draft.incident))
    if problem is not None:
        raise HTTPException(status_code=422, detail=problem)
    replaced = db.scalars(
        select(AiDraft).where(
            AiDraft.incident_id == draft.incident_id,
            AiDraft.kind == draft.kind,
            AiDraft.status == "aprobado",
        )
    ).all()
    for previous in replaced:
        previous.status = "descartado"
    draft.status = "aprobado"
    draft.final_text = final_text
    draft.approved_by_id = actor.id
    draft.approved_at = utcnow()
    audit.record(
        db, actor, "aprobar", "ai_draft", draft.id,
        {
            "incidente": draft.incident_id,
            "tipo": draft.kind,
            "modelo": draft.model,
            "editado": final_text != draft.generated_text,
            "reemplaza": [previous.id for previous in replaced] or None,
        },
        audit.request_ip(request),
    )
    db.commit()
    db.refresh(draft)
    return present_draft(draft)


@drafts_router.post("/{draft_id}/discard", response_model=AiDraftOut)
def discard_draft(
    draft_id: int,
    request: Request,
    db: Session = Depends(get_db),
    actor: User = Depends(require_agency),
):
    """Descarta un borrador que no sirve; queda en la lista para ver qué propuso el asistente."""
    draft = _load_draft(db, draft_id)
    _require_pending(draft)
    draft.status = "descartado"
    audit.record(
        db, actor, "descartar", "ai_draft", draft.id,
        {"incidente": draft.incident_id, "tipo": draft.kind, "modelo": draft.model},
        audit.request_ip(request),
    )
    db.commit()
    db.refresh(draft)
    return present_draft(draft)

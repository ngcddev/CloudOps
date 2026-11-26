# Borradores del asistente para un incidente (spec 012): generar el resumen y el mensaje al cliente, ver los borradores, aprobar (con el
# texto editado) o descartar. Solo agencia: el cliente solo ve el mensaje ya aprobado, en el portal (dashboard). Nada sale sin aprobación.
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.deps import require_agency
from app.models.ai_draft import AiDraft
from app.models.incident import Incident
from app.models.project import Project
from app.models.service import Service
from app.models.user import User
from app.schemas.ai_draft import ApproveIn, DiagnosisIn, DraftOut, GenerateIn
from app.services import ai_drafts, aiops, audit
from app.services.incident_flow import IncidentFlowError

router = APIRouter(prefix="/api", tags=["borradores-ia"], dependencies=[Depends(require_agency)])


def _get_incident(db: Session, incident_id: int) -> Incident:
    incident = db.scalar(
        select(Incident)
        .options(selectinload(Incident.service).selectinload(Service.project).selectinload(Project.client), selectinload(Incident.events))
        .where(Incident.id == incident_id)
    )
    if incident is None:
        raise HTTPException(status_code=404, detail="El incidente no existe.")
    return incident


def _get_draft(db: Session, draft_id: int) -> AiDraft:
    borrador = db.get(AiDraft, draft_id)
    if borrador is None:
        raise HTTPException(status_code=404, detail="El borrador no existe.")
    return borrador


def _present(b: AiDraft) -> DraftOut:
    checks = b.checks or {}
    avisos = []
    if checks.get("motivo_texto_base"):
        avisos.append(f"{checks['motivo_texto_base']} Se dejó un texto base para que lo revises y lo edites.")
    if checks.get("terminos_prohibidos"):
        avisos.append(f"La IA usó términos técnicos que se rechazaron: {', '.join(checks['terminos_prohibidos'])}.")
    if checks.get("horas_que_no_coinciden"):
        avisos.append(f"La IA mencionó horas o tiempos que no son los del incidente: {', '.join(checks['horas_que_no_coinciden'])}.")
    if checks.get("citas_inexistentes"):
        avisos.append(f"La IA citó evidencia que no existe: {', '.join(checks['citas_inexistentes'])}.")
    if checks.get("sin_citas"):
        avisos.append("La IA no citó ninguna evidencia.")
    if checks.get("comandos_prohibidos"):
        avisos.append(f"La IA propuso cambios a mano que no se permiten: {', '.join(checks['comandos_prohibidos'])}.")
    return DraftOut(
        id=b.id, incident_id=b.incident_id, kind=b.kind, status=b.status, source=b.source, model=b.model, prompt_version=b.prompt_version,
        generated_text=b.generated_text, final_text=b.final_text, notice=" ".join(avisos) or None, latency_ms=b.latency_ms,
        approved_by=b.approved_by.name if b.approved_by is not None else None, approved_at=b.approved_at, created_at=b.created_at,
    )


@router.post("/incidents/{incident_id}/ai-drafts", response_model=list[DraftOut], status_code=201)
def generate(incident_id: int, body: GenerateIn | None = None, db: Session = Depends(get_db)):
    """Genera el resumen y el mensaje al cliente de un incidente mitigado. Si la IA no responde, deja un texto base para editar."""
    incident = _get_incident(db, incident_id)
    kinds = tuple(body.kinds) if body and body.kinds else ai_drafts.KINDS
    try:
        return [_present(b) for b in ai_drafts.generate(db, incident, kinds)]
    except IncidentFlowError as error:
        raise HTTPException(status_code=409, detail=str(error)) from None


@router.post("/incidents/{incident_id}/ai-diagnosis", response_model=DraftOut, status_code=201)
def diagnose(incident_id: int, body: DiagnosisIn | None = None, db: Session = Depends(get_db)):
    """Hipótesis de diagnóstico y borrador de runbook con la evidencia del incidente (métricas, registros y lo que se aporte). Sirve con el incidente abierto.

    Es un borrador: una persona lo edita y lo aprueba; la IA no ejecuta nada. Si no responde o su texto no pasa las verificaciones, queda un texto base.
    """
    return _present(aiops.diagnose(db, _get_incident(db, incident_id), body.evidence if body else None))


@router.get("/incidents/{incident_id}/ai-drafts", response_model=list[DraftOut])
def list_drafts(incident_id: int, db: Session = Depends(get_db)):
    """Todos los borradores del incidente, del más nuevo al más viejo."""
    _get_incident(db, incident_id)
    filas = db.scalars(
        select(AiDraft).options(selectinload(AiDraft.approved_by)).where(AiDraft.incident_id == incident_id).order_by(AiDraft.id.desc())
    ).all()
    return [_present(b) for b in filas]


@router.post("/ai-drafts/{draft_id}/approve", response_model=DraftOut)
def approve(draft_id: int, request: Request, body: ApproveIn | None = None, db: Session = Depends(get_db), user: User = Depends(require_agency)):
    """Aprueba el borrador con el texto que la persona editó; el mensaje al cliente no puede traer jerga ni horas que no coincidan."""
    try:
        return _present(ai_drafts.approve(db, _get_draft(db, draft_id), user, body.text if body else None, audit.request_ip(request)))
    except ai_drafts.DraftError as error:
        raise HTTPException(status_code=422, detail=str(error)) from None


@router.post("/ai-drafts/{draft_id}/discard", response_model=DraftOut)
def discard(draft_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(require_agency)):
    """Descarta el borrador: no llega a nadie."""
    try:
        return _present(ai_drafts.discard(db, _get_draft(db, draft_id), user, audit.request_ip(request)))
    except ai_drafts.DraftError as error:
        raise HTTPException(status_code=409, detail=str(error)) from None

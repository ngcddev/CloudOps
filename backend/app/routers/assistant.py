# Endpoints del asistente local de ayuda (spec 012): preguntar, opinar sobre la decisión de la compuerta, ver
# estadísticas y reindexar la ayuda para el RAG. Solo agencia: el cliente no ve jerga técnica (principio 8) y el asistente responde sobre el Hub.
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import require_agency
from app.models.ai_query import AiQuery
from app.models.user import User
from app.schemas.assistant import AskIn, AskOut, DriftOut, FeedbackIn, ReindexOut, StatsOut
from app.services import ai_drift, assistant, knowledge

router = APIRouter(prefix="/api/assistant", tags=["asistente"])


def _out(q: AiQuery) -> AskOut:
    return AskOut(
        id=q.id,
        answer=q.answer,
        answered_by="llm" if q.llm_woken else ("compuerta" if q.gate_label == "fuera_de_tema" else "ayuda"),
        gate_label=q.gate_label,
        p_fuera_de_tema=q.p_fuera_de_tema,
        llm_woken=q.llm_woken,
        llm_ok=q.llm_ok,
        model=q.model,
        latency_ms=q.latency_ms,
        context_sections=q.context_sections or [],
        context_mode=q.context_mode,
        retrieval_score=q.retrieval_score,
    )


@router.post("/ask", response_model=AskOut)
def ask(body: AskIn, user: User = Depends(require_agency), db: Session = Depends(get_db)):
    """Responde una pregunta sobre el Hub; la compuerta decide si hace falta despertar al LLM."""
    return _out(assistant.ask(db, user, body.question.strip()))


@router.post("/reindex", response_model=ReindexOut, dependencies=[Depends(require_agency)])
def reindex(db: Session = Depends(get_db)):
    """Vuelve a generar los embeddings de la ayuda del Hub (RAG). Necesita a Ollama con el modelo de embeddings."""
    resultado = knowledge.indexar(db)
    if resultado is None:
        raise HTTPException(status_code=503, detail="No se pudo indexar: Ollama no respondió o no tiene el modelo de embeddings.")
    return resultado


@router.post("/{query_id}/feedback", status_code=204)
def feedback(query_id: int, body: FeedbackIn, user: User = Depends(require_agency), db: Session = Depends(get_db)):
    """La persona dice si la pregunta era o no del tema; alimenta el reentrenamiento de la compuerta."""
    query = db.get(AiQuery, query_id)
    if query is None or query.user_id != user.id:
        raise HTTPException(status_code=404, detail="No encontramos esa consulta.")
    query.feedback_label = body.label
    db.commit()


@router.get("/stats", response_model=StatsOut, dependencies=[Depends(require_agency)])
def stats(db: Session = Depends(get_db)):
    """Cuántas veces se despertó el LLM, cuántas se evitaron y cuántas decisiones corrigió la gente."""
    return assistant.stats(db)


@router.get("/drift", response_model=DriftOut, dependencies=[Depends(require_agency)])
def drift(days: int = Query(default=7, ge=1, le=90), db: Session = Depends(get_db)):
    """Deriva del asistente: los últimos `days` días frente a los `days` anteriores, con los avisos que pasan su umbral (spec 020).

    Las rutas fijas van antes que `/{query_id}/feedback`, que solo es POST: no chocan.
    """
    return ai_drift.calcular(db, days)

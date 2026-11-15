# Endpoints del asistente local de ayuda (spec 012): preguntar, opinar sobre la decisión de la compuerta, ver
# estadísticas y reindexar la ayuda para el RAG. Solo agencia: el cliente no ve jerga técnica (principio 8) y el asistente responde sobre el Hub.
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import require_agency
from app.models.ai_query import AiQuery
from app.models.user import User
from app.integrations import voz
from app.schemas.assistant import AskIn, AskOut, DriftOut, FeedbackIn, ReindexOut, SpeakIn, StatsOut, TranscriptionOut, VoiceStatusOut
from app.services import ai_drift, assistant, knowledge, redaccion
from app.services.assistant_gate import ModeloAlterado

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
        secrets_redacted=getattr(q, "secretos_tapados", []),
    )


@router.post("/ask", response_model=AskOut)
def ask(body: AskIn, user: User = Depends(require_agency), db: Session = Depends(get_db)):
    """Responde una pregunta sobre el Hub; la compuerta decide si hace falta despertar al LLM."""
    try:
        return _out(assistant.ask(db, user, body.question.strip()))
    except ModeloAlterado:
        # La compuerta no pasó la verificación de integridad (spec 020): no se responde con un modelo que alguien modificó a mano
        raise HTTPException(status_code=503, detail="El modelo de la compuerta no pasó la verificación de integridad; avisa a Sistemas.") from None


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


# ---------- Voz (spec 021): hablarle al asistente y escuchar su respuesta ----------
# El audio pasa por la API hacia el servicio de voz y no se guarda en ninguna parte; de la voz solo queda, si la persona envía la pregunta, su texto ya sin secretos.
MAX_AUDIO_BYTES = 2_000_000


@router.get("/voice/status", response_model=VoiceStatusOut, dependencies=[Depends(require_agency)])
def voice_status():
    """Si la voz está configurada y responde; la pantalla muestra el micrófono solo si está disponible."""
    return voz.estado()


@router.post("/voice/transcribe", response_model=TranscriptionOut, dependencies=[Depends(require_agency)])
async def voice_transcribe(request: Request):
    """Convierte el audio del cuerpo (webm, ogg o wav, hasta 30 s) en texto. No envía la pregunta: la persona revisa la transcripción y la manda aparte."""
    audio = await request.body()
    if not audio:
        raise HTTPException(status_code=400, detail="No llegó audio.")
    if len(audio) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="El audio es demasiado grande: habla en frases de menos de 30 segundos.")
    try:
        resultado = voz.transcribir(audio, request.headers.get("content-type", ""))
    except voz.VozError as error:
        raise HTTPException(status_code=error.status, detail=error.detail) from None
    texto, secretos = redaccion.redactar(resultado.get("texto", ""))
    return TranscriptionOut(
        text=texto, duration_s=resultado.get("duracion_s", 0), elapsed_ms=resultado.get("tiempo_ms", 0), model=resultado.get("modelo", ""), secrets_redacted=secretos
    )


@router.post("/voice/speak", dependencies=[Depends(require_agency)], responses={200: {"content": {"audio/wav": {}}}})
def voice_speak(body: SpeakIn):
    """Lee un texto en voz alta (la respuesta del asistente) y devuelve el audio WAV."""
    texto, _ = redaccion.redactar(body.text)
    try:
        audio = voz.sintetizar(texto)
    except voz.VozError as error:
        raise HTTPException(status_code=error.status, detail=error.detail) from None
    return Response(content=audio, media_type="audio/wav")

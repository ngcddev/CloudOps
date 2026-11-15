# Orquesta una pregunta al asistente (spec 012): compuerta → (si corresponde) LLM → registro en ai_queries.
# La compuerta decide en milisegundos si la pregunta trata de la aplicación; el LLM solo se despierta si sí o si
# hay duda. Toda pregunta queda registrada, con o sin LLM, para medir ahorro, latencia y errores de la compuerta.
import time

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import telemetry
from app.config import settings
from app.integrations import ollama
from app.models.ai_query import AiQuery
from app.models.user import User
from app.services import assistant_context, knowledge
from app.services.assistant_gate import GateModel, load_model
from app.services.redaccion import redactar

PROMPT_VERSION = assistant_context.PROMPT_VERSION

RESPUESTA_FUERA_DE_TEMA = (
    "Solo puedo ayudarte con el uso del Hub: clientes, planes, tickets, prioridades, SLA, solicitudes de cambio, "
    "incidentes, rollback, dashboards y reportes. Reformula tu pregunta sobre alguno de esos temas."
)
RESPUESTA_IA_NO_DISPONIBLE = (
    "El asistente de IA local no respondió a tiempo. El resto del Hub funciona con normalidad: puedes consultar "
    "la pantalla correspondiente o intentarlo de nuevo en unos minutos."
)


def _contexto(db: Session, question: str, transport=None) -> tuple[list[assistant_context.Seccion], str, float | None]:
    """Contexto para el LLM según el modo configurado: (secciones, modo realmente usado, similitud del mejor trozo).

    En modo `rag`, si Ollama no puede dar embeddings o el índice no existe, se cae a la recuperación léxica y el modo
    usado queda como `recuperacion`: el asistente no se rompe por el RAG.
    """
    modo = settings.assistant_context_mode
    if modo == "rag":
        encontrado = knowledge.recuperar(db, question, transport=transport)
        if encontrado is not None:
            return encontrado.secciones, "rag", encontrado.mejor
        modo = "recuperacion"
    contexto = assistant_context.elegir_contexto(question, modo)
    if modo == "completo" and not assistant_context.contexto_completo_cabe():
        modo = "recuperacion"  # lo mismo que hace elegir_contexto cuando la ayuda ya no cabe entera
    return contexto, modo, None


def ask(db: Session, user: User, question: str, gate: GateModel | None = None, transport=None) -> AiQuery:
    """Procesa la pregunta y devuelve la fila registrada (hace commit)."""
    # Spec 020: una clave pegada en la pregunta no se guarda ni viaja al modelo; se tapa antes de cualquier otra cosa
    question, secretos = redactar(question)
    gate = gate or load_model()
    umbral = settings.assistant_gate_threshold or None
    tracer = telemetry.tracer()
    # Los spans llevan tiempos, estados y contadores; nunca el texto de la pregunta ni de la respuesta (principio 2)
    with tracer.start_as_current_span("assistant.compuerta") as span:
        decision = gate.decide(question, threshold=umbral)
        span.set_attributes({"gate.label": decision.label, "gate.p_fuera_de_tema": decision.p_fuera_de_tema, "gate.version": decision.model_version})

    modelo = prompt = llm_ok = latencia = modo_contexto = puntaje = None
    secciones: list[str] = []
    despierta = False
    if not decision.despertar_llm:
        respuesta = RESPUESTA_FUERA_DE_TEMA
    else:
        with tracer.start_as_current_span("assistant.contexto") as span:
            contexto, modo_contexto, puntaje = _contexto(db, question, transport)
            span.set_attributes({"context.mode": modo_contexto, "context.secciones": len(contexto)})
            if puntaje is not None:
                span.set_attribute("retrieval.score", puntaje)
        if not contexto:
            # Modo por secciones: del tema, pero la ayuda no dice nada parecido; no se llama al LLM para que no invente
            respuesta = assistant_context.SIN_INFORMACION
        else:
            despierta = True
            secciones = [sec.titulo for sec in contexto]
            inicio = time.monotonic()
            with tracer.start_as_current_span("assistant.llm") as span:
                texto = ollama.chat(assistant_context.mensaje_de_sistema(contexto), question, transport=transport)
                span.set_attributes({"llm.model": settings.ollama_model, "llm.ok": texto is not None, "llm.prompt_version": PROMPT_VERSION})
            latencia = int((time.monotonic() - inicio) * 1000)
            modelo, prompt, llm_ok = settings.ollama_model, PROMPT_VERSION, texto is not None
            respuesta = texto or RESPUESTA_IA_NO_DISPONIBLE

    registro = AiQuery(
        user_id=user.id,
        question=question,
        gate_label=decision.label,
        p_fuera_de_tema=decision.p_fuera_de_tema,
        gate_version=decision.model_version,
        llm_woken=despierta,
        model=modelo,
        prompt_version=prompt,
        llm_ok=llm_ok,
        latency_ms=latencia,
        answer=respuesta,
        context_sections=secciones,
        context_mode=modo_contexto,
        retrieval_score=puntaje,
    )
    db.add(registro)
    db.commit()
    db.refresh(registro)
    # No es una columna: solo avisa a quien pregunta que se taparon secretos (el aviso no se guarda)
    registro.secretos_tapados = secretos
    return registro


def stats(db: Session) -> dict:
    """Indicadores de la compuerta y del LLM; `llm_evitado_pct` es el ahorro real medido en uso."""
    total = db.scalar(select(func.count(AiQuery.id))) or 0
    despertados = db.scalar(select(func.count(AiQuery.id)).where(AiQuery.llm_woken.is_(True))) or 0
    fallidos = db.scalar(select(func.count(AiQuery.id)).where(AiQuery.llm_ok.is_(False))) or 0
    latencia = db.scalar(select(func.avg(AiQuery.latency_ms)).where(AiQuery.llm_ok.is_(True)))
    opinadas = db.scalar(select(func.count(AiQuery.id)).where(AiQuery.feedback_label.is_not(None))) or 0
    erradas = (
        db.scalar(select(func.count(AiQuery.id)).where(AiQuery.feedback_label.is_not(None), AiQuery.feedback_label != AiQuery.gate_label))
        or 0
    )
    return {
        "total": total,
        "llm_despertado": despertados,
        "llm_evitado": total - despertados,
        "llm_evitado_pct": round(100 * (total - despertados) / total, 1) if total else None,
        "llm_sin_respuesta": fallidos,
        "latencia_llm_ms": round(latencia) if latencia is not None else None,
        "con_opinion": opinadas,
        # Deriva: decisiones de la compuerta que la persona corrigió; si sube, toca reentrenar
        "decisiones_corregidas": erradas,
        "decisiones_corregidas_pct": round(100 * erradas / opinadas, 1) if opinadas else None,
    }

# Deriva del asistente (spec 020, T03; MLOps del módulo 5): compara dos ventanas de tiempo seguidas de `ai_queries` (la actual y la anterior) y avisa cuando
# cambió lo que la gente pregunta, cuando corrige más las decisiones de la compuerta, cuando el LLM tarda más o cuando falla. Las cuentas son SQL simple y los umbrales
# están a la vista; con pocos datos no se avisa (datos insuficientes). Es la señal para reentrenar la compuerta o revisar el prompt, no una acción automática.
from datetime import datetime, timedelta, timezone

from sqlalchemy import Float, cast, func, select
from sqlalchemy.orm import Session

from app.models.ai_query import AiQuery

# Umbrales: por debajo de las muestras mínimas no se avisa de ese indicador
MIN_CONSULTAS = 20  # para comparar el reparto de etiquetas entre ventanas
MIN_OPINIONES = 10  # para fiarse del porcentaje de decisiones corregidas
MIN_LLM = 5  # para comparar la latencia del LLM
CORREGIDAS_PCT = 15.0  # decisiones corregidas por la gente: desde aquí toca reentrenar
CAMBIO_FUERA_DE_TEMA_PUNTOS = 20.0  # cambio del porcentaje de preguntas fuera de tema entre ventanas
LATENCIA_VECES = 1.5  # el LLM tarda al menos 1,5 veces lo de la ventana anterior
FALLOS_LLM_PCT = 20.0  # respuestas del LLM que fallaron


def _utc(valor: datetime) -> datetime:
    return valor if valor.tzinfo else valor.replace(tzinfo=timezone.utc)


def _ventana(db: Session, desde: datetime, hasta: datetime) -> dict:
    """Indicadores de las consultas con `desde <= creada < hasta`."""
    en_ventana = (AiQuery.created_at >= desde, AiQuery.created_at < hasta)
    total = db.scalar(select(func.count(AiQuery.id)).where(*en_ventana)) or 0
    fuera = db.scalar(select(func.count(AiQuery.id)).where(*en_ventana, AiQuery.gate_label == "fuera_de_tema")) or 0
    opinadas = db.scalar(select(func.count(AiQuery.id)).where(*en_ventana, AiQuery.feedback_label.is_not(None))) or 0
    corregidas = db.scalar(select(func.count(AiQuery.id)).where(*en_ventana, AiQuery.feedback_label.is_not(None), AiQuery.feedback_label != AiQuery.gate_label)) or 0
    llm = db.scalar(select(func.count(AiQuery.id)).where(*en_ventana, AiQuery.llm_woken.is_(True))) or 0
    llm_fallidos = db.scalar(select(func.count(AiQuery.id)).where(*en_ventana, AiQuery.llm_woken.is_(True), AiQuery.llm_ok.is_(False))) or 0
    latencia = db.scalar(select(func.avg(cast(AiQuery.latency_ms, Float))).where(*en_ventana, AiQuery.llm_ok.is_(True)))
    pct = lambda parte, todo: round(100 * parte / todo, 1) if todo else None  # noqa: E731
    return {
        "desde": desde, "hasta": hasta, "consultas": total, "fuera_de_tema_pct": pct(fuera, total), "con_opinion": opinadas,
        "corregidas_pct": pct(corregidas, opinadas), "llm_consultas": llm, "llm_fallidas_pct": pct(llm_fallidos, llm),
        "latencia_llm_ms": round(latencia) if latencia is not None else None,
    }


def calcular(db: Session, dias: int = 7, ahora: datetime | None = None) -> dict:
    """Ventana actual (los últimos `dias`) frente a la anterior, con los avisos que corresponden."""
    ahora = _utc(ahora or datetime.now(timezone.utc))
    corte = ahora - timedelta(days=dias)
    actual = _ventana(db, corte, ahora + timedelta(seconds=1))
    anterior = _ventana(db, corte - timedelta(days=dias), corte)
    avisos: list[dict] = []

    if actual["con_opinion"] >= MIN_OPINIONES and actual["corregidas_pct"] >= CORREGIDAS_PCT:
        avisos.append({"codigo": "decisiones_corregidas", "mensaje": f"La gente corrigió el {actual['corregidas_pct']} % de las decisiones de la compuerta (umbral {CORREGIDAS_PCT:g} %): conviene reentrenarla con esas correcciones."})
    if actual["consultas"] >= MIN_CONSULTAS and anterior["consultas"] >= MIN_CONSULTAS:
        cambio = abs(actual["fuera_de_tema_pct"] - anterior["fuera_de_tema_pct"])
        if cambio >= CAMBIO_FUERA_DE_TEMA_PUNTOS:
            avisos.append({"codigo": "cambio_de_temas", "mensaje": f"Cambió lo que preguntan: las preguntas fuera de tema pasaron del {anterior['fuera_de_tema_pct']} % al {actual['fuera_de_tema_pct']} %."})
    if actual["llm_consultas"] >= MIN_LLM and anterior["llm_consultas"] >= MIN_LLM and actual["latencia_llm_ms"] and anterior["latencia_llm_ms"]:
        if actual["latencia_llm_ms"] >= LATENCIA_VECES * anterior["latencia_llm_ms"]:
            avisos.append({"codigo": "llm_mas_lento", "mensaje": f"El LLM tarda {actual['latencia_llm_ms']} ms, {LATENCIA_VECES:g} veces o más que los {anterior['latencia_llm_ms']} ms de la ventana anterior."})
    if actual["llm_consultas"] >= MIN_LLM and actual["llm_fallidas_pct"] >= FALLOS_LLM_PCT:
        avisos.append({"codigo": "llm_fallando", "mensaje": f"El {actual['llm_fallidas_pct']} % de las respuestas del LLM fallaron (umbral {FALLOS_LLM_PCT:g} %): revisar Ollama."})

    suficiente = actual["consultas"] >= MIN_CONSULTAS or actual["con_opinion"] >= MIN_OPINIONES or actual["llm_consultas"] >= MIN_LLM
    return {"ventana_dias": dias, "estado": "atencion" if avisos else ("ok" if suficiente else "sin_datos"), "actual": actual, "anterior": anterior, "avisos": avisos}

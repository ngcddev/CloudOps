# Esquemas del asistente local (spec 012): pregunta, respuesta con la decisión de la compuerta, opinión y estadísticas.
from typing import Literal

from pydantic import BaseModel, Field


class AskIn(BaseModel):
    question: str = Field(min_length=3, max_length=500)


class AskOut(BaseModel):
    id: int
    answer: str
    # Quién respondió: la compuerta (ajena al Hub), la ayuda («sin información», sin LLM) o el LLM local
    answered_by: Literal["compuerta", "ayuda", "llm"]
    gate_label: Literal["en_tema", "fuera_de_tema"]
    p_fuera_de_tema: float
    llm_woken: bool
    # Falso si se llamó al LLM y no respondió (el texto ya explica la alternativa)
    llm_ok: bool | None
    model: str | None
    latency_ms: int | None
    # Secciones de la ayuda en las que se basó la respuesta
    context_sections: list[str]
    # Cómo se eligió ese contexto (el RAG puede caer a la recuperación léxica) y la similitud del mejor trozo
    context_mode: Literal["completo", "recuperacion", "rag"] | None = None
    retrieval_score: float | None = None


class ReindexOut(BaseModel):
    documentos: int
    trozos: int
    # Modelo de embeddings con el que quedó el índice
    modelo: str


class FeedbackIn(BaseModel):
    # Lo que la pregunta era en realidad; si difiere de la decisión de la compuerta, queda como error a corregir
    label: Literal["en_tema", "fuera_de_tema"]


class StatsOut(BaseModel):
    total: int
    llm_despertado: int
    llm_evitado: int
    llm_evitado_pct: float | None
    llm_sin_respuesta: int
    latencia_llm_ms: int | None
    con_opinion: int
    decisiones_corregidas: int
    decisiones_corregidas_pct: float | None

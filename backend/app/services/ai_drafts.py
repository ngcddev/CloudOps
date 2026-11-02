# Genera los borradores de un incidente con el asistente y los controla antes de guardarlos (spec 012, T05).
# El asistente es intercambiable (`DraftWriter`): en las pruebas es tests/fake_ollama.py y en el módulo 5
# será integrations/ollama.py. Lo que redacte queda siempre como `borrador_ia` (principio 6).
import time
from dataclasses import dataclass, field
from typing import Protocol

from sqlalchemy.orm import Session

from app.models.ai_draft import AiDraft
from app.models.incident import Incident
from app.services.ai_checks import forbidden_terms, invented_times
from app.services.ai_context import incident_facts

# Orden en que se piden: primero el resumen técnico (agencia) y luego el mensaje al cliente
KINDS = ("resumen", "mensaje_cliente")
KIND_LABELS = {"resumen": "El resumen", "mensaje_cliente": "El mensaje al cliente"}


class WriterError(Exception):
    """El asistente no respondió a tiempo o no está disponible: el técnico escribe a mano (CA-5)."""


@dataclass
class WriterResult:
    text: str
    # Modelo que redactó el texto (p. ej. `qwen2.5:7b`)
    model: str
    # Versión de las instrucciones usadas (`v1`), la de ai/prompts/
    prompt_version: str


class DraftWriter(Protocol):
    """Lo único que el Hub le pide al asistente: un texto de cierto tipo a partir de los hechos del incidente."""

    def write(self, kind: str, facts: dict) -> WriterResult: ...


@dataclass
class DraftsResult:
    drafts: list[AiDraft] = field(default_factory=list)
    # Textos que el asistente redactó pero no pasaron los controles, con la razón para el técnico
    problems: list[str] = field(default_factory=list)


def check_text(kind: str, text: str, facts: dict) -> str | None:
    """Razón por la que el texto no sirve, o None si pasa los controles de su tipo.

    Las horas se revisan en los dos tipos (CA-2); la jerga solo en el mensaje al cliente, porque el resumen
    lo lee la agencia y puede ser técnico (CA-3).
    """
    if not text.strip():
        return f"{KIND_LABELS[kind]} llegó vacío."
    invented = invented_times(text, facts)
    if invented:
        return f"{KIND_LABELS[kind]} cita horas que no son del incidente: {', '.join(invented)}."
    if kind == "mensaje_cliente":
        jerga = forbidden_terms(text)
        if jerga:
            return f"{KIND_LABELS[kind]} usa términos técnicos que el cliente no debe ver: {', '.join(jerga)}."
    return None


def generate_drafts(db: Session, incident: Incident, writer: DraftWriter) -> DraftsResult:
    """Pide el resumen y el mensaje, guarda como `borrador_ia` los que pasan los controles y no hace commit.

    Si el asistente falla, `WriterError` sube sin dejar nada a medias en la sesión: el router responde que
    se escriba a mano y el incidente sigue igual.
    """
    facts = incident_facts(incident)
    result = DraftsResult()
    pending: list[AiDraft] = []
    for kind in KINDS:
        started = time.monotonic()
        answer = writer.write(kind, facts)
        latency_ms = int((time.monotonic() - started) * 1000)
        text = answer.text.strip()
        problem = check_text(kind, text, facts)
        if problem is not None:
            result.problems.append(problem)
            continue
        pending.append(
            AiDraft(
                incident_id=incident.id,
                kind=kind,
                status="borrador_ia",
                model=answer.model,
                prompt_version=answer.prompt_version,
                generated_text=text,
                latency_ms=latency_ms,
            )
        )
    for draft in pending:
        db.add(draft)
    db.flush()
    result.drafts = pending
    return result

# Pruebas de las trazas del Hub (OpenTelemetry): sin endpoint no hacen nada; con un exportador en memoria, las peticiones y las etapas del
# asistente generan spans, y ningún span lleva el texto de las preguntas ni de las respuestas (principio 2).
import json

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from app import telemetry
from app.config import settings
from app.main import app


@pytest.fixture(scope="module")
def spans():
    """Un proveedor global en memoria para las etapas del asistente (el proveedor global solo se puede fijar una vez por proceso)."""
    exportador = InMemorySpanExporter()
    proveedor = TracerProvider()
    proveedor.add_span_processor(SimpleSpanProcessor(exportador))
    trace.set_tracer_provider(proveedor)
    return exportador


@pytest.fixture(autouse=True)
def limpiar(spans):
    spans.clear()
    yield
    spans.clear()


@pytest.fixture
def client(as_agency):
    return as_agency


@pytest.fixture
def ollama_responde(monkeypatch):
    monkeypatch.setattr(settings, "ollama_url", "http://ollama.test:11434")
    monkeypatch.setattr(
        "app.integrations.ollama.urllib_transport",
        lambda url, body, timeout: (200, json.dumps({"message": {"content": "Respuesta secreta del asistente."}}).encode()),
    )


def nombres(spans) -> list[str]:
    """Los spans del asistente (FastAPI también genera los suyos propios, como `fastapi.dependencies`)."""
    return [s.name for s in spans.get_finished_spans() if s.name.startswith("assistant.")]


def test_sin_endpoint_las_trazas_no_se_activan(monkeypatch):
    monkeypatch.setattr(settings, "otel_exporter_otlp_endpoint", "")

    assert telemetry.configure(app) is None
    assert getattr(app, "_is_instrumented_by_opentelemetry", False) is False


def test_una_pregunta_del_tema_deja_un_span_por_etapa(client, ollama_responde, spans):
    client.post("/api/assistant/ask", json={"question": "¿Cómo hago un rollback?"})

    assert nombres(spans) == ["assistant.compuerta", "assistant.contexto", "assistant.llm"]
    por_nombre = {s.name: dict(s.attributes) for s in spans.get_finished_spans() if s.name.startswith("assistant.")}
    assert por_nombre["assistant.compuerta"]["gate.label"] == "en_tema"
    assert por_nombre["assistant.contexto"]["context.mode"] == "completo" and por_nombre["assistant.contexto"]["context.secciones"] > 0
    assert por_nombre["assistant.llm"]["llm.ok"] is True and por_nombre["assistant.llm"]["llm.prompt_version"] == "v3"


def test_una_pregunta_ajena_no_deja_span_del_llm(client, ollama_responde, spans):
    client.post("/api/assistant/ask", json={"question": "¿Cuál es la capital de Francia?"})

    assert nombres(spans) == ["assistant.compuerta"]


def test_los_spans_no_llevan_el_texto_de_la_pregunta_ni_de_la_respuesta(client, ollama_responde, spans):
    client.post("/api/assistant/ask", json={"question": "¿Cómo hago un rollback del sitio de Pedro Pérez?"})

    todo = json.dumps([dict(s.attributes) for s in spans.get_finished_spans()], default=str).lower()
    for texto in ("pedro", "pérez", "rollback", "secreta", "respuesta"):
        assert texto not in todo


def test_con_un_exportador_la_api_genera_spans_de_cada_ruta(client, spans):
    exportador = InMemorySpanExporter()
    proveedor = telemetry.configure(app, exporter=exportador)
    app.middleware_stack = None  # en producción se instrumenta al importar; aquí la app ya sirvió peticiones y hay que reconstruir el stack
    try:
        assert proveedor is not None
        client.get("/api/plans")
        client.get("/health")
        client.get("/livez")
        proveedor.force_flush()
        rutas = [s.attributes.get("http.route") for s in exportador.get_finished_spans() if s.attributes.get("http.route")]
        assert "/api/plans" in rutas
        assert "/health" not in rutas and "/livez" not in rutas  # el clúster los consulta cada pocos segundos: se excluyen
    finally:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.uninstrument_app(app)
        app.middleware_stack = None

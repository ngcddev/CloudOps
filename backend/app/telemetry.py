# Trazas del Hub con OpenTelemetry (spec 008/012): cada petición a la API y las etapas del asistente (compuerta, contexto, LLM) quedan como
# spans que se mandan por OTLP/HTTP a Tempo, y Grafana los muestra. Las consultas SQL no se instrumentan: la instrumentación de SQLAlchemy de
# OpenTelemetry soporta hasta la 2.0 y el Hub usa la 2.1 (no instrumenta nada); cuando la soporte, se suma aquí. Solo se activa si OTEL_EXPORTER_OTLP_ENDPOINT está
# definido; sin él todo esto es un no-op y la API no cambia. Privacidad (principio 2): los spans llevan tiempos, estados y contadores, nunca
# el texto de las preguntas ni de las respuestas del asistente, ni el cuerpo de las peticiones.
from opentelemetry import trace

from app.config import settings

NOMBRE = "hub-api"


def tracer() -> trace.Tracer:
    """El tracer de la aplicación; sin telemetría configurada devuelve uno que no hace nada."""
    return trace.get_tracer(NOMBRE)


def configurar(app, exporter=None):
    """Activa las trazas y devuelve el proveedor de trazas; sin endpoint (ni exportador de prueba) no hace nada y devuelve None.

    `exporter` permite a las pruebas inyectar uno en memoria en lugar del exportador OTLP.
    """
    endpoint = settings.otel_exporter_otlp_endpoint.rstrip("/")
    if exporter is None:
        if not endpoint:
            return None
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

        exporter = OTLPSpanExporter(endpoint=f"{endpoint}/v1/traces", timeout=5)

    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    proveedor = TracerProvider(resource=Resource.create({"service.name": NOMBRE, "deployment.environment": "laboratorio"}))
    proveedor.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(proveedor)
    # /health lo consulta el clúster cada pocos segundos: no aporta nada y llenaría Tempo
    FastAPIInstrumentor.instrument_app(app, tracer_provider=proveedor, excluded_urls="health")
    return proveedor

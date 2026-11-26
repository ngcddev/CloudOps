# Registros de la API (spec 022, T26; auditoría OB-04): una línea JSON por evento en la salida estándar, con el id de la petición y el `trace_id` de la traza de
# Tempo. Antes los `logger.info` no salían (sin handler) y un 500 no se podía seguir de un log a su traza. Alloy recoge esta salida y la manda a Loki.
# Privacidad (principio 2): se registra el método, la ruta SIN la cadena de consulta, el estado y la duración; nunca cuerpos, cabeceras ni parámetros.
import contextvars
import json
import logging
import logging.config
import re
import time
import uuid

from opentelemetry import trace

# El id de la petición en curso; fuera de una petición queda vacío
request_id: contextvars.ContextVar[str] = contextvars.ContextVar("id_de_peticion", default="")

# Un id que llega en `X-Request-ID` solo se acepta si parece un id: así no entra texto libre (ni saltos de línea) a los registros
_VALID_ID = re.compile(r"^[A-Za-z0-9._-]{8,64}$")
# Los sondeos del clúster llegan cada pocos segundos y no se registran como eventos normales
_PROBE_PATHS = ("/health", "/livez")

log = logging.getLogger("hub.peticiones")


class JsonFormatter(logging.Formatter):
    """Una línea JSON por registro: hora UTC, nivel, origen, mensaje, id de petición y, si hay una traza activa, su `trace_id` y `span_id`."""

    def format(self, record: logging.LogRecord) -> str:
        """Convierte el registro en una línea JSON con nivel, mensaje, id de petición y traza."""
        datos = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created)) + f".{int(record.msecs):03d}Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if (rid := request_id.get()):
            datos["request_id"] = rid
        contexto = trace.get_current_span().get_span_context()
        if contexto.is_valid:
            datos["trace_id"] = format(contexto.trace_id, "032x")
            datos["span_id"] = format(contexto.span_id, "016x")
        # Campos propios de la llamada (`extra={"evento": {...}}`), ya saneados por quien registra
        if isinstance(extra := getattr(record, "evento", None), dict):
            datos.update({k: v for k, v in extra.items() if k not in datos})
        if record.exc_info:
            datos["exc"] = self.formatException(record.exc_info)
        return json.dumps(datos, ensure_ascii=False)


def configure_logging(nivel: str = "INFO") -> None:
    """Deja la salida estándar con registros JSON. Idempotente. Uvicorn registra el acceso con la cadena de consulta: se apaga y lo reemplaza el middleware."""
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {"json": {"()": JsonFormatter}},
            "handlers": {"salida": {"class": "logging.StreamHandler", "formatter": "json", "stream": "ext://sys.stdout"}},
            "root": {"level": nivel, "handlers": ["salida"]},
            "loggers": {
                "uvicorn": {"handlers": ["salida"], "level": nivel, "propagate": False},
                "uvicorn.error": {"handlers": ["salida"], "level": nivel, "propagate": False},
                "uvicorn.access": {"handlers": [], "level": "WARNING", "propagate": False},
            },
        }
    )


class RequestIdMiddleware:
    """Middleware ASGI: toma `X-Request-ID` si es válido (o crea uno), lo deja disponible para los registros, lo devuelve en la respuesta y registra la petición."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        recibido = dict(scope["headers"]).get(b"x-request-id", b"").decode("latin-1")
        rid = recibido if _VALID_ID.match(recibido) else uuid.uuid4().hex
        ficha = request_id.set(rid)
        inicio = time.perf_counter()
        estado = 500

        async def send_with_id(mensaje):
            nonlocal estado
            if mensaje["type"] == "http.response.start":
                estado = mensaje["status"]
                mensaje = {**mensaje, "headers": [*mensaje.get("headers", []), (b"x-request-id", rid.encode())]}
            await send(mensaje)

        try:
            await self.app(scope, receive, send_with_id)
        except Exception:
            # Un error sin atrapar: queda registrado con el mismo id (y la misma traza) con que se responde; Starlette devuelve el 500
            log.exception("Error sin atrapar", extra={"evento": self._event(scope, 500, inicio)})
            raise
        else:
            nivel = logging.DEBUG if scope["path"] in _PROBE_PATHS else (logging.WARNING if estado >= 500 else logging.INFO)
            log.log(nivel, "petición", extra={"evento": self._event(scope, estado, inicio)})
        finally:
            request_id.reset(ficha)

    @staticmethod
    def _event(scope, estado: int, inicio: float) -> dict:
        # `scope["path"]` no incluye la cadena de consulta: ni filtros ni identificadores que lleguen en ella se registran
        return {"method": scope["method"], "path": scope["path"], "status": estado, "ms": round((time.perf_counter() - inicio) * 1000, 1)}

# Cliente del servicio de voz (spec 021, T02): voz a texto y texto a voz. Igual que Ollama, es opcional: con VOZ_URL vacía (o con el servicio caído) la API responde que la voz no
# está disponible y el asistente sigue por texto. El audio se reenvía tal cual y no se guarda en ninguna parte.
import json
import urllib.request

from app.config import settings
from app.integrations.http import Transport, urllib_transport

# La primera transcripción carga el modelo (unos segundos); el resto tarda menos de 2 s
TIMEOUT_TRANSCRIBIR = 60.0
TIMEOUT_HABLAR = 30.0
TIMEOUT_ESTADO = 2.0


class VozError(Exception):
    """El servicio de voz respondió con un error o no respondió; `status` es el código que la API debe devolver."""

    def __init__(self, status: int, detail: str):
        super().__init__(detail)
        self.status, self.detail = status, detail


def habilitada() -> bool:
    return bool(settings.voz_url)


def _peticion(ruta: str, cuerpo: bytes | None, tipo: str | None) -> urllib.request.Request:
    cabeceras = {"Content-Type": tipo} if tipo else {}
    if settings.voz_token:
        cabeceras["X-Voz-Token"] = settings.voz_token
    return urllib.request.Request(f"{settings.voz_url}{ruta}", data=cuerpo, headers=cabeceras, method="POST" if cuerpo is not None else "GET")


def _enviar(ruta: str, cuerpo: bytes | None, tipo: str | None, timeout: float, transport: Transport | None) -> bytes:
    if not habilitada():
        raise VozError(503, "La voz no está disponible: el servicio de voz no está configurado.")
    try:
        status, respuesta = (transport or urllib_transport)(_peticion(ruta, cuerpo, tipo), timeout)
    except Exception:
        raise VozError(503, "El servicio de voz no respondió.") from None
    if status == 200:
        return respuesta
    try:
        detalle = json.loads(respuesta).get("detail", "")
    except Exception:
        detalle = ""
    # El servicio ya habla español y no revela rutas; se pasan sus avisos de tamaño, duración y turno ocupado
    if status in (400, 413, 422, 429):
        raise VozError(status, str(detalle) or "El servicio de voz rechazó la petición.")
    raise VozError(503, "El servicio de voz no está disponible.")


def estado(transport: Transport | None = None) -> dict:
    """{habilitada, disponible}: si hay URL configurada y el servicio responde en /health."""
    if not habilitada():
        return {"habilitada": False, "disponible": False}
    try:
        _enviar("/health", None, None, TIMEOUT_ESTADO, transport)
        return {"habilitada": True, "disponible": True}
    except VozError:
        return {"habilitada": True, "disponible": False}


def transcribir(audio: bytes, tipo: str, transport: Transport | None = None) -> dict:
    """{texto, duracion_s, tiempo_ms, modelo} del audio dado."""
    return json.loads(_enviar("/stt", audio, tipo or "application/octet-stream", TIMEOUT_TRANSCRIBIR, transport))


def sintetizar(texto: str, transport: Transport | None = None) -> bytes:
    """El audio WAV con el texto leído."""
    return _enviar("/tts", json.dumps({"texto": texto}).encode("utf-8"), "application/json", TIMEOUT_HABLAR, transport)

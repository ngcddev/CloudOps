# Cliente del servicio de voz (spec 021, T02): voz a texto y texto a voz. Igual que Ollama, es opcional: con VOZ_URL vacía (o con el servicio caído) la API responde que la voz no
# está disponible y el asistente sigue por texto. El audio se reenvía tal cual y no se guarda en ninguna parte.
import json
import urllib.request

from app.config import settings
from app.integrations.http import Transport, urllib_transport

# La primera transcripción carga el modelo (unos segundos); el resto tarda menos de 2 s
TIMEOUT_TRANSCRIBE = 60.0
TIMEOUT_SPEAK = 30.0
TIMEOUT_STATUS = 2.0


class VoiceError(Exception):
    """El servicio de voz respondió con un error o no respondió; `status` es el código que la API debe devolver."""

    def __init__(self, status: int, detail: str):
        super().__init__(detail)
        self.status, self.detail = status, detail


def enabled() -> bool:
    return bool(settings.voz_url)


def _request(ruta: str, cuerpo: bytes | None, tipo: str | None) -> urllib.request.Request:
    cabeceras = {"Content-Type": tipo} if tipo else {}
    if settings.voz_token:
        cabeceras["X-Voz-Token"] = settings.voz_token
    return urllib.request.Request(f"{settings.voz_url}{ruta}", data=cuerpo, headers=cabeceras, method="POST" if cuerpo is not None else "GET")


def _send(ruta: str, cuerpo: bytes | None, tipo: str | None, timeout: float, transport: Transport | None) -> bytes:
    if not enabled():
        raise VoiceError(503, "La voz no está disponible: el servicio de voz no está configurado.")
    try:
        status, respuesta = (transport or urllib_transport)(_request(ruta, cuerpo, tipo), timeout)
    except Exception:
        raise VoiceError(503, "El servicio de voz no respondió.") from None
    if status == 200:
        return respuesta
    try:
        detalle = json.loads(respuesta).get("detail", "")
    except Exception:
        detalle = ""
    # El servicio ya habla español y no revela rutas; se pasan sus avisos de tamaño, duración y turno ocupado
    if status in (400, 413, 422, 429):
        raise VoiceError(status, str(detalle) or "El servicio de voz rechazó la petición.")
    raise VoiceError(503, "El servicio de voz no está disponible.")


def get_status(transport: Transport | None = None) -> dict:
    """{habilitada, disponible}: si hay URL configurada y el servicio responde en /health."""
    if not enabled():
        return {"habilitada": False, "disponible": False}
    try:
        _send("/health", None, None, TIMEOUT_STATUS, transport)
        return {"habilitada": True, "disponible": True}
    except VoiceError:
        return {"habilitada": True, "disponible": False}


def transcribe(audio: bytes, tipo: str, transport: Transport | None = None) -> dict:
    """{texto, duracion_s, tiempo_ms, modelo} del audio dado."""
    return json.loads(_send("/stt", audio, tipo or "application/octet-stream", TIMEOUT_TRANSCRIBE, transport))


def synthesize(texto: str, transport: Transport | None = None) -> bytes:
    """El audio WAV con el texto leído."""
    return _send("/tts", json.dumps({"texto": texto}).encode("utf-8"), "application/json", TIMEOUT_SPEAK, transport)

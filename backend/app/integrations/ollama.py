# Llamada HTTP a Ollama (PC B) para el asistente (spec 012). Solo se llama cuando la compuerta lo despierta.
# Nunca lanza: si Ollama está apagado, tarda o responde mal, devuelve `None` y el Hub sigue funcionando
# (principio 6: el flujo completo funciona aunque la IA esté apagada).
import json
from collections.abc import Callable

from app.config import settings

# transport(url, cuerpo, timeout) -> (código HTTP, cuerpo)
Transport = Callable[[str, bytes, float], tuple[int, bytes]]


def urllib_transport(url: str, body: bytes, timeout: float) -> tuple[int, bytes]:
    """POST JSON con urllib; un error HTTP (4xx/5xx) se devuelve como código, no como excepción."""
    import urllib.error
    import urllib.request

    from app.integrations.http import validar_esquema

    request = urllib.request.Request(validar_esquema(url), data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        # bandit B310: esquema validado en la línea anterior
        with urllib.request.urlopen(request, timeout=timeout) as response:  # nosec B310
            return response.status, response.read()
    except urllib.error.HTTPError as error_:
        return error_.code, error_.read()


# Respuestas deterministas y cortas: es un asistente de ayuda, no un generador creativo (menos margen de error)
OPCIONES = {"temperature": 0, "top_p": 0.1, "seed": 7, "num_ctx": 8192, "num_predict": 350}


def build_payload(system: str, question: str, model: str, keep_alive: str) -> dict:
    """Cuerpo de /api/chat; lo comparten el Hub y el script de evaluación para medir lo que de verdad se usa."""
    return {
        "model": model,
        "stream": False,
        # Libera la VRAM pronto: el PC B comparte GPU con ComfyUI (spec 014)
        "keep_alive": keep_alive,
        "options": OPCIONES,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": question}],
    }


def chat(system: str, question: str, transport: Transport | None = None) -> str | None:
    """Respuesta del modelo local, o `None` si Ollama no está configurado o no respondió a tiempo."""
    if not settings.ollama_url:
        return None
    payload = build_payload(system, question, settings.ollama_model, settings.ollama_keep_alive)
    try:
        status, body = (transport or urllib_transport)(
            f"{settings.ollama_url}/api/chat", json.dumps(payload).encode("utf-8"), float(settings.assistant_timeout_seconds)
        )
        if status != 200:
            return None
        texto = json.loads(body).get("message", {}).get("content", "").strip()
        return texto or None
    except Exception:
        return None


def embed(textos: list[str], transport: Transport | None = None) -> list[list[float]] | None:
    """Embeddings de los textos con el modelo de embeddings de Ollama (`/api/embed`, un vector por texto).

    Igual que `chat`, nunca lanza: devuelve `None` si Ollama no está configurado, no responde o devuelve algo inesperado,
    y el asistente cae a la recuperación léxica.
    """
    if not settings.ollama_url or not textos:
        return None
    cuerpo = {"model": settings.ollama_embed_model, "input": textos, "keep_alive": settings.ollama_keep_alive}
    try:
        status, body = (transport or urllib_transport)(
            f"{settings.ollama_url}/api/embed", json.dumps(cuerpo).encode("utf-8"), float(settings.assistant_timeout_seconds)
        )
        if status != 200:
            return None
        vectores = json.loads(body).get("embeddings")
        if not isinstance(vectores, list) or len(vectores) != len(textos):
            return None
        if not all(isinstance(v, list) and v and all(isinstance(x, (int, float)) for x in v) for v in vectores):
            return None
        return [[float(x) for x in v] for v in vectores]
    except Exception:
        return None

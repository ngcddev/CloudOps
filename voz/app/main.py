# Servicio de voz del Hub (spec 021, T01): voz a texto (faster-whisper) y texto a voz (Piper), los dos en CPU y sin servicios externos (principio 2).
# Lo llama la API del Hub con VOZ_URL, igual que a Ollama; si el servicio no está, el asistente sigue funcionando por texto.
#   GET  /health  estado y modelos cargados
#   POST /stt     cuerpo = audio (webm, ogg, wav…) → {texto, duracion_s, tiempo_ms, modelo}; el vocabulario del Hub sesga el reconocimiento («rollback», «SLA»…)
#   POST /tts     {"texto": "..."} → audio/wav
# No guarda audio ni escribe texto en los registros. Límites de tamaño, duración y caracteres para que una petición no agote la memoria; una sola
# transcripción a la vez. Con VOZ_TOKEN definido, exige la cabecera X-Voz-Token (el servicio solo debe ser alcanzable desde la API del Hub).
import hmac
import io
import os
import re
import threading
import time
import wave
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field

MODELOS = Path(os.environ.get("VOZ_MODELOS", "/modelos"))
WHISPER_MODELO = os.environ.get("WHISPER_MODELO", "small")
VOCABULARIO = Path(os.environ.get("VOZ_VOCABULARIO", "/app/vocabulario.txt"))
TOKEN = os.environ.get("VOZ_TOKEN", "")
MAX_BYTES = int(os.environ.get("VOZ_MAX_BYTES", str(2_000_000)))
MAX_SEGUNDOS = float(os.environ.get("VOZ_MAX_SEGUNDOS", "30"))
MAX_CARACTERES = int(os.environ.get("VOZ_MAX_CARACTERES", "700"))
HILOS = int(os.environ.get("VOZ_HILOS", "4"))

app = FastAPI(title="Servicio de voz del Hub", docs_url=None, redoc_url=None)
_candado_carga = threading.Lock()
_una_transcripcion = threading.Semaphore(1)
_whisper = None
_piper = None


class TtsIn(BaseModel):
    texto: str = Field(min_length=1, max_length=5000)


def _autorizar(peticion: Request) -> None:
    if TOKEN and not hmac.compare_digest(peticion.headers.get("x-voz-token", ""), TOKEN):
        raise HTTPException(status_code=401, detail="Falta el token del servicio de voz.")


def _modelo_whisper():
    global _whisper
    with _candado_carga:
        if _whisper is None:
            from faster_whisper import WhisperModel

            _whisper = WhisperModel(str(MODELOS / f"whisper-{WHISPER_MODELO}"), device="cpu", compute_type="int8", cpu_threads=HILOS)
        return _whisper


def _voz_piper():
    global _piper
    with _candado_carga:
        if _piper is None:
            from piper import PiperVoice

            _piper = PiperVoice.load(str(MODELOS / "piper" / "voz.onnx"))
        return _piper


def pista_de_vocabulario() -> str:
    """Los términos del Hub como pista inicial para Whisper: ayuda a reconocer «rollback», «SLA» o «Argo CD» en español."""
    if not VOCABULARIO.exists():
        return ""
    terminos = [t.strip() for t in VOCABULARIO.read_text(encoding="utf-8").splitlines() if t.strip()]
    return "Consola del Hub: " + ", ".join(terminos[:40]) + "."


def limpiar_para_voz(texto: str) -> str:
    """Quita lo que se leería mal en voz alta (marcas de formato, enlaces, viñetas) y recorta al máximo."""
    texto = re.sub(r"```[\s\S]*?```", " ", texto)
    texto = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", texto)
    texto = re.sub(r"https?://\S+", " ", texto)
    texto = re.sub(r"[*_`#>|]+", "", texto)
    texto = re.sub(r"^\s*[-•]\s+", "", texto, flags=re.MULTILINE)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto[:MAX_CARACTERES]


@app.get("/health")
def health():
    return {"estado": "ok", "stt": f"faster-whisper-{WHISPER_MODELO}", "tts": "piper-es_MX-claude-high", "stt_cargado": _whisper is not None, "tts_cargado": _piper is not None}


@app.post("/stt")
async def stt(peticion: Request):
    _autorizar(peticion)
    audio = await peticion.body()
    if not audio:
        raise HTTPException(status_code=400, detail="No llegó audio.")
    if len(audio) > MAX_BYTES:
        raise HTTPException(status_code=413, detail=f"El audio pesa más de {MAX_BYTES // 1000} KB.")
    if not _una_transcripcion.acquire(blocking=False):
        raise HTTPException(status_code=429, detail="Ya hay una transcripción en curso; intenta de nuevo en unos segundos.")
    try:
        inicio = time.monotonic()
        try:
            segmentos, info = _modelo_whisper().transcribe(
                io.BytesIO(audio), language="es", beam_size=1, vad_filter=True, initial_prompt=pista_de_vocabulario() or None, condition_on_previous_text=False,
            )
        except Exception:
            raise HTTPException(status_code=422, detail="No se pudo leer el audio (formato no reconocido).") from None
        if info.duration > MAX_SEGUNDOS:
            raise HTTPException(status_code=413, detail=f"El audio dura más de {MAX_SEGUNDOS:g} segundos.")
        texto = " ".join(s.text.strip() for s in segmentos).strip()
        return {"texto": texto, "duracion_s": round(info.duration, 2), "tiempo_ms": int((time.monotonic() - inicio) * 1000), "modelo": f"faster-whisper-{WHISPER_MODELO}"}
    finally:
        _una_transcripcion.release()


@app.post("/tts")
def tts(datos: TtsIn, peticion: Request):
    _autorizar(peticion)
    texto = limpiar_para_voz(datos.texto)
    if not texto:
        raise HTTPException(status_code=422, detail="No hay texto que leer.")
    inicio = time.monotonic()
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as salida:
        _voz_piper().synthesize_wav(texto, salida)
    return Response(content=buffer.getvalue(), media_type="audio/wav", headers={"X-Tiempo-Ms": str(int((time.monotonic() - inicio) * 1000))})

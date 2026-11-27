# La transcripción de voz no congela el bucle de eventos (T09, auditoría BE-01): mientras una transcripción lenta está en curso,
# /health sigue respondiendo. Se prueba sobre un único bucle (sin servidor real), llamando a la aplicación ASGI directamente.
import importlib.util
import time
from pathlib import Path
from types import SimpleNamespace

import anyio
import pytest

from app.config import settings
from app.integrations import voz
from app.main import app

RUTA_VOZ = Path("/repo/voz/app/main.py")
PAUSA = 0.6   # lo que tarda la transcripción simulada
ESPERA = 0.1  # cuándo se pregunta por /health: durante la transcripción


async def _pedir(aplicacion, metodo: str, ruta: str, cabeceras: dict[str, str] | None = None, cuerpo: bytes = b"") -> int:
    """Una petición ASGI mínima; devuelve el código de respuesta."""
    mensajes: list[dict] = []
    entregado = False

    async def receive():
        nonlocal entregado
        if not entregado:
            entregado = True
            return {"type": "http.request", "body": cuerpo, "more_body": False}
        return {"type": "http.disconnect"}

    async def send(mensaje):
        mensajes.append(mensaje)

    scope = {
        "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1", "method": metodo, "path": ruta, "raw_path": ruta.encode(),
        "query_string": b"", "root_path": "", "scheme": "http", "server": ("prueba", 80), "client": ("prueba", 1),
        "headers": [(k.lower().encode(), v.encode()) for k, v in (cabeceras or {}).items()],
    }
    await aplicacion(scope, receive, send)
    return next(m["status"] for m in mensajes if m["type"] == "http.response.start")


def _durante_una_transcripcion(aplicacion, transcribir: tuple, salud: tuple) -> dict[str, float]:
    """Lanza la transcripción lenta y, a los 0,1 s, pregunta por la salud. Devuelve a qué hora terminó cada una."""
    horas: dict[str, float] = {}

    async def lenta():
        horas["codigo_transcribir"] = await _pedir(aplicacion, *transcribir)
        horas["transcribir"] = time.monotonic()

    async def sana():
        await anyio.sleep(ESPERA)
        horas["codigo_salud"] = await _pedir(aplicacion, *salud)
        horas["salud"] = time.monotonic()

    async def escenario():
        async with anyio.create_task_group() as grupo:
            grupo.start_soon(lenta)
            grupo.start_soon(sana)

    anyio.run(escenario)
    return horas


def test_la_api_responde_mientras_el_servicio_de_voz_transcribe(as_agency, monkeypatch):
    monkeypatch.setattr(settings, "voz_url", "http://voz.test:8100")

    def lenta(audio, tipo):
        time.sleep(PAUSA)   # el servicio de voz real tarda segundos; la llamada es síncrona
        return {"texto": "hola", "duracion_s": 1.0, "tiempo_ms": 600, "modelo": "simulado"}

    monkeypatch.setattr(voz, "transcribe", lenta)
    sesion = {"Authorization": as_agency.headers["authorization"], "Content-Type": "audio/webm"}

    horas = _durante_una_transcripcion(app, ("POST", "/api/assistant/voice/transcribe", sesion, b"audio"), ("GET", "/health"))

    assert horas["codigo_transcribir"] == 200 and horas["codigo_salud"] == 200
    assert horas["salud"] < horas["transcribir"], "/health esperó a que terminara la transcripción: el bucle estaba bloqueado"


@pytest.mark.skipif(not RUTA_VOZ.exists(), reason="el repositorio no está montado en /repo")
def test_el_servicio_de_voz_responde_mientras_transcribe(monkeypatch, tmp_path):
    especificacion = importlib.util.spec_from_file_location("voz_main_bloqueo", RUTA_VOZ)
    modulo = importlib.util.module_from_spec(especificacion)
    especificacion.loader.exec_module(modulo)
    monkeypatch.setattr(modulo, "TOKEN", "")
    monkeypatch.setattr(modulo, "VOCABULARY", tmp_path / "no-existe.txt")

    class Lento:
        def transcribe(self, audio, **opciones):
            time.sleep(PAUSA)
            return [SimpleNamespace(text="hola")], SimpleNamespace(duration=1.0)

    monkeypatch.setattr(modulo, "_whisper_model", lambda: Lento())

    horas = _durante_una_transcripcion(modulo.app, ("POST", "/stt", {}, b"audio"), ("GET", "/health"))

    assert horas["codigo_transcribir"] == 200 and horas["codigo_salud"] == 200
    assert horas["salud"] < horas["transcribir"], "/health esperó a que terminara la transcripción: el bucle estaba bloqueado"

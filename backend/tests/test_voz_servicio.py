# Servicio de voz (spec 021, T01) sin modelos: los límites, el token, la limpieza del texto y la forma de las respuestas, con transcriptor y voz simulados.
# Los modelos reales se prueban con el contenedor (voz/ y ai/eval/evaluar_voz.py).
import importlib.util
import wave
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

RUTA = Path("/repo/voz/app/main.py")
pytestmark = pytest.mark.skipif(not RUTA.exists(), reason="el repositorio no está montado en /repo")


@pytest.fixture
def voz(monkeypatch, tmp_path):
    especificacion = importlib.util.spec_from_file_location("voz_main", RUTA)
    modulo = importlib.util.module_from_spec(especificacion)
    especificacion.loader.exec_module(modulo)
    vocabulario = tmp_path / "vocabulario.txt"
    vocabulario.write_text("ticket\nrollback\nSLA\n", encoding="utf-8")
    monkeypatch.setattr(modulo, "VOCABULARIO", vocabulario)
    monkeypatch.setattr(modulo, "TOKEN", "")
    modulo.llamadas = []

    class Transcriptor:
        duracion = 4.0

        def transcribe(self, audio, **opciones):
            modulo.llamadas.append(opciones)
            return [SimpleNamespace(text=" Hola "), SimpleNamespace(text="Hub ")], SimpleNamespace(duration=self.duracion)

    class Voz:
        def synthesize_wav(self, texto, salida):
            modulo.leido = texto
            salida.setnchannels(1)
            salida.setsampwidth(2)
            salida.setframerate(22050)
            salida.writeframes(b"\x00\x00" * 2205)

    modulo.transcriptor, modulo.voz_simulada = Transcriptor(), Voz()
    monkeypatch.setattr(modulo, "_modelo_whisper", lambda: modulo.transcriptor)
    monkeypatch.setattr(modulo, "_voz_piper", lambda: modulo.voz_simulada)
    return modulo, TestClient(modulo.app)


def test_health_dice_los_modelos(voz):
    _, cliente = voz

    cuerpo = cliente.get("/health").json()

    assert cuerpo["estado"] == "ok" and cuerpo["stt"].startswith("faster-whisper") and cuerpo["tts"].startswith("piper")


def test_stt_devuelve_el_texto_y_pasa_el_vocabulario_como_pista(voz):
    modulo, cliente = voz

    respuesta = cliente.post("/stt", content=b"audio-falso", headers={"Content-Type": "audio/webm"})

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["texto"] == "Hola Hub" and cuerpo["duracion_s"] == 4.0 and cuerpo["modelo"].startswith("faster-whisper")
    opciones = modulo.llamadas[0]
    assert opciones["language"] == "es" and "rollback" in opciones["initial_prompt"] and opciones["vad_filter"] is True


def test_stt_rechaza_audio_vacio_demasiado_grande_o_demasiado_largo(voz, monkeypatch):
    modulo, cliente = voz
    monkeypatch.setattr(modulo, "MAX_BYTES", 10)

    assert cliente.post("/stt", content=b"").status_code == 400
    assert cliente.post("/stt", content=b"x" * 11).status_code == 413
    monkeypatch.setattr(modulo, "MAX_BYTES", 1000)
    modulo.transcriptor.duracion = 31.0
    assert cliente.post("/stt", content=b"audio").status_code == 413


def test_un_audio_que_no_se_puede_leer_es_422_sin_filtrar_el_error(voz):
    modulo, cliente = voz

    def roto(audio, **opciones):
        raise RuntimeError("detalle interno con /ruta/secreta")

    modulo.transcriptor.transcribe = roto
    respuesta = cliente.post("/stt", content=b"basura")

    assert respuesta.status_code == 422 and "secreta" not in respuesta.text


def test_una_sola_transcripcion_a_la_vez(voz):
    modulo, cliente = voz
    modulo._una_transcripcion.acquire()
    try:
        assert cliente.post("/stt", content=b"audio").status_code == 429
    finally:
        modulo._una_transcripcion.release()
    assert cliente.post("/stt", content=b"audio").status_code == 200


def test_el_token_se_exige_si_esta_definido(voz, monkeypatch):
    modulo, cliente = voz
    monkeypatch.setattr(modulo, "TOKEN", "secreto-de-prueba")

    assert cliente.post("/stt", content=b"audio").status_code == 401
    assert cliente.post("/tts", json={"texto": "hola"}).status_code == 401
    assert cliente.post("/stt", content=b"audio", headers={"X-Voz-Token": "otro"}).status_code == 401
    assert cliente.post("/stt", content=b"audio", headers={"X-Voz-Token": "secreto-de-prueba"}).status_code == 200


def test_tts_devuelve_un_wav_valido(voz):
    modulo, cliente = voz

    respuesta = cliente.post("/tts", json={"texto": "Se aprueba desde Cambios."})

    assert respuesta.status_code == 200 and respuesta.headers["content-type"] == "audio/wav" and "x-tiempo-ms" in respuesta.headers
    import io

    with wave.open(io.BytesIO(respuesta.content)) as onda:
        assert onda.getframerate() == 22050 and onda.getnframes() == 2205
    assert modulo.leido == "Se aprueba desde Cambios."


def test_tts_limpia_el_formato_antes_de_leer(voz):
    modulo, cliente = voz

    cliente.post("/tts", json={"texto": "**Pasos**:\n- Abre [Cambios](http://hub.local/cambios)\n- Pulsa `Aprobar` https://evil.test/x\n```\ncodigo\n```"})

    assert modulo.leido == "Pasos: Abre Cambios Pulsa Aprobar"


def test_tts_recorta_el_texto_largo_y_rechaza_el_vacio(voz):
    modulo, cliente = voz

    cliente.post("/tts", json={"texto": "a" * 3000})
    assert len(modulo.leido) == modulo.MAX_CARACTERES
    assert cliente.post("/tts", json={"texto": "```solo código```"}).status_code == 422
    assert cliente.post("/tts", json={"texto": ""}).status_code == 422

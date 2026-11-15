# Voz en la API del Hub (spec 021, T02): estado, transcribir y hablar, con el servicio de voz simulado: solo la agencia, redacción de secretos, límites,
# sin servicio la voz se apaga y el asistente sigue por texto.
import json

import pytest

from app.config import settings
from app.integrations import voz


@pytest.fixture
def client(as_agency):
    return as_agency


@pytest.fixture
def servicio(monkeypatch):
    """Servicio de voz simulado: guarda lo que recibe y responde según `estado['texto']`."""
    estado = {"texto": "¿cómo apruebo un cambio?", "recibido": [], "codigo": 200}

    def transporte(request, timeout):
        estado["recibido"].append((request.full_url, request.get_method(), request.data, dict(request.header_items())))
        if estado["codigo"] != 200:
            return estado["codigo"], json.dumps({"detail": "Ya hay una transcripción en curso."}).encode()
        if request.full_url.endswith("/health"):
            return 200, b'{"estado":"ok"}'
        if request.full_url.endswith("/stt"):
            return 200, json.dumps({"texto": estado["texto"], "duracion_s": 2.5, "tiempo_ms": 800, "modelo": "faster-whisper-base"}).encode()
        return 200, b"RIFFwav-falso"

    monkeypatch.setattr(settings, "voz_url", "http://voz.test:8100")
    monkeypatch.setattr(settings, "voz_token", "")
    monkeypatch.setattr(voz, "urllib_transport", transporte)
    return estado


def test_sin_url_la_voz_esta_deshabilitada_y_el_asistente_sigue(client, monkeypatch):
    monkeypatch.setattr(settings, "voz_url", "")
    monkeypatch.setattr(settings, "ollama_url", "")

    assert client.get("/api/assistant/voice/status").json() == {"habilitada": False, "disponible": False}
    assert client.post("/api/assistant/voice/transcribe", content=b"audio").status_code == 503
    assert client.post("/api/assistant/voice/speak", json={"text": "hola"}).status_code == 503
    assert client.post("/api/assistant/ask", json={"question": "¿Cómo abro un incidente manual?"}).status_code == 200


def test_el_estado_dice_si_el_servicio_responde(client, servicio):
    assert client.get("/api/assistant/voice/status").json() == {"habilitada": True, "disponible": True}


def test_el_estado_dice_no_disponible_si_el_servicio_cae(client, servicio):
    servicio["codigo"] = 500

    assert client.get("/api/assistant/voice/status").json() == {"habilitada": True, "disponible": False}


def test_transcribir_devuelve_el_texto_y_reenvia_el_audio_tal_cual(client, servicio):
    respuesta = client.post("/api/assistant/voice/transcribe", content=b"\x1aE\xdf\xa3audio", headers={"Content-Type": "audio/webm"})

    assert respuesta.status_code == 200
    assert respuesta.json() == {"text": "¿cómo apruebo un cambio?", "duration_s": 2.5, "elapsed_ms": 800, "model": "faster-whisper-base", "secrets_redacted": []}
    url, metodo, cuerpo, cabeceras = servicio["recibido"][0]
    assert url == "http://voz.test:8100/stt" and metodo == "POST" and cuerpo == b"\x1aE\xdf\xa3audio" and cabeceras["Content-type"] == "audio/webm"


def test_el_token_del_servicio_viaja_en_la_cabecera(client, servicio, monkeypatch):
    monkeypatch.setattr(settings, "voz_token", "token-de-prueba")

    client.post("/api/assistant/voice/transcribe", content=b"audio")

    assert servicio["recibido"][0][3]["X-voz-token"] == "token-de-prueba"


def test_un_secreto_dictado_se_tapa_en_la_transcripcion(client, servicio):
    servicio["texto"] = "mi password: Sup3rSecreta9 no funciona"

    cuerpo = client.post("/api/assistant/voice/transcribe", content=b"audio").json()

    assert "Sup3rSecreta9" not in cuerpo["text"] and cuerpo["secrets_redacted"]


def test_transcribir_rechaza_vacio_y_demasiado_grande(client, servicio):
    assert client.post("/api/assistant/voice/transcribe", content=b"").status_code == 400
    assert client.post("/api/assistant/voice/transcribe", content=b"x" * 2_000_001).status_code == 413
    assert servicio["recibido"] == []


def test_los_avisos_del_servicio_llegan_a_la_persona(client, servicio):
    servicio["codigo"] = 429

    respuesta = client.post("/api/assistant/voice/transcribe", content=b"audio")

    assert respuesta.status_code == 429 and "en curso" in respuesta.json()["detail"]


def test_un_error_del_servicio_es_503_sin_detalles(client, servicio):
    servicio["codigo"] = 500

    respuesta = client.post("/api/assistant/voice/transcribe", content=b"audio")

    assert respuesta.status_code == 503 and "no está disponible" in respuesta.json()["detail"]


def test_hablar_devuelve_el_audio(client, servicio):
    respuesta = client.post("/api/assistant/voice/speak", json={"text": "Se aprueba desde Cambios."})

    assert respuesta.status_code == 200 and respuesta.headers["content-type"] == "audio/wav" and respuesta.content == b"RIFFwav-falso"
    assert json.loads(servicio["recibido"][0][2]) == {"texto": "Se aprueba desde Cambios."}


def test_hablar_tapa_los_secretos_antes_de_enviarlos_al_servicio(client, servicio):
    client.post("/api/assistant/voice/speak", json={"text": "La clave AKIAZ3MQ7XK2VWR9TDLP no va aquí."})

    assert b"AKIAZ3MQ7XK2VWR9TDLP" not in servicio["recibido"][0][2]


def test_el_cliente_no_puede_usar_la_voz(as_client, servicio):
    assert as_client.get("/api/assistant/voice/status").status_code == 403
    assert as_client.post("/api/assistant/voice/transcribe", content=b"audio").status_code == 403
    assert as_client.post("/api/assistant/voice/speak", json={"text": "hola"}).status_code == 403

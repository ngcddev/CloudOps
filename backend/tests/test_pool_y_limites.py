# Pool de conexiones y topes de tamaño (spec 022, T07; auditoría BE-02 y BE-05): el motor de PostgreSQL lleva su pool y sus tiempos límite, esperar a
# Ollama no sostiene una conexión, y un cuerpo o un texto demasiado grande se rechaza en vez de agotar la memoria del Pod.
import json

import pytest
from pydantic import ValidationError
from sqlalchemy import select

from app.config import settings
from app.db import opciones_del_motor, soltar_conexion
from app.models import Incident, User
from app.schemas.change_request import ChangeRequestReject
from app.schemas.client import ProjectCreate
from app.schemas.ticket import TicketClassify, TicketCreate, WorkLogCreate
from app.services import ai_drafts, assistant
from tests.test_ai_drafts import mitigado, sazon  # noqa: F401  (fixtures)

# ---------- BE-02: el motor y la conexión ----------


def test_postgresql_recibe_el_pool_y_los_tiempos_limite(monkeypatch):
    monkeypatch.setattr(settings, "db_pool_size", 7)
    monkeypatch.setattr(settings, "db_max_overflow", 3)
    monkeypatch.setattr(settings, "db_pool_timeout", 4)
    monkeypatch.setattr(settings, "db_statement_timeout_ms", 1500)
    monkeypatch.setattr(settings, "db_idle_in_transaction_timeout_ms", 99000)

    opciones = opciones_del_motor("postgresql+psycopg://hub:x@db:5432/hub")

    assert (opciones["pool_size"], opciones["max_overflow"], opciones["pool_timeout"]) == (7, 3, 4)
    assert opciones["pool_pre_ping"] is True
    assert opciones["connect_args"]["options"] == "-c statement_timeout=1500 -c idle_in_transaction_session_timeout=99000"


def test_sqlite_no_recibe_argumentos_de_pool():
    # El pool de SQLite no admite max_overflow ni pool_timeout: pasarlos rompe las pruebas y los scripts de ai/
    assert opciones_del_motor("sqlite://") == {"pool_pre_ping": True}


def test_los_valores_por_defecto_son_los_documentados():
    assert (settings.db_pool_size, settings.db_max_overflow, settings.db_pool_timeout) == (10, 5, 10)
    assert settings.db_statement_timeout_ms == 15000
    # La red de seguridad debe superar con holgura lo que tarda una llamada lenta que sí sostiene la transacción (diagnóstico: ~75 s)
    assert settings.db_idle_in_transaction_timeout_ms >= 180000


def test_soltar_la_conexion_termina_la_transaccion(db):
    db.scalars(select(User)).all()
    assert db.in_transaction()

    soltar_conexion(db)

    assert not db.in_transaction()


def test_soltar_la_conexion_no_tira_cambios_sin_guardar(seeded):
    usuario = seeded.scalar(select(User))
    usuario.name = "Cambio sin guardar"

    with pytest.raises(RuntimeError, match="cambios sin guardar"):
        soltar_conexion(seeded)

    assert usuario.name == "Cambio sin guardar"   # sigue ahí: no se hizo rollback


def test_preguntar_al_asistente_no_sostiene_una_conexion_mientras_espera_a_ollama(seeded, monkeypatch):
    tecnico = seeded.scalar(select(User).where(User.role == "agencia"))
    durante = []

    def transporte(url, body, timeout):
        durante.append(seeded.in_transaction())
        return 200, json.dumps({"message": {"content": "Se abre desde Incidentes → Nuevo."}}).encode()

    monkeypatch.setattr(settings, "ollama_url", "http://ollama.test:11434")
    monkeypatch.setattr("app.integrations.ollama.urllib_transport", transporte)
    seeded.scalars(select(User)).all()   # la sesión ya tiene una transacción abierta, como en una petición real

    registro = assistant.ask(seeded, tecnico, "¿Cómo abro un incidente manual?")

    assert durante == [False]                      # mientras esperaba a Ollama no había transacción (ni conexión) tomada
    assert registro.user_id == tecnico.id and registro.answer.startswith("Se abre")   # y la respuesta quedó registrada igual


def test_generar_borradores_no_sostiene_una_conexion_mientras_espera_a_ollama(seeded, mitigado, monkeypatch):  # noqa: F811
    durante = []
    textos = {
        "mensaje": "Detectamos una falla temporal en su sitio a las 14:00 y el servicio volvió a funcionar a las 14:07. Tiempo total: 7 minutos.",
        "resumen": "El sitio del restaurante falló de 14:00 a 14:07 por una versión con error de configuración; se hizo rollback de v2 a v1.",
    }

    def transporte(url, body, timeout):
        durante.append(seeded.in_transaction())
        sistema = json.loads(body)["messages"][0]["content"]
        clave = "mensaje" if "mensajes de una agencia web" in sistema else "resumen"
        return 200, json.dumps({"message": {"content": textos[clave]}}).encode()

    monkeypatch.setattr(settings, "ollama_url", "http://ollama.test:11434")
    seeded.get(Incident, mitigado.id)   # transacción abierta

    borradores = ai_drafts.generar(seeded, mitigado, transport=transporte)

    assert durante and not any(durante)
    assert {b.kind for b in borradores} == set(ai_drafts.KINDS) and all(b.status == "borrador_ia" for b in borradores)


# ---------- BE-05: topes de texto ----------


@pytest.mark.parametrize(
    ("modelo", "campos", "tope"),
    [
        (TicketCreate, {"service_id": 1, "title": "t", "description": "x"}, ("description", 5000)),
        (TicketClassify, {"impact": "alto", "urgency": "alta", "correction_reason": "x"}, ("correction_reason", 1000)),
        (WorkLogCreate, {"hours": "1.5", "note": "x"}, ("note", 2000)),
        (ChangeRequestReject, {"reason": "x"}, ("reason", 1000)),
        (ProjectCreate, {"name": "p", "description": "x"}, ("description", 2000)),
    ],
)
def test_los_textos_libres_tienen_tope(modelo, campos, tope):
    campo, maximo = tope
    modelo(**{**campos, campo: "x" * maximo})   # justo en el tope, pasa
    with pytest.raises(ValidationError, match=campo):
        modelo(**{**campos, campo: "x" * (maximo + 1)})


# ---------- BE-05: tope del cuerpo ----------


@pytest.fixture
def anonimo(anonymous):
    return anonymous


def _trozos(total: int, trozo: int = 200_000):
    """Un cuerpo que llega por trozos y sin Content-Length."""
    restante = total
    while restante > 0:
        n = min(trozo, restante)
        restante -= n
        yield b"x" * n


def test_un_cuerpo_mayor_que_el_tope_responde_413_sin_leerlo(anonimo):
    respuesta = anonimo.post("/api/tickets", content=b"x" * (settings.body_limit_bytes + 1), headers={"Content-Type": "application/json"})

    assert respuesta.status_code == 413
    assert "demasiado grande" in respuesta.json()["detail"] and "1024 KB" in respuesta.json()["detail"]


def test_un_cuerpo_por_trozos_sin_content_length_tambien_se_corta(anonimo):
    respuesta = anonimo.post("/api/tickets", content=_trozos(settings.body_limit_bytes + 100_000), headers={"Content-Type": "application/json"})

    assert respuesta.status_code == 413
    assert "demasiado grande" in respuesta.json()["detail"]


def test_un_cuerpo_normal_pasa_el_tope_y_llega_a_la_autenticacion(anonimo):
    # Sin sesión responde 401: el tope no lo tocó
    assert anonimo.post("/api/tickets", json={"service_id": 1, "title": "t", "description": "x"}).status_code == 401
    assert anonimo.post("/api/tickets", content=b"x" * (settings.body_limit_bytes - 10), headers={"Content-Type": "application/json"}).status_code in (401, 422)


def test_el_informe_del_pipeline_admite_un_cuerpo_grande_pero_con_su_propio_tope(anonimo):
    grande = b'{"x": "' + b"a" * 3_000_000 + b'"}'     # 3 MB: mucho más que los ~600 KB de un informe real, y por encima del tope general
    assert anonimo.post("/api/pipeline-events", content=grande, headers={"Content-Type": "application/json"}).status_code == 401   # pasó el tope
    demasiado = b"x" * (settings.pipeline_body_limit_bytes + 1)
    assert anonimo.post("/api/pipeline-events", content=demasiado, headers={"Content-Type": "application/json"}).status_code == 413


def test_el_audio_de_voz_tiene_su_propio_tope(anonimo):
    assert anonimo.post("/api/assistant/voice/transcribe", content=b"x" * 1_900_000).status_code == 401   # 1,9 MB cabe: lo rechaza la sesión
    assert anonimo.post("/api/assistant/voice/transcribe", content=b"x" * (settings.voice_body_limit_bytes + 1)).status_code == 413


def test_las_lecturas_no_tienen_tope_de_cuerpo(anonimo):
    assert anonimo.get("/health").status_code in (200, 503)

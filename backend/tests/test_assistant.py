# Pruebas del asistente local (spec 012): la compuerta, el registro en ai_queries, el modo sin IA y los permisos.
import json

import pytest

from app.config import settings
from app.models.ai_query import AiQuery
from app.services.assistant_gate import load_model


@pytest.fixture
def client(as_agency):
    return as_agency


@pytest.fixture
def ollama_responde(monkeypatch):
    """Simula a Ollama: cuenta las llamadas y responde un texto fijo."""
    llamadas = []

    def transport(url, body, timeout):
        llamadas.append(json.loads(body))
        return 200, json.dumps({"message": {"content": "Se abre desde Incidentes → Nuevo."}}).encode()

    monkeypatch.setattr(settings, "ollama_url", "http://ollama.test:11434")
    monkeypatch.setattr("app.integrations.ollama.urllib_transport", transport)
    return llamadas


def test_pregunta_del_tema_despierta_al_llm(client, ollama_responde, db):
    response = client.post("/api/assistant/ask", json={"question": "¿Cómo abro un incidente manual?"})

    assert response.status_code == 200
    body = response.json()
    assert body["answered_by"] == "llm" and body["gate_label"] == "en_tema"
    assert body["answer"].startswith("Se abre")
    assert len(ollama_responde) == 1
    assert db.get(AiQuery, body["id"]).llm_woken is True


def test_pregunta_ajena_no_despierta_al_llm(client, ollama_responde, db):
    response = client.post("/api/assistant/ask", json={"question": "¿Cómo preparo una receta de arepas?"})

    body = response.json()
    assert body["answered_by"] == "compuerta" and body["gate_label"] == "fuera_de_tema"
    assert body["llm_woken"] is False and body["model"] is None
    assert ollama_responde == []  # el LLM nunca se llamó
    assert "Hub" in body["answer"]


def test_sin_ollama_el_asistente_avisa_y_no_falla(client, monkeypatch):
    monkeypatch.setattr(settings, "ollama_url", "")

    response = client.post("/api/assistant/ask", json={"question": "¿Qué es un rollback?"})

    assert response.status_code == 200
    body = response.json()
    assert body["llm_woken"] is True and body["llm_ok"] is False
    assert "no respondió" in body["answer"]


def test_ollama_con_error_http_tambien_se_trata_como_no_disponible(client, monkeypatch):
    monkeypatch.setattr(settings, "ollama_url", "http://ollama.test:11434")
    monkeypatch.setattr("app.integrations.ollama.urllib_transport", lambda url, body, timeout: (500, b"error"))

    body = client.post("/api/assistant/ask", json={"question": "¿Qué es el SLA?"}).json()

    assert body["llm_ok"] is False


def test_la_guarda_de_vocabulario_nunca_salta_al_llm():
    modelo = load_model()
    for pregunta in ("ticket", "Quiero ver mis incidentes", "¿cómo hago un rollback?"):
        assert modelo.decide(pregunta).despertar_llm, pregunta


def test_el_modelo_exportado_sabe_su_version_y_umbral():
    modelo = load_model()
    assert modelo.version and 0.5 <= modelo.threshold < 1


def test_las_estadisticas_cuentan_el_ahorro(client, ollama_responde):
    client.post("/api/assistant/ask", json={"question": "¿Cómo apruebo una solicitud de cambio?"})
    client.post("/api/assistant/ask", json={"question": "¿Cuál es la capital de Francia?"})
    client.post("/api/assistant/ask", json={"question": "Cuéntame un chiste"})

    stats = client.get("/api/assistant/stats").json()

    assert stats["total"] == 3 and stats["llm_despertado"] == 1 and stats["llm_evitado"] == 2
    assert stats["llm_evitado_pct"] == pytest.approx(66.7)
    assert stats["latencia_llm_ms"] is not None


def test_la_opinion_corrige_la_decision_y_cuenta_como_deriva(client, ollama_responde):
    consulta = client.post("/api/assistant/ask", json={"question": "Cuéntame un chiste"}).json()

    r = client.post(f"/api/assistant/{consulta['id']}/feedback", json={"label": "en_tema"})

    assert r.status_code == 204
    stats = client.get("/api/assistant/stats").json()
    assert stats["con_opinion"] == 1 and stats["decisiones_corregidas"] == 1
    assert stats["decisiones_corregidas_pct"] == 100.0


def test_no_se_opina_sobre_la_consulta_de_otra_persona(client, as_user, seeded, ollama_responde):
    consulta = client.post("/api/assistant/ask", json={"question": "Cuéntame un chiste"}).json()
    otra = as_user("sofia@forjadigital.test")

    assert otra.post(f"/api/assistant/{consulta['id']}/feedback", json={"label": "en_tema"}).status_code == 404


def test_el_cliente_no_usa_el_asistente(as_client):
    assert as_client.post("/api/assistant/ask", json={"question": "¿Qué es un rollback?"}).status_code == 403
    assert as_client.get("/api/assistant/stats").status_code == 403


def test_pregunta_vacia_o_muy_larga_se_rechaza(client):
    assert client.post("/api/assistant/ask", json={"question": "a"}).status_code == 422
    assert client.post("/api/assistant/ask", json={"question": "x" * 501}).status_code == 422


# ---------- Contexto fundamentado en la ayuda del Hub ----------


def test_en_modo_completo_el_llm_recibe_toda_la_ayuda_y_la_consulta_la_registra(client, ollama_responde, db):
    body = client.post("/api/assistant/ask", json={"question": "¿Cómo cierro un incidente?"}).json()

    sistema = ollama_responde[0]["messages"][0]["content"]
    assert "CONTEXTO:" in sistema and "Mitigar y cerrar un incidente" in sistema and "Rollback" in sistema
    assert "Mitigar y cerrar un incidente" in body["context_sections"]


def test_el_llm_responde_de_forma_determinista_y_corta(client, ollama_responde):
    client.post("/api/assistant/ask", json={"question": "¿Qué es un rollback?"})

    opciones = ollama_responde[0]["options"]
    assert opciones["temperature"] == 0 and opciones["num_predict"] <= 400


def test_en_modo_recuperacion_una_pregunta_sin_relacion_en_la_ayuda_no_llama_al_llm(client, ollama_responde, monkeypatch):
    monkeypatch.setattr(settings, "assistant_context_mode", "recuperacion")

    body = client.post("/api/assistant/ask", json={"question": "¿Cómo cambio mi contraseña?"}).json()

    assert body["answered_by"] == "ayuda" and body["llm_woken"] is False
    assert "No tengo esa información" in body["answer"]
    assert ollama_responde == []


def test_en_modo_recuperacion_solo_se_pasan_las_secciones_parecidas(client, ollama_responde, monkeypatch):
    monkeypatch.setattr(settings, "assistant_context_mode", "recuperacion")

    client.post("/api/assistant/ask", json={"question": "¿Cómo cierro un incidente?"})

    sistema = ollama_responde[0]["messages"][0]["content"]
    assert "Mitigar y cerrar un incidente" in sistema and "### Planes" not in sistema


def test_la_busqueda_encuentra_la_seccion_correcta():
    from app.services import assistant_context as ctx

    assert ctx.context_for("¿Cuánto cuesta el plan Premium?")[0].titulo == "Planes"
    assert ctx.context_for("¿Cómo hago un rollback?")[0].titulo == "Rollback"
    assert ctx.context_for("¿Cómo elimino un cliente?") == []  # la ayuda no lo dice


def test_la_ayuda_cabe_en_el_contexto_del_modelo():
    from app.services import assistant_context as ctx

    assert ctx.full_context_fits()
    assert len(ctx.all_sections()) >= 25


def test_cada_dato_de_la_ayuda_sobre_los_planes_coincide_con_la_semilla():
    """La ayuda repite precios, horas y SLO: si la semilla cambia y la ayuda no, esta prueba falla."""
    import json
    from pathlib import Path

    from app.services import assistant_context as ctx

    planes = json.loads((Path(__file__).resolve().parents[2] / "seed" / "plans.json").read_text(encoding="utf-8"))
    texto = next(s.texto for s in ctx.all_sections() if s.titulo == "Planes")
    for plan in planes:
        assert f"{plan['monthly_price']:,}".replace(",", ".") in texto, plan["name"]
        assert f"{plan['included_hours']} horas" in texto, plan["name"]
        assert plan["cpu_quota"] in texto and plan["memory_quota"] in texto, plan["name"]

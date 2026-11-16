# Pruebas del RAG del asistente (spec 012): división de la ayuda en trozos, embeddings con Ollama, índice en la base,
# búsqueda por similitud, respaldo léxico y reindexado. Ollama se simula con un transporte que dispara /api/embed y
# /api/chat; los embeddings de prueba son una bolsa de palabras con hash (misma idea que el modelo real, sin red).
import hashlib
import json
import re

import pytest
from sqlalchemy import select

from app.config import settings
from app.integrations import ollama
from app.models.ai_query import AiQuery
from app.models.knowledge import KbChunk, KbDocument
from app.services import assistant_context, knowledge
from app.services.assistant_gate import normalize

DIMENSIONES = 64


def vector_de_prueba(texto: str) -> list[float]:
    """Embedding falso pero determinista: cuenta las raíces de las palabras en 64 casillas."""
    texto = re.sub(r"^(search_document|search_query): ", "", texto)
    vector = [0.0] * DIMENSIONES
    for palabra in normalize(texto).split():
        if len(palabra) > 3:
            casilla = int(hashlib.md5(palabra[:6].encode()).hexdigest(), 16) % DIMENSIONES
            vector[casilla] += 1.0
    return vector


class OllamaFalso:
    """Transporte que simula a Ollama: embeddings de prueba y un texto fijo para el chat; cuenta las llamadas."""

    def __init__(self, embed_status: int = 200):
        self.embed_status = embed_status
        self.embeds: list[list[str]] = []
        self.chats: list[dict] = []

    def __call__(self, url: str, body: bytes, timeout: float):
        cuerpo = json.loads(body)
        if url.endswith("/api/embed"):
            self.embeds.append(cuerpo["input"])
            if self.embed_status != 200:
                return self.embed_status, b"error"
            return 200, json.dumps({"embeddings": [vector_de_prueba(t) for t in cuerpo["input"]]}).encode()
        self.chats.append(cuerpo)
        return 200, json.dumps({"message": {"content": "Respuesta de prueba."}}).encode()


@pytest.fixture
def falso(monkeypatch):
    transporte = OllamaFalso()
    monkeypatch.setattr(settings, "ollama_url", "http://ollama.test:11434")
    monkeypatch.setattr("app.integrations.ollama.urllib_transport", transporte)
    return transporte


@pytest.fixture
def agency(as_agency):
    return as_agency


# ---------- Funciones puras ----------


def test_dividir_da_un_trozo_por_seccion_de_la_ayuda():
    trozos = knowledge.dividir(assistant_context.HELP_PATH.read_text(encoding="utf-8"))
    titulos = [s.titulo for s in assistant_context.todas()]

    assert [t.seccion for t in trozos] == titulos
    assert all(t.texto for t in trozos)
    assert "Rollback" in titulos and len(trozos) >= 25


def test_dividir_parte_las_secciones_largas_por_parrafos():
    parrafos = "\n\n".join(f"Párrafo {i} " + "palabra " * 30 for i in range(6))
    trozos = knowledge.dividir(f"## Sección larga\n{parrafos}\n\n## Corta\nHola", max_chars=500)

    larga = [t for t in trozos if t.seccion == "Sección larga"]
    assert len(larga) > 1 and all(len(t.texto) <= 500 for t in larga)
    assert [t.posicion for t in trozos] == list(range(len(trozos)))  # el orden es del documento entero (clave única)
    assert trozos[-1].seccion == "Corta"


def test_coseno_y_orden():
    assert knowledge.coseno([1, 0], [1, 0]) == pytest.approx(1)
    assert knowledge.coseno([1, 0], [0, 1]) == pytest.approx(0)
    assert knowledge.coseno([0, 0], [1, 1]) == 0

    a, b, c = knowledge.Trozo("A", 0, "a"), knowledge.Trozo("B", 0, "b"), knowledge.Trozo("C", 0, "c")
    orden = knowledge.ordenar([1, 0], [(a, [0, 1]), (b, [1, 0.1]), (c, [1, 1])], k=2)
    assert [t.seccion for _, t in orden] == ["B", "C"]


def test_agrupar_une_los_trozos_de_la_misma_seccion_en_orden_de_relevancia():
    t = [(0.9, knowledge.Trozo("X", 0, "uno")), (0.8, knowledge.Trozo("Y", 0, "dos")), (0.7, knowledge.Trozo("X", 1, "tres"))]

    secciones = knowledge.agrupar(t)

    assert [s.titulo for s in secciones] == ["X", "Y"]
    assert secciones[0].texto == "uno\n\ntres"


# ---------- Embeddings con Ollama ----------


def test_embed_sin_ollama_configurado_devuelve_none(monkeypatch):
    monkeypatch.setattr(settings, "ollama_url", "")
    assert ollama.embed(["hola"]) is None


def test_embed_devuelve_un_vector_por_texto_y_usa_el_modelo_configurado(falso):
    vectores = ollama.embed(["uno", "dos"], transport=falso)

    assert len(vectores) == 2 and len(vectores[0]) == DIMENSIONES
    assert falso.embeds == [["uno", "dos"]]


@pytest.mark.parametrize(
    "respuesta",
    [(500, b"error"), (200, b"no es json"), (200, b'{"embeddings": [[1.0]]}'), (200, b'{"embeddings": [["a"], ["b"]]}')],
)
def test_embed_nunca_lanza_ante_respuestas_malas(monkeypatch, respuesta):
    monkeypatch.setattr(settings, "ollama_url", "http://ollama.test:11434")
    assert ollama.embed(["uno", "dos"], transport=lambda url, body, timeout: respuesta) is None


def test_embed_nunca_lanza_si_el_transporte_falla(monkeypatch):
    monkeypatch.setattr(settings, "ollama_url", "http://ollama.test:11434")

    def roto(url, body, timeout):
        raise TimeoutError("sin red")

    assert ollama.embed(["uno"], transport=roto) is None


# ---------- Índice en la base ----------


def test_indexar_guarda_documento_y_trozos_con_su_embedding(db, falso):
    resultado = knowledge.indexar(db, transport=falso)

    doc = db.scalar(select(KbDocument))
    trozos = db.scalars(select(KbChunk)).all()
    assert resultado["trozos"] == len(trozos) == doc.chunk_count and resultado["modelo"] == settings.ollama_embed_model
    assert doc.source == "ayuda_hub.md" and len(doc.content_hash) == 64
    assert all(len(t.embedding) == DIMENSIONES and t.content_hash for t in trozos)
    assert knowledge.indice_vigente(db) is True


def test_reindexar_reemplaza_el_indice_sin_duplicar(db, falso):
    knowledge.indexar(db, transport=falso)
    primeros = len(db.scalars(select(KbChunk)).all())

    knowledge.indexar(db, transport=falso)

    assert len(db.scalars(select(KbChunk)).all()) == primeros
    assert len(db.scalars(select(KbDocument)).all()) == 1


def test_el_indice_se_vence_si_cambia_la_ayuda_o_el_modelo(db, falso, monkeypatch):
    knowledge.indexar(db, transport=falso)
    assert knowledge.indice_vigente(db) is True

    monkeypatch.setattr(settings, "ollama_embed_model", "otro-modelo")
    assert knowledge.indice_vigente(db) is False

    monkeypatch.setattr(settings, "ollama_embed_model", "nomic-embed-text")
    db.scalar(select(KbDocument)).content_hash = "viejo"
    assert knowledge.indice_vigente(db) is False


def test_si_ollama_falla_al_indexar_el_indice_anterior_queda_intacto(db, falso):
    knowledge.indexar(db, transport=falso)
    antes = [(c.id, c.text) for c in db.scalars(select(KbChunk))]

    assert knowledge.indexar(db, transport=OllamaFalso(embed_status=500)) is None

    assert [(c.id, c.text) for c in db.scalars(select(KbChunk))] == antes


# ---------- Búsqueda ----------


def test_recuperar_encuentra_la_seccion_correcta_y_la_cita(db, falso, monkeypatch):
    monkeypatch.setattr(settings, "rag_min_score", 0.2)  # los embeddings de prueba puntúan más bajo que los reales

    encontrado = knowledge.recuperar(db, "¿cómo hago un rollback de un incidente?", transport=falso)

    assert encontrado is not None and encontrado.secciones
    assert "Rollback" in [s.titulo for s in encontrado.secciones]
    assert encontrado.trozos[0][0] == pytest.approx(encontrado.mejor, abs=1e-4) and encontrado.mejor <= 1.0
    assert len(encontrado.trozos) == settings.rag_top_k


def test_recuperar_deja_vacio_si_nada_se_parece_lo_bastante(db, falso, monkeypatch):
    monkeypatch.setattr(settings, "rag_min_score", 0.9)

    encontrado = knowledge.recuperar(db, "receta de arepas con queso", transport=falso)

    assert encontrado is not None and encontrado.secciones == []  # el LLM no se llama: sin información


def test_recuperar_indexa_solo_si_el_indice_esta_vencido(db, falso):
    knowledge.recuperar(db, "¿qué es el SLA?", transport=falso)
    primera = len(falso.embeds)  # una llamada para indexar y otra para la pregunta
    knowledge.recuperar(db, "¿qué es el SLA?", transport=falso)

    assert primera == 2 and len(falso.embeds) == 3


def test_recuperar_devuelve_none_si_ollama_no_da_embeddings(db, monkeypatch):
    monkeypatch.setattr(settings, "ollama_url", "http://ollama.test:11434")

    assert knowledge.recuperar(db, "¿qué es el SLA?", transport=OllamaFalso(embed_status=500)) is None


# ---------- El asistente en modo RAG ----------


@pytest.fixture
def modo_rag(monkeypatch):
    monkeypatch.setattr(settings, "assistant_context_mode", "rag")
    monkeypatch.setattr(settings, "rag_min_score", 0.3)


def test_en_modo_rag_el_llm_solo_recibe_los_trozos_recuperados(agency, falso, modo_rag, db):
    body = agency.post("/api/assistant/ask", json={"question": "¿Cómo hago un rollback de un incidente?"}).json()

    assert body["answered_by"] == "llm" and body["context_mode"] == "rag"
    assert body["retrieval_score"] is not None and 0 < body["retrieval_score"] <= 1
    assert "Rollback" in body["context_sections"] and len(body["context_sections"]) <= settings.rag_top_k
    sistema = falso.chats[0]["messages"][0]["content"]
    assert "### Rollback" in sistema and "### Portal del cliente" not in sistema  # no se manda toda la ayuda
    fila = db.get(AiQuery, body["id"])
    assert fila.context_mode == "rag" and fila.retrieval_score == body["retrieval_score"]


def test_en_modo_rag_lo_que_la_ayuda_no_trata_no_llama_al_llm(agency, falso, modo_rag, monkeypatch):
    monkeypatch.setattr(settings, "rag_min_score", 0.95)

    body = agency.post("/api/assistant/ask", json={"question": "¿Cómo cambio mi contraseña del Hub?"}).json()

    assert body["answered_by"] == "ayuda" and body["llm_woken"] is False
    assert body["answer"] == assistant_context.SIN_INFORMACION and falso.chats == []
    assert body["context_mode"] == "rag" and body["context_sections"] == []


def test_en_modo_rag_si_los_embeddings_fallan_cae_a_la_recuperacion_lexica(agency, monkeypatch, modo_rag):
    falla = OllamaFalso(embed_status=500)
    monkeypatch.setattr(settings, "ollama_url", "http://ollama.test:11434")
    monkeypatch.setattr("app.integrations.ollama.urllib_transport", falla)

    body = agency.post("/api/assistant/ask", json={"question": "¿Cómo cierro un incidente?"}).json()

    assert body["answered_by"] == "llm" and body["llm_ok"] is True  # el asistente sigue funcionando
    assert body["context_mode"] == "recuperacion" and body["retrieval_score"] is None
    assert "Mitigar y cerrar un incidente" in body["context_sections"]


def test_en_modo_completo_se_registra_el_modo(agency, falso):
    body = agency.post("/api/assistant/ask", json={"question": "¿Cómo cierro un incidente?"}).json()

    assert body["context_mode"] == "completo" and body["retrieval_score"] is None


# ---------- Reindexado ----------


def test_reindexar_requiere_agencia(as_client):
    assert as_client.post("/api/assistant/reindex").status_code == 403


def test_reindexar_genera_el_indice(agency, falso, db):
    r = agency.post("/api/assistant/reindex")

    assert r.status_code == 200
    assert r.json()["trozos"] == len(db.scalars(select(KbChunk)).all()) > 0
    assert r.json()["modelo"] == settings.ollama_embed_model


def test_reindexar_sin_ollama_responde_503(agency, monkeypatch):
    monkeypatch.setattr(settings, "ollama_url", "")

    r = agency.post("/api/assistant/reindex")

    assert r.status_code == 503 and "Ollama" in r.json()["detail"]


# ---------- Carreras al reindexar (auditoría BE-07, spec 022 T19) ----------


def test_si_el_indice_ya_esta_vigente_recuperar_no_lo_reescribe(db, falso):
    knowledge.indexar(db, transport=falso)
    ids = sorted(c.id for c in db.scalars(select(KbChunk)))

    # Con `solo_si_vencido` (lo que usa `recuperar` en medio de una pregunta) un índice vigente no se vuelve a escribir: quien esperaba el candado de otro no lo repite
    knowledge.indexar(db, transport=falso, solo_si_vencido=True)

    assert sorted(c.id for c in db.scalars(select(KbChunk))) == ids


def test_una_carrera_de_unicos_deja_el_indice_intacto_y_cae_a_la_lexica(db, falso, monkeypatch):
    from sqlalchemy.exc import IntegrityError

    knowledge.indexar(db, transport=falso)
    antes = [(c.id, c.text) for c in db.scalars(select(KbChunk))]
    db.scalar(select(KbDocument)).content_hash = "viejo"   # índice vencido
    db.commit()

    def choque(*args, **kwargs):
        raise IntegrityError("INSERT", {}, Exception("uq_kb_chunks_document_position"))

    monkeypatch.setattr(knowledge, "_reemplazar_indice", choque)

    assert knowledge.indexar(db, transport=falso, solo_si_vencido=True) is None
    assert knowledge.recuperar(db, "¿cómo apruebo un cambio?", transport=falso) is None   # el asistente responde con la recuperación léxica, no con un 500
    assert [(c.id, c.text) for c in db.scalars(select(KbChunk))] == antes

# Reindexado del RAG con dos preguntas a la vez, contra un PostgreSQL de verdad (auditoría BE-07, spec 022 T19). SQLite no tiene candados de transacción ni
# escrituras concurrentes, así que esta prueba solo corre si TEST_POSTGRES_URL apunta a una base vacía y desechable; en CI se omite.
import os
import threading

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.db import Base
from app.models.knowledge import KbChunk, KbDocument
from app.services import knowledge
from tests.test_knowledge import OllamaFalso

URL = os.environ.get("TEST_POSTGRES_URL")
pytestmark = pytest.mark.skipif(not URL, reason="TEST_POSTGRES_URL no está definida (hace falta un PostgreSQL desechable)")


def test_dos_preguntas_con_el_indice_vencido_no_chocan(monkeypatch):
    motor = create_engine(URL)
    Base.metadata.drop_all(motor)
    Base.metadata.create_all(motor)
    sesion = sessionmaker(bind=motor)
    transporte = OllamaFalso()
    monkeypatch.setattr(settings, "ollama_url", "http://ollama.test:11434")
    monkeypatch.setattr("app.integrations.ollama.urllib_transport", transporte)
    resultados, errores = [], []
    barrera = threading.Barrier(6)

    def pregunta():
        with sesion() as db:
            try:
                barrera.wait()
                resultados.append(knowledge.retrieve(db, "¿cómo apruebo un cambio?", transport=transporte))
            except Exception as e:  # noqa: BLE001 - lo que se mide es que ninguna pregunta lance
                errores.append(repr(e))

    hilos = [threading.Thread(target=pregunta) for _ in range(6)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()

    with sesion() as db:
        documentos = db.scalars(select(KbDocument)).all()
        trozos = db.scalars(select(KbChunk)).all()
    assert errores == []
    assert all(r is not None for r in resultados), "alguna pregunta cayó a la recuperación léxica por una carrera"
    assert len(documentos) == 1 and len(trozos) == documentos[0].chunk_count
    Base.metadata.drop_all(motor)

# Deriva del asistente (spec 020, T03): ventanas de tiempo, umbrales y el endpoint, con consultas sintéticas.
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.models import User
from app.models.ai_query import AiQuery
from app.services import ai_drift

AHORA = datetime(2026, 11, 15, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def client(as_agency):
    return as_agency


@pytest.fixture
def usuario(seeded) -> User:
    return seeded.scalars(select(User).where(User.role == "agencia")).first()


def consulta(db, usuario, hace_dias: float, label="en_tema", feedback=None, llm=False, llm_ok=True, latencia=None):
    db.add(AiQuery(
        user_id=usuario.id, question="¿Cómo apruebo un cambio?", gate_label=label, p_fuera_de_tema=0.1, gate_version="v1", llm_woken=llm,
        model="qwen2.5:7b-instruct" if llm else None, prompt_version="v3" if llm else None, llm_ok=llm_ok if llm else None,
        latency_ms=latencia, answer="respuesta", context_sections=[], context_mode="completo", feedback_label=feedback,
        created_at=AHORA - timedelta(days=hace_dias),
    ))


def llenar(db, usuario, hace_dias, n, **kw):
    for _ in range(n):
        consulta(db, usuario, hace_dias, **kw)
    db.commit()


def test_sin_consultas_el_estado_es_sin_datos(db):
    r = ai_drift.compute(db, ahora=AHORA)

    assert r["estado"] == "sin_datos" and r["avisos"] == [] and r["actual"]["consultas"] == 0


def test_con_datos_estables_no_hay_avisos(db, usuario):
    llenar(db, usuario, 1, 25)
    llenar(db, usuario, 9, 25)

    r = ai_drift.compute(db, ahora=AHORA)

    assert r["estado"] == "ok" and r["avisos"] == [] and r["actual"]["consultas"] == 25 and r["anterior"]["consultas"] == 25


def test_las_ventanas_no_se_mezclan(db, usuario):
    llenar(db, usuario, 1, 3)  # actual
    llenar(db, usuario, 9, 4)  # anterior
    llenar(db, usuario, 20, 5)  # fuera de las dos

    r = ai_drift.compute(db, ahora=AHORA)

    assert (r["actual"]["consultas"], r["anterior"]["consultas"]) == (3, 4)


def test_muchas_decisiones_corregidas_avisan_que_hay_que_reentrenar(db, usuario):
    llenar(db, usuario, 1, 7, label="en_tema", feedback="en_tema")
    llenar(db, usuario, 1, 3, label="fuera_de_tema", feedback="en_tema")  # 3 de 10 corregidas = 30 %

    r = ai_drift.compute(db, ahora=AHORA)

    assert r["estado"] == "atencion"
    assert [a["codigo"] for a in r["avisos"]] == ["decisiones_corregidas"] and "30" in r["avisos"][0]["mensaje"]


def test_con_pocas_opiniones_no_se_avisa_aunque_el_porcentaje_sea_alto(db, usuario):
    llenar(db, usuario, 1, 4, label="fuera_de_tema", feedback="en_tema")

    assert ai_drift.compute(db, ahora=AHORA)["avisos"] == []


def test_un_cambio_grande_en_las_preguntas_fuera_de_tema_se_detecta(db, usuario):
    llenar(db, usuario, 9, 25, label="en_tema")  # antes: 0 % fuera de tema
    llenar(db, usuario, 1, 15, label="en_tema")
    llenar(db, usuario, 1, 10, label="fuera_de_tema")  # ahora: 40 %

    avisos = ai_drift.compute(db, ahora=AHORA)["avisos"]

    assert [a["codigo"] for a in avisos] == ["cambio_de_temas"]


def test_un_llm_que_tarda_el_doble_se_detecta(db, usuario):
    llenar(db, usuario, 9, 6, llm=True, latencia=2000)
    llenar(db, usuario, 1, 6, llm=True, latencia=4500)

    avisos = ai_drift.compute(db, ahora=AHORA)["avisos"]

    assert [a["codigo"] for a in avisos] == ["llm_mas_lento"]


def test_un_llm_que_falla_mucho_se_detecta(db, usuario):
    llenar(db, usuario, 1, 4, llm=True, llm_ok=True, latencia=2000)
    llenar(db, usuario, 1, 2, llm=True, llm_ok=False)

    assert "llm_fallando" in [a["codigo"] for a in ai_drift.compute(db, ahora=AHORA)["avisos"]]


def test_el_endpoint_responde_para_la_agencia_y_valida_los_dias(client, db, usuario):
    llenar(db, usuario, 0.1, 3)

    respuesta = client.get("/api/assistant/drift", params={"days": 7})

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["ventana_dias"] == 7 and set(cuerpo) == {"ventana_dias", "estado", "actual", "anterior", "avisos"}
    assert client.get("/api/assistant/drift", params={"days": 0}).status_code == 422


def test_el_cliente_no_ve_la_deriva(as_client):
    assert as_client.get("/api/assistant/drift").status_code == 403

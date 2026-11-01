# Pruebas de la generación de borradores con el asistente simulado (spec 012, T05).
import pytest
from sqlalchemy import select

from app.models import AiDraft
from app.services.ai_drafts import WriterError, generate_drafts
from tests.ai_support import mitigated_incident
from tests.fake_ollama import FakeOllama


@pytest.fixture
def incidente(seeded):
    return mitigated_incident(seeded)


def test_guarda_el_resumen_y_el_mensaje_como_borradores(seeded, incidente):
    result = generate_drafts(seeded, incidente, FakeOllama())
    seeded.commit()

    drafts = seeded.scalars(select(AiDraft).order_by(AiDraft.id)).all()
    assert [d.kind for d in drafts] == ["resumen", "mensaje_cliente"]
    assert {d.status for d in drafts} == {"borrador_ia"}
    assert {(d.model, d.prompt_version) for d in drafts} == {("fake-qwen2.5:7b", "v1")}
    assert all(d.latency_ms is not None and d.final_text is None for d in drafts)
    assert result.problems == []
    # El resumen técnico sí puede hablar de rollback y versiones: lo lee la agencia
    assert "v2 a v1" in drafts[0].generated_text and "14:00" in drafts[0].generated_text


def test_el_asistente_solo_recibe_hechos_del_hub(seeded, incidente):
    fake = FakeOllama()
    generate_drafts(seeded, incidente, fake)

    assert [kind for kind, _ in fake.calls] == ["resumen", "mensaje_cliente"]
    assert "@" not in repr(fake.calls)


def test_un_mensaje_con_jerga_no_se_guarda(seeded, incidente):
    fake = FakeOllama({"mensaje_cliente": "Hicimos rollback a la v1 a las 14:07."})
    result = generate_drafts(seeded, incidente, fake)

    assert [d.kind for d in result.drafts] == ["resumen"]
    assert result.problems == [
        "El mensaje al cliente usa términos técnicos que el cliente no debe ver: rollback, versión vN."
    ]


def test_una_hora_inventada_no_se_guarda(seeded, incidente):
    fake = FakeOllama({"resumen": "Empezó a las 14:00 y terminó a las 16:45."})
    result = generate_drafts(seeded, incidente, fake)

    assert [d.kind for d in result.drafts] == ["mensaje_cliente"]
    assert result.problems == ["El resumen cita horas que no son del incidente: 16:45."]


def test_si_el_asistente_falla_no_queda_nada(seeded, incidente):
    with pytest.raises(WriterError):
        generate_drafts(seeded, incidente, FakeOllama(fail=True))
    seeded.rollback()

    assert seeded.scalars(select(AiDraft)).all() == []

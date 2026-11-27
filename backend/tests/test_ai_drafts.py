# Pruebas de los borradores del asistente para un incidente (spec 012, T12-T17): generar el resumen y el mensaje al cliente con el
# LLM simulado, verificar términos del glosario y horas, caer al texto base si la IA falla, aprobar con el texto editado dejando la
# bitácora, y que al portal del cliente solo llegue el mensaje aprobado.
import json
from datetime import timedelta

import pytest
from sqlalchemy import select

from app.config import settings
from app.models import AuditLog, Client, Incident, Project, Service
from app.models.ai_draft import AiDraft
from app.services import ai_drafts
from tests.rollback_support import T0, open_incident

MENSAJE_BUENO = "Detectamos una falla temporal en su sitio a las 14:00 y el servicio volvió a funcionar a las 14:07. Tiempo total: 7 minutos."
RESUMEN_BUENO = "El sitio del restaurante falló de 14:00 a 14:07 por una versión con error de configuración; se hizo rollback de v2 a v1."


@pytest.fixture
def client(as_agency):
    return as_agency


@pytest.fixture
def sazon(seeded) -> Service:
    return seeded.scalar(select(Service).where(Service.namespace == "cliente-restaurante"))


@pytest.fixture
def mitigado(seeded, sazon) -> Incident:
    """Falla de La Sazón de 14:00 a 14:07 (hora de Colombia), con causa y rollback de v2 a v1."""
    incident = open_incident(seeded, sazon, status="mitigado")
    incident.mitigated_at = T0 + timedelta(minutes=7)
    incident.root_cause = "Versión con error de configuración"
    incident.rollback_from_version, incident.rollback_to_version = "v2", "v1"
    seeded.commit()
    return incident


@pytest.fixture
def ia(monkeypatch):
    """Ollama simulado: responde según el tipo de borrador y guarda cada llamada para revisar qué datos recibió."""
    estado = {"mensaje": MENSAJE_BUENO, "resumen": RESUMEN_BUENO, "llamadas": []}

    def transporte(url, body, timeout):
        cuerpo = json.loads(body)
        sistema = cuerpo["messages"][0]["content"]
        estado["llamadas"].append(sistema)
        clave = "mensaje" if "mensajes de una agencia web" in sistema else "resumen"
        texto = estado[clave]
        return (200, json.dumps({"message": {"content": texto}}).encode()) if texto is not None else (500, b"error")

    monkeypatch.setattr(settings, "ollama_url", "http://ollama.test:11434")
    monkeypatch.setattr("app.integrations.ollama.urllib_transport", transporte)
    return estado


def generar(client, incident, **cuerpo):
    return client.post(f"/api/incidents/{incident.id}/ai-drafts", json=cuerpo)


def por_tipo(borradores: list[dict]) -> dict[str, dict]:
    return {b["kind"]: b for b in borradores}


# ---------- Generar ----------


def test_genera_los_dos_borradores_como_borrador_ia(client, mitigado, ia):
    respuesta = generar(client, mitigado)

    assert respuesta.status_code == 201, respuesta.text
    borradores = por_tipo(respuesta.json())
    assert set(borradores) == {"resumen", "mensaje_cliente"}
    for b in borradores.values():
        assert b["status"] == "borrador_ia" and b["source"] == "llm" and b["notice"] is None
        assert b["model"] == settings.ollama_model and b["prompt_version"] == "v1" and b["final_text"] is None
    assert borradores["mensaje_cliente"]["generated_text"] == MENSAJE_BUENO


def test_el_modelo_recibe_solo_los_hechos_reales_del_incidente(client, mitigado, ia):
    generar(client, mitigado)

    resumen = next(s for s in ia["llamadas"] if "resumen técnico" in s)
    assert "inicio de la falla: 14:00" in resumen and "servicio recuperado: 14:07" in resumen and "tiempo total: 7 minutos" in resumen
    assert "causa raíz: Versión con error de configuración" in resumen
    assert "rollback de la versión v2 a la v1" in resumen


def test_el_mensaje_al_cliente_no_recibe_datos_internos(client, mitigado, ia):
    generar(client, mitigado, kinds=["mensaje_cliente"])

    sistema = ia["llamadas"][0]
    assert "14:00" in sistema and "14:07" in sistema
    for interno in ("Versión con error", "v2", "v1", "P1", "El sitio no responde", "La Sazón"):
        assert interno not in sistema.split("DATOS:")[1], interno


def test_se_puede_pedir_solo_un_tipo(client, mitigado, ia):
    respuesta = generar(client, mitigado, kinds=["resumen"])

    assert [b["kind"] for b in respuesta.json()] == ["resumen"]
    assert len(ia["llamadas"]) == 1


def test_un_incidente_sin_mitigar_no_genera_borradores(client, seeded, sazon, ia):
    abierto = open_incident(seeded, sazon)

    respuesta = generar(client, abierto)

    assert respuesta.status_code == 409 and "mitigado" in respuesta.json()["detail"]
    assert ia["llamadas"] == []


def test_un_incidente_inexistente_es_404(client, ia):
    assert client.post("/api/incidents/999/ai-drafts", json={}).status_code == 404


def test_regenerar_descarta_los_borradores_anteriores_sin_aprobar(client, mitigado, ia, db):
    primero = por_tipo(generar(client, mitigado).json())
    segundo = por_tipo(generar(client, mitigado).json())

    assert primero["resumen"]["id"] != segundo["resumen"]["id"]
    estados = {b.id: b.status for b in db.scalars(select(AiDraft))}
    assert estados[primero["resumen"]["id"]] == "descartado" and estados[segundo["resumen"]["id"]] == "borrador_ia"


# ---------- Verificaciones y texto base ----------


def test_un_mensaje_con_jerga_se_rechaza_y_queda_el_texto_base(client, mitigado, ia):
    ia["mensaje"] = "Tuvimos un incidente P1 y hicimos un rollback a la v1 a las 14:07."

    b = por_tipo(generar(client, mitigado).json())["mensaje_cliente"]

    assert b["source"] == "plantilla"
    assert b["generated_text"] == "Detectamos una falla temporal en su sitio a las 14:00. Activamos la recuperación y a las 14:07 el servicio volvió a funcionar. Tiempo total: 7 minutos."
    assert "incidente" in b["notice"] and "rollback" in b["notice"]


def test_un_mensaje_con_horas_inventadas_se_rechaza(client, mitigado, ia):
    ia["mensaje"] = "Detectamos una falla temporal a las 15:30 y se resolvió a las 14:07. Tiempo total: 7 minutos."

    b = por_tipo(generar(client, mitigado).json())["mensaje_cliente"]

    assert b["source"] == "plantilla" and "15:30" in b["notice"]


def test_un_mensaje_con_una_duracion_equivocada_se_rechaza(client, mitigado, ia):
    ia["mensaje"] = "Detectamos una falla temporal a las 14:00 y el servicio volvió a funcionar a las 14:07. Tiempo total: 20 minutos."

    b = por_tipo(generar(client, mitigado).json())["mensaje_cliente"]

    assert b["source"] == "plantilla" and "20 minutos" in b["notice"]


def test_un_resumen_con_horas_que_no_son_las_del_incidente_cae_al_texto_base(client, mitigado, ia):
    ia["resumen"] = "El sitio falló a las 09:15 y se recuperó a las 14:07."

    b = por_tipo(generar(client, mitigado).json())["resumen"]

    assert b["source"] == "plantilla" and "09:15" in b["notice"]
    assert "14:00" in b["generated_text"] and "14:07" in b["generated_text"] and "Causa raíz: Versión con error de configuración" in b["generated_text"]


def test_el_resumen_interno_puede_usar_terminos_tecnicos(client, mitigado, ia):
    b = por_tipo(generar(client, mitigado).json())["resumen"]

    assert b["source"] == "llm" and "rollback" in b["generated_text"]


def test_sin_la_causa_el_texto_base_dice_que_esta_sin_registrar(client, seeded, sazon, ia):
    ia["resumen"] = None
    incidente = open_incident(seeded, sazon, status="mitigado")
    incidente.mitigated_at = T0 + timedelta(minutes=7)
    seeded.commit()

    b = por_tipo(generar(client, incidente).json())["resumen"]

    assert b["source"] == "plantilla" and "Causa raíz: sin registrar" in b["generated_text"] and "No hay rollback registrado" in b["generated_text"]


def test_si_la_ia_no_responde_el_tecnico_recibe_un_texto_base_para_editar(client, mitigado, ia):
    ia["mensaje"] = ia["resumen"] = None

    respuesta = generar(client, mitigado)

    assert respuesta.status_code == 201  # el flujo no se bloquea
    for b in respuesta.json():
        assert b["source"] == "plantilla" and b["status"] == "borrador_ia" and "no respondió" in b["notice"] and b["model"] is None


def test_sin_ollama_configurado_tambien_deja_el_texto_base(client, mitigado, monkeypatch):
    monkeypatch.setattr(settings, "ollama_url", "")

    respuesta = generar(client, mitigado)

    assert respuesta.status_code == 201 and all(b["source"] == "plantilla" for b in respuesta.json())


def test_el_texto_base_del_mensaje_cumple_sus_propias_verificaciones(mitigado, sazon, db):
    h = ai_drafts.facts_for(db.get(Incident, mitigado.id))

    for kind in ai_drafts.KINDS:
        assert ai_drafts.check(ai_drafts.base_text(h, kind), h, kind) == {"terminos_prohibidos": [], "horas_que_no_coinciden": []}


@pytest.mark.parametrize("texto,esperado", [
    ("Se hizo un rollback", ["rollback"]),
    ("Abrimos un ticket P1 con el SLA", ["p1", "sla", "ticket"]),
    ("Volvimos a la v2 por Argo CD", ["argo", "v2"]),
    ("Tuvimos una falla temporal y la recuperación fue rápida", []),
])
def test_los_terminos_prohibidos_salen_del_glosario(texto, esperado):
    assert ai_drafts.forbidden_terms_in(texto) == esperado


# ---------- Aprobar y descartar ----------


def _borrador(client, incident, kind="mensaje_cliente"):
    return por_tipo(generar(client, incident).json())[kind]


def test_aprobar_guarda_el_texto_editado_quien_lo_aprobo_y_la_bitacora(client, mitigado, ia, db):
    borrador = _borrador(client, mitigado)
    editado = "Hola, detectamos una falla temporal a las 14:00 y a las 14:07 el servicio volvió a funcionar. Tiempo total: 7 minutos. Gracias por su paciencia."

    respuesta = client.post(f"/api/ai-drafts/{borrador['id']}/approve", json={"text": editado})

    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["status"] == "aprobado" and cuerpo["final_text"] == editado and cuerpo["generated_text"] == MENSAJE_BUENO
    assert cuerpo["approved_by"] and cuerpo["approved_at"]
    log = db.scalar(select(AuditLog).where(AuditLog.action == "ai_draft.aprobar"))
    assert log.entity == "ai_draft" and log.entity_id == borrador["id"] and log.details["editado"] is True and log.details["fuente"] == "llm"


def test_aprobar_sin_texto_aprueba_el_borrador_tal_cual(client, mitigado, ia, db):
    borrador = _borrador(client, mitigado)

    cuerpo = client.post(f"/api/ai-drafts/{borrador['id']}/approve", json={}).json()

    assert cuerpo["final_text"] == MENSAJE_BUENO
    assert db.scalar(select(AuditLog).where(AuditLog.action == "ai_draft.aprobar")).details["editado"] is False


def test_no_se_aprueba_un_mensaje_al_cliente_con_jerga(client, mitigado, ia, db):
    borrador = _borrador(client, mitigado)

    respuesta = client.post(f"/api/ai-drafts/{borrador['id']}/approve", json={"text": "Hicimos un rollback a las 14:07."})

    assert respuesta.status_code == 422 and "rollback" in respuesta.json()["detail"]
    assert db.get(AiDraft, borrador["id"]).status == "borrador_ia"
    assert db.scalar(select(AuditLog).where(AuditLog.action == "ai_draft.aprobar")) is None


def test_no_se_aprueba_un_mensaje_con_horas_que_no_son_las_del_incidente(client, mitigado, ia):
    borrador = _borrador(client, mitigado)

    respuesta = client.post(f"/api/ai-drafts/{borrador['id']}/approve", json={"text": "Hubo una falla temporal a las 16:45."})

    assert respuesta.status_code == 422 and "16:45" in respuesta.json()["detail"]


def test_no_se_aprueba_un_texto_vacio(client, mitigado, ia):
    borrador = _borrador(client, mitigado, "resumen")

    assert client.post(f"/api/ai-drafts/{borrador['id']}/approve", json={"text": "   "}).status_code == 422


def test_un_borrador_aprobado_no_se_aprueba_ni_se_descarta_de_nuevo(client, mitigado, ia):
    borrador = _borrador(client, mitigado)
    client.post(f"/api/ai-drafts/{borrador['id']}/approve", json={})

    assert client.post(f"/api/ai-drafts/{borrador['id']}/approve", json={}).status_code == 422
    assert client.post(f"/api/ai-drafts/{borrador['id']}/discard").status_code == 409


def test_descartar_deja_la_bitacora_y_el_cliente_no_recibe_nada(client, mitigado, ia, db):
    borrador = _borrador(client, mitigado)

    respuesta = client.post(f"/api/ai-drafts/{borrador['id']}/discard")

    assert respuesta.status_code == 200 and respuesta.json()["status"] == "descartado"
    assert db.scalar(select(AuditLog).where(AuditLog.action == "ai_draft.descartar")).entity_id == borrador["id"]
    assert ai_drafts.approved_message(db, mitigado.id) is None


def test_un_borrador_inexistente_es_404(client):
    assert client.post("/api/ai-drafts/999/approve", json={}).status_code == 404
    assert client.post("/api/ai-drafts/999/discard").status_code == 404


def test_se_listan_los_borradores_del_incidente(client, mitigado, ia):
    generar(client, mitigado)

    lista = client.get(f"/api/incidents/{mitigado.id}/ai-drafts").json()

    assert len(lista) == 2 and lista[0]["id"] > lista[1]["id"]


# ---------- Lo que ve el cliente ----------


def _incidentes_del_portal(usuario, db, incident):
    cliente_id = db.scalar(select(Client.id).join(Project, Project.client_id == Client.id).join(Service, Service.project_id == Project.id).where(Service.id == incident.service_id))
    mes = incident.started_at.strftime("%Y-%m")
    return usuario.get(f"/api/dashboard/client/{cliente_id}/incidents?month={mes}")


def test_el_portal_solo_muestra_el_mensaje_aprobado(client, as_client, mitigado, ia, db):
    borrador = _borrador(client, mitigado)

    antes = _incidentes_del_portal(as_client, db, mitigado)
    assert antes.status_code == 200 and antes.json()[0]["message"] is None  # un borrador no llega al cliente

    client.post(f"/api/ai-drafts/{borrador['id']}/approve", json={})
    despues = _incidentes_del_portal(as_client, db, mitigado).json()[0]
    assert despues["message"] == MENSAJE_BUENO


def test_un_borrador_descartado_no_llega_al_portal(client, as_client, mitigado, ia, db):
    borrador = _borrador(client, mitigado)
    client.post(f"/api/ai-drafts/{borrador['id']}/discard")

    assert _incidentes_del_portal(as_client, db, mitigado).json()[0]["message"] is None


def test_el_resumen_tecnico_nunca_llega_al_portal(client, as_client, mitigado, ia, db):
    resumen = _borrador(client, mitigado, "resumen")
    client.post(f"/api/ai-drafts/{resumen['id']}/approve", json={})

    assert _incidentes_del_portal(as_client, db, mitigado).json()[0]["message"] is None


def test_el_cliente_no_genera_ni_aprueba_borradores(client, as_client, mitigado, ia):
    borrador = _borrador(client, mitigado)

    assert as_client.post(f"/api/incidents/{mitigado.id}/ai-drafts", json={}).status_code == 403
    assert as_client.get(f"/api/incidents/{mitigado.id}/ai-drafts").status_code == 403
    assert as_client.post(f"/api/ai-drafts/{borrador['id']}/approve", json={}).status_code == 403
    assert as_client.post(f"/api/ai-drafts/{borrador['id']}/discard").status_code == 403


def test_sin_sesion_es_401(anonymous, mitigado):
    assert anonymous.post(f"/api/incidents/{mitigado.id}/ai-drafts", json={}).status_code == 401
    assert anonymous.post("/api/ai-drafts/1/approve", json={}).status_code == 401

# Pruebas de los reportes mensuales (spec 013): las cifras son las de los tableros (CA-5), el ejecutivo cabe en una página y no trae jerga
# (CA-2, CA-3), ambos se generan para cualquier mes y cliente y se descargan en PDF (CA-4), el cliente solo ve lo suyo y los datos quedan
# congelados al generarlos.
import io
import json
from datetime import datetime, timedelta, timezone

import pytest
from pypdf import PdfReader
from sqlalchemy import select

from app.models import AuditLog, Client, Deployment, Service
from app.models.ai_draft import AiDraft
from app.services import ai_drafts, kpi, report_pdf, reports
from tests.rollback_support import T0, open_incident
from tests.test_kpi import _solicitud

MES = "2026-10"  # T0 (14:00 en Colombia) cae en octubre de 2026
MENSAJE = "Detectamos una falla temporal en su sitio a las 14:00 y el servicio volvió a funcionar a las 14:07. Tiempo total: 7 minutos."


@pytest.fixture
def client(as_agency):
    return as_agency


@pytest.fixture
def sazon(seeded) -> Service:
    return seeded.scalar(select(Service).where(Service.namespace == "cliente-restaurante"))


@pytest.fixture
def prometheus(monkeypatch):
    """Prometheus simulado: la consulta devuelve la fracción 0,9995 (kpi la pasa a 99,95 %; el SLO Premium es 99,9 %) y una latencia de 0,3 s."""
    monkeypatch.setattr(kpi.prometheus, "query", lambda promql, at, transport=None: 0.9995 if "probe_success" in promql else 0.3)


@pytest.fixture
def datos(seeded, sazon):
    """Octubre de La Sazón: una falla con mensaje aprobado, una actualización publicada, un rollback y dos solicitudes."""
    incidente = open_incident(seeded, sazon, status="mitigado")
    incidente.mitigated_at = T0 + timedelta(minutes=7)
    seeded.add(AiDraft(incident_id=incidente.id, kind="mensaje_cliente", status="aprobado", source="llm", generated_text=MENSAJE, final_text=MENSAJE,
                       approved_at=T0 + timedelta(minutes=30)))
    # Un resumen técnico aprobado jamás llega al cliente
    seeded.add(AiDraft(incident_id=incidente.id, kind="resumen", status="aprobado", source="llm", generated_text="Falló el Pod por una dependencia.",
                       final_text="Falló el Pod por una dependencia.", approved_at=T0 + timedelta(minutes=30)))
    seeded.add(Deployment(service_id=sazon.id, version="v2", author="Sofía", source="cambio", created_at=T0 - timedelta(days=3)))
    seeded.add(Deployment(service_id=sazon.id, version="v1", author="Sofía", source="rollback", created_at=T0 + timedelta(minutes=8)))
    creado = datetime(2026, 10, 5, 14, 0, tzinfo=timezone.utc)
    plazos = {"response_due_at": creado + timedelta(minutes=15), "resolution_due_at": creado + timedelta(hours=4)}
    _solicitud(seeded, sazon.id, "abierto", creado, **plazos)
    _solicitud(seeded, sazon.id, "cerrado", creado, first_response_at=creado + timedelta(minutes=5), resolved_at=creado + timedelta(minutes=10),
               closed_at=creado + timedelta(minutes=12), **plazos)
    seeded.commit()
    return incidente


def generar(client, **cuerpo):
    return client.post("/api/reports", json=cuerpo)


def texto_pdf(contenido: bytes) -> str:
    return " ".join(p.extract_text() for p in PdfReader(io.BytesIO(contenido)).pages)


# ---------- Reporte ejecutivo ----------


def test_el_ejecutivo_resume_disponibilidad_fallas_actualizaciones_y_solicitudes(client, datos, prometheus, sazon):
    respuesta = generar(client, kind="ejecutivo", client_id=sazon.project.client_id, month=MES)

    assert respuesta.status_code == 201, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["kind"] == "ejecutivo" and cuerpo["month_label"] == "octubre de 2026" and cuerpo["client_name"] == "Restaurante La Sazón"
    d = cuerpo["data"]
    assert d["disponibilidad"]["valor"] == 99.95 and d["disponibilidad"]["objetivo"] == 99.9 and d["disponibilidad"]["cumple"] is True
    assert d["disponibilidad"]["texto"] == "Su sitio se mantuvo disponible dentro del objetivo acordado."
    assert d["fallas"]["total"] == 1 and d["fallas"]["listadas"][0]["texto"] == MENSAJE  # el texto aprobado por una persona
    assert d["fallas"]["tiempo_de_recuperacion_promedio"] is None  # con una sola falla el promedio sobra
    assert d["fallas"]["listadas"][0]["duracion"] == "7 minutos" and d["fallas"]["listadas"][0]["cuando"].endswith("14:00")
    assert d["actualizaciones"]["publicadas"] == 1  # el rollback no cuenta como actualización
    assert d["solicitudes"] == {"abiertas": 1, "atendidas": 1, "texto": "Recibimos 2 solicitudes y atendimos 1."}


def test_el_ejecutivo_no_trae_jerga_en_ningun_texto(client, datos, prometheus, sazon):
    d = generar(client, kind="ejecutivo", client_id=sazon.project.client_id, month=MES).json()["data"]

    textos = [d["disponibilidad"]["texto"], d["actualizaciones"]["texto"], d["solicitudes"]["texto"], *(f["texto"] for f in d["fallas"]["listadas"])]
    for texto in textos:
        assert ai_drafts.terminos_prohibidos_en(texto) == [], texto
    assert ai_drafts.terminos_prohibidos_en(texto_pdf(report_pdf.ejecutivo_pdf(d))) == []
    assert "dependencia" not in str(d)  # el resumen técnico aprobado no entra al reporte del cliente


def test_sin_mensaje_aprobado_la_falla_usa_la_frase_del_glosario(client, seeded, sazon, prometheus):
    incidente = open_incident(seeded, sazon, status="mitigado")
    incidente.mitigated_at = T0 + timedelta(minutes=7)
    seeded.add(AiDraft(incident_id=incidente.id, kind="mensaje_cliente", status="borrador_ia", source="llm", generated_text=MENSAJE))
    seeded.commit()

    d = generar(client, kind="ejecutivo", client_id=sazon.project.client_id, month=MES).json()["data"]

    assert d["fallas"]["listadas"][0]["texto"] == "Se detectó una falla temporal y se activó el proceso de recuperación."  # un borrador no se muestra


def test_un_mes_sin_fallas_ni_solicitudes_lo_dice_con_las_frases_del_glosario(client, seeded, sazon, prometheus):
    d = generar(client, kind="ejecutivo", client_id=sazon.project.client_id, month="2026-03").json()["data"]

    assert d["fallas"]["texto"] == "No tuvimos fallas que afectaran su sitio este mes."
    assert d["solicitudes"]["texto"] == "Este mes no abrió solicitudes."
    assert d["actualizaciones"]["texto"] == "Este mes no hubo actualizaciones de su sitio."


def test_un_nan_de_prometheus_se_guarda_como_sin_datos_y_el_json_es_estricto(client, seeded, sazon, monkeypatch):
    # Prometheus devuelve NaN en la latencia de un sitio sin tráfico; PostgreSQL rechaza NaN en una columna JSON (lo descubrió el clúster real)
    monkeypatch.setattr(kpi.prometheus, "query", lambda promql, at, transport=None: float("nan"))

    operativo = generar(client, kind="operativo", month=MES).json()["data"]
    ejecutivo = generar(client, kind="ejecutivo", client_id=sazon.project.client_id, month=MES).json()["data"]

    for datos in (operativo, ejecutivo):
        json.dumps(datos, allow_nan=False)  # lanza ValueError si queda algún NaN o infinito
    assert all(f["latencia_p95"] is None and f["disponibilidad"] is None for f in operativo["clientes"])
    assert ejecutivo["disponibilidad"]["valor"] is None and ejecutivo["disponibilidad"]["texto"] == "Todavía no tenemos datos de su sitio este mes."
    assert report_pdf.operativo_pdf(operativo).startswith(b"%PDF") and report_pdf.ejecutivo_pdf(ejecutivo).startswith(b"%PDF")


def test_sin_nan_limpia_estructuras_anidadas():
    assert reports.sin_nan({"a": float("nan"), "b": [1.0, float("inf"), {"c": float("-inf")}], "d": 2}) == {"a": None, "b": [1.0, None, {"c": None}], "d": 2}


def test_el_texto_de_solicitudes_respeta_el_singular(client, seeded, sazon, prometheus):
    _solicitud(seeded, sazon.id, "abierto", datetime(2026, 10, 5, 14, 0, tzinfo=timezone.utc))
    seeded.commit()

    d = generar(client, kind="ejecutivo", client_id=sazon.project.client_id, month=MES).json()["data"]

    assert d["solicitudes"]["texto"] == "Recibimos 1 solicitud y atendimos 0."


def test_sin_datos_del_monitoreo_el_ejecutivo_no_inventa_una_disponibilidad(client, seeded, sazon):
    d = generar(client, kind="ejecutivo", client_id=sazon.project.client_id, month=MES).json()["data"]  # sin Prometheus

    assert d["disponibilidad"]["valor"] is None
    assert d["disponibilidad"]["texto"] == "Todavía no tenemos datos de su sitio este mes."


def test_por_debajo_del_objetivo_el_texto_lo_explica_sin_alarmar(client, seeded, sazon, monkeypatch):
    monkeypatch.setattr(kpi.prometheus, "query", lambda promql, at, transport=None: 0.98 if "probe_success" in promql else 0.3)

    d = generar(client, kind="ejecutivo", client_id=sazon.project.client_id, month=MES).json()["data"]

    assert d["disponibilidad"]["cumple"] is False and "menos de lo acordado" in d["disponibilidad"]["texto"]


def test_el_ejecutivo_cabe_en_una_pagina_incluso_con_muchas_fallas_y_mensajes_largos(client, seeded, sazon, prometheus):
    largo = "Detectamos una falla temporal en su sitio y activamos la recuperación. " * 25
    for i in range(9):
        incidente = open_incident(seeded, sazon, started_at=T0 + timedelta(hours=i), status="mitigado")
        incidente.mitigated_at = incidente.started_at + timedelta(minutes=5)
        seeded.add(AiDraft(incident_id=incidente.id, kind="mensaje_cliente", status="aprobado", source="llm", generated_text=largo, final_text=largo,
                           approved_at=T0 + timedelta(days=1)))
    seeded.commit()
    d = reports.ejecutivo(seeded, sazon.project.client_id, MES)

    assert d["fallas"]["total"] == 9 and len(d["fallas"]["listadas"]) == reports.MAX_INCIDENTES_LISTADOS and d["fallas"]["sin_listar"] == 4
    assert len(PdfReader(io.BytesIO(report_pdf.ejecutivo_pdf(d))).pages) == 1


def test_el_pdf_ejecutivo_dice_lo_que_dice_el_reporte(client, datos, prometheus, sazon):
    reporte = generar(client, kind="ejecutivo", client_id=sazon.project.client_id, month=MES).json()

    respuesta = client.get(f"/api/reports/{reporte['id']}/pdf")

    assert respuesta.status_code == 200 and respuesta.headers["content-type"] == "application/pdf"
    assert "reporte-ejecutivo-2026-10-restaurante-la-sazon.pdf" in respuesta.headers["content-disposition"]
    paginas = PdfReader(io.BytesIO(respuesta.content)).pages
    assert len(paginas) == 1
    texto = " ".join(paginas[0].extract_text().split())
    for esperado in ("octubre de 2026", "Restaurante La Sazón", "99,95 %", "99,9 %", "dentro del objetivo acordado", "Recibimos 2 solicitudes y atendimos 1."):
        assert esperado in texto, esperado


# ---------- Reporte operativo ----------


def test_las_cifras_del_operativo_son_las_del_dashboard_de_la_agencia(client, datos, prometheus):
    tablero = {c["client_id"]: c for c in client.get(f"/api/dashboard/agency?month={MES}").json()["clients"]}

    d = generar(client, kind="operativo", month=MES).json()["data"]

    assert [c["client_id"] for c in d["clientes"]] == sorted(tablero)
    for fila in d["clientes"]:
        t = tablero[fila["client_id"]]
        assert (fila["disponibilidad"], fila["cumple_objetivo"], fila["sla"], fila["mttr"], fila["latencia_p95"]) == (
            t["availability"], t["cumple_objetivo"], t["sla_compliance"], t["mttr"], t["latency_p95"])
        assert (fila["solicitudes_abiertas"], fila["solicitudes_cerradas"], fila["horas"], fila["costo"]) == (
            t["open_tickets"], t["closed_tickets"], t["hours"], t["cost"])


def test_el_operativo_trae_el_mes_anterior_los_totales_y_la_carga_de_los_tecnicos(client, datos, prometheus):
    d = generar(client, kind="operativo", month=MES).json()["data"]

    assert d["mes_anterior"] == "2026-09" and d["etiqueta_mes_anterior"] == "septiembre de 2026"
    assert all("mes_anterior" in fila and "mttr" in fila["mes_anterior"] for fila in d["clientes"])
    sazon_fila = next(f for f in d["clientes"] if f["cliente"] == "Restaurante La Sazón")
    assert sazon_fila["incidentes"] == 1 and sazon_fila["mttr"] == 7.0 and sazon_fila["solicitudes_abiertas"] == 1
    assert d["totales"]["incidentes"] == 1 and d["totales"]["solicitudes_abiertas"] == 1 and d["totales"]["solicitudes_cerradas"] == 1
    assert d["tecnicos"] and {"nombre", "horas", "carga"} <= set(d["tecnicos"][0])


def test_el_mes_anterior_de_enero_es_diciembre_del_ano_anterior():
    assert reports.mes_anterior("2026-01") == "2025-12" and reports.mes_anterior("2026-10") == "2026-09"


def test_el_pdf_operativo_lista_los_clientes_y_el_mes_anterior(client, datos, prometheus):
    reporte = generar(client, kind="operativo", month=MES).json()

    respuesta = client.get(f"/api/reports/{reporte['id']}/pdf")

    assert respuesta.status_code == 200 and respuesta.content.startswith(b"%PDF")
    texto = " ".join(texto_pdf(respuesta.content).split())
    for esperado in ("Reporte operativo", "octubre de 2026", "septiembre de 2026", "Restaurante La Sazón", "Ferretería El Tornillo", "Consultorio Dental Popayán", "Carga de los técnicos"):
        assert esperado in texto, esperado


# ---------- Generación, congelado y permisos ----------


def test_se_genera_para_cualquier_mes_y_cliente_y_queda_en_la_bitacora(client, seeded, prometheus, db):
    for cliente in db.scalars(select(Client)).all():
        assert generar(client, kind="ejecutivo", client_id=cliente.id, month="2025-12").status_code == 201
    assert generar(client, kind="operativo", month="2027-02").status_code == 201

    acciones = db.scalars(select(AuditLog).where(AuditLog.action == "report.generar")).all()
    assert len(acciones) == db.scalar(select(Client.id).order_by(Client.id.desc())) + 1
    assert acciones[0].details["mes"] == "2025-12"


def test_sin_mes_se_usa_el_mes_actual(client, seeded, prometheus):
    assert generar(client, kind="operativo").json()["month"] == kpi.mes_actual()


def test_los_datos_quedan_congelados_al_generar(client, datos, prometheus, sazon, seeded):
    reporte = generar(client, kind="ejecutivo", client_id=sazon.project.client_id, month=MES).json()
    pdf_antes = client.get(f"/api/reports/{reporte['id']}/pdf").content
    texto_antes = texto_pdf(pdf_antes)

    # Después de generarlo cambian las solicitudes y el monitoreo: el reporte ya generado no se mueve
    _solicitud(seeded, sazon.id, "abierto", datetime(2026, 10, 6, 9, 0, tzinfo=timezone.utc))
    seeded.commit()
    kpi.prometheus._cache.clear()
    leido = client.get(f"/api/reports/{reporte['id']}").json()["data"]

    assert leido["solicitudes"]["abiertas"] == 1 and leido["disponibilidad"]["valor"] == 99.95
    assert texto_pdf(client.get(f"/api/reports/{reporte['id']}/pdf").content) == texto_antes
    assert reports.ejecutivo(seeded, sazon.project.client_id, MES)["solicitudes"]["abiertas"] == 2  # un reporte nuevo sí ve el cambio


@pytest.mark.parametrize("cuerpo,estado", [
    ({"kind": "ejecutivo", "month": MES}, 422),
    ({"kind": "ejecutivo", "client_id": 999, "month": MES}, 404),
    ({"kind": "semanal"}, 422),
    ({"kind": "operativo", "month": "2026-13"}, 422),
    ({"kind": "operativo", "month": "octubre"}, 422),
])
def test_las_peticiones_invalidas_se_rechazan(client, seeded, cuerpo, estado):
    assert generar(client, **cuerpo).status_code == estado


def test_el_cliente_ve_y_descarga_solo_sus_reportes_ejecutivos(client, as_client, datos, prometheus, sazon, seeded):
    propio = generar(client, kind="ejecutivo", client_id=sazon.project.client_id, month=MES).json()
    ajeno_id = seeded.scalar(select(Client.id).where(Client.id != sazon.project.client_id))
    ajeno = generar(client, kind="ejecutivo", client_id=ajeno_id, month=MES).json()
    operativo = generar(client, kind="operativo", month=MES).json()

    assert [r["id"] for r in as_client.get("/api/reports").json()] == [propio["id"]]
    assert as_client.get(f"/api/reports/{propio['id']}").status_code == 200
    assert as_client.get(f"/api/reports/{propio['id']}/pdf").status_code == 200
    for otro in (ajeno["id"], operativo["id"]):  # el de otro cliente y el interno: 404, no se revela que existen
        assert as_client.get(f"/api/reports/{otro}").status_code == 404
        assert as_client.get(f"/api/reports/{otro}/pdf").status_code == 404


def test_el_cliente_no_genera_reportes_y_sin_sesion_es_401(as_client, anonymous, sazon):
    assert as_client.post("/api/reports", json={"kind": "operativo"}).status_code == 403
    assert anonymous.post("/api/reports", json={"kind": "operativo"}).status_code == 401
    assert anonymous.get("/api/reports").status_code == 401
    assert anonymous.get("/api/reports/1/pdf").status_code == 401


def test_un_reporte_inexistente_es_404(client):
    assert client.get("/api/reports/999").status_code == 404
    assert client.get("/api/reports/999/pdf").status_code == 404


def test_la_agencia_lista_todos_del_mas_nuevo_al_mas_viejo(client, seeded, prometheus, sazon):
    generar(client, kind="operativo", month=MES)
    generar(client, kind="ejecutivo", client_id=sazon.project.client_id, month=MES)

    lista = client.get("/api/reports").json()

    assert [r["kind"] for r in lista] == ["ejecutivo", "operativo"] and lista[0]["id"] > lista[1]["id"]
    assert "data" not in lista[0]  # la lista no trae los datos completos

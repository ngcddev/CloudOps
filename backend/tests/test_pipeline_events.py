# Eventos del pipeline: abrir una corrida, registrar controles y cerrarla (spec 006, T13).
import pytest
from sqlalchemy import select

from app.config import settings
from app.models import SecurityCheck, SecurityRun, Service

URL = "/api/pipeline-events"
HEADERS = {"Authorization": f"Bearer {settings.pipeline_token}"}
IMAGE_STEPS = ["construccion", "vulnerabilidades", "sbom", "firma", "verificacion"]


@pytest.fixture
def http(anonymous, seeded):
    return anonymous


def _post(http, body, headers=HEADERS):
    return http.post(URL, json=body, headers=headers)


def _inicio(http, site="ferreteria", version="v1.1", images=None):
    body = {"event": "inicio", "site": site, "version": version, "commit_sha": "a" * 40}
    if images is not None:
        body["images"] = images
    return _post(http, body)


def _paso(http, step, status="ok", site="ferreteria", version="v1.1", image=None, summary="", report=None):
    body = {"event": "paso", "site": site, "version": version, "step": step, "status": status, "summary": summary}
    if image:
        body["image"] = image
    if report is not None:
        body["report"] = report
    return _post(http, body)


def _fin(http, status="ok", site="ferreteria", version="v1.1", digests=None):
    body = {"event": "fin", "site": site, "version": version, "status": status}
    if digests:
        body["image_digests"] = digests
    return _post(http, body)


def _corrida_completa(http, site="ferreteria", version="v1.1", images=None):
    images = images or [site]
    _inicio(http, site, version, images)
    _paso(http, "secretos", site=site, version=version)
    for image in images:
        for step in IMAGE_STEPS:
            _paso(http, step, site=site, version=version, image=image)


def test_sin_token_o_con_otro_responde_401(http):
    body = {"event": "inicio", "site": "ferreteria", "version": "v1.1"}

    assert http.post(URL, json=body).status_code == 401
    assert _post(http, body, {"Authorization": "Bearer otro-token"}).status_code == 401
    # el token de una sesión de persona tampoco sirve
    assert _post(http, body, {"Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.e30.x"}).status_code == 401


def test_sin_token_configurado_no_acepta_eventos(http, monkeypatch):
    monkeypatch.setattr(settings, "pipeline_token", "")

    assert _post(http, {"event": "inicio", "site": "ferreteria", "version": "v1.1"}, {"Authorization": "Bearer "}).status_code == 401


def test_inicio_abre_una_corrida_en_curso(http, seeded):
    response = _inicio(http, images=["ferreteria"])

    assert response.status_code == 200
    body = response.json()
    assert (body["status"], body["version"], body["images"], body["checks"]) == ("en_curso", "v1.1", ["ferreteria"], [])
    service = seeded.scalar(select(Service).where(Service.namespace == "cliente-ferreteria"))
    assert body["service_id"] == service.id and body["commit_sha"] == "a" * 40


def test_sin_imagenes_declaradas_la_corrida_espera_la_del_sitio(http):
    assert _inicio(http).json()["images"] == ["ferreteria"]


def test_una_corrida_completa_queda_ok_con_sus_seis_controles(http):
    _corrida_completa(http)

    response = _fin(http, "ok", digests={"ferreteria": "sha256:" + "b" * 64})

    body = response.json()
    assert body["status"] == "ok" and body["failed_step"] is None
    assert [c["step"] for c in body["checks"]] == ["secretos", *IMAGE_STEPS]
    assert body["image_digests"] == {"ferreteria": "sha256:" + "b" * 64}
    assert body["finished_at"] is not None


def test_el_reporte_se_guarda_como_evidencia(http, seeded):
    _inicio(http)
    reporte = {"Results": [{"Vulnerabilities": []}]}

    _paso(http, "secretos", summary="Sin secretos", report=reporte)

    check = seeded.scalar(select(SecurityCheck))
    assert check.report == reporte and check.summary == "Sin secretos"


def test_un_control_que_falla_cierra_la_corrida_de_inmediato(http):
    _inicio(http)

    response = _paso(http, "secretos", "fallo", summary="1 secreto en config.js")

    assert response.json()["status"] == "fallo"
    assert response.json()["failed_step"] == "secretos"
    # y ya no acepta más controles
    assert _paso(http, "construccion", image="ferreteria").status_code == 409


def test_fin_ok_sin_todos_los_controles_queda_en_fallo(http):
    _inicio(http)
    _paso(http, "secretos")
    _paso(http, "construccion", image="ferreteria")

    body = _fin(http, "ok").json()

    assert body["status"] == "fallo"
    assert body["failed_step"] == "vulnerabilidades"  # el primer control que faltó


def test_fin_con_fallo_sin_control_fallido_marca_pipeline(http):
    _inicio(http)

    body = _fin(http, "fallo").json()

    assert (body["status"], body["failed_step"]) == ("fallo", "pipeline")


def test_fin_es_idempotente_y_no_reabre_una_corrida_fallida(http):
    _inicio(http)
    _paso(http, "secretos", "fallo")

    body = _fin(http, "ok").json()

    assert (body["status"], body["failed_step"]) == ("fallo", "secretos")


def test_el_consultorio_exige_los_cinco_controles_de_cada_imagen(http):
    images = ["consultorio-web", "consultorio-api"]
    _inicio(http, "consultorio", "v1.1", images)
    _paso(http, "secretos", site="consultorio")
    for step in IMAGE_STEPS:
        _paso(http, step, site="consultorio", image="consultorio-web")

    # falta todo lo de consultorio-api
    body = _fin(http, "ok", site="consultorio").json()
    assert (body["status"], body["failed_step"]) == ("fallo", "construccion")


def test_el_consultorio_pasa_con_las_dos_imagenes_completas(http):
    _corrida_completa(http, "consultorio", "v1.1", ["consultorio-web", "consultorio-api"])

    body = _fin(http, "ok", site="consultorio").json()

    assert body["status"] == "ok"
    assert len(body["checks"]) == 1 + 2 * len(IMAGE_STEPS)


def test_un_control_repetido_o_de_una_imagen_ajena_es_409(http):
    _inicio(http)
    _paso(http, "secretos")

    assert _paso(http, "secretos").status_code == 409
    ajena = _paso(http, "sbom", image="otra-imagen")
    assert ajena.status_code == 409 and "otra-imagen" in ajena.json()["detail"]


def test_un_control_de_imagen_sin_imagen_es_409(http):
    _inicio(http)

    assert _paso(http, "sbom").status_code == 409


def test_subir_la_version_otra_vez_abre_una_corrida_nueva(http, seeded):
    _inicio(http)
    _paso(http, "secretos", "fallo")
    nueva = _inicio(http).json()

    assert nueva["status"] == "en_curso"
    assert len(seeded.scalars(select(SecurityRun)).all()) == 2
    # los controles nuevos van a la corrida nueva, la anterior queda como historial
    assert _paso(http, "secretos").json()["id"] == nueva["id"]


def test_un_paso_sin_corrida_abierta_es_404(http):
    assert _paso(http, "secretos", version="v9").status_code == 404


def test_un_sitio_desconocido_es_404(http):
    assert _inicio(http, site="panaderia").status_code == 404


def test_un_paso_sin_control_o_resultado_es_422_en_espanol(http):
    _inicio(http)

    response = _post(http, {"event": "paso", "site": "ferreteria", "version": "v1.1"})

    assert response.status_code == 422
    assert "control" in response.json()["detail"][0]["msg"]


def test_un_control_desconocido_es_422(http):
    _inicio(http)

    assert _paso(http, "magia").status_code == 422


# --- Cada evento va a su corrida (revisión de código) ---


def _evento_con_corrida(http, run_id, body):
    return _post(http, {**body, "run_id": run_id})


def test_los_eventos_con_run_id_van_a_su_corrida_aunque_haya_una_mas_nueva(http):
    vieja = _inicio(http).json()["id"]
    nueva = _inicio(http).json()["id"]

    # el pipeline viejo sigue vivo y cuenta lo suyo: no debe tocar la corrida nueva
    respuesta = _evento_con_corrida(
        http, vieja, {"event": "paso", "site": "ferreteria", "version": "v1.1", "step": "secretos", "status": "ok"}
    )

    assert respuesta.json()["id"] == vieja
    assert [c["step"] for c in respuesta.json()["checks"]] == ["secretos"]
    sin_tocar = _paso(http, "secretos")  # sin run_id: la última (la nueva), todavía vacía
    assert sin_tocar.json()["id"] == nueva


def test_el_fin_de_un_pipeline_viejo_no_cierra_la_corrida_nueva(http):
    vieja = _inicio(http).json()["id"]
    nueva = _inicio(http).json()["id"]

    cierre = _evento_con_corrida(http, vieja, {"event": "fin", "site": "ferreteria", "version": "v1.1", "status": "fallo"})

    assert (cierre.json()["id"], cierre.json()["status"]) == (vieja, "fallo")
    assert _paso(http, "secretos").json()["id"] == nueva  # la nueva sigue abierta y recibe sus controles


def test_un_run_id_de_otra_version_o_sitio_es_409(http):
    otra = _inicio(http, version="v2").json()["id"]

    respuesta = _evento_con_corrida(
        http, otra, {"event": "paso", "site": "ferreteria", "version": "v1.1", "step": "secretos", "status": "ok"}
    )

    assert respuesta.status_code == 409


def test_un_run_id_que_no_existe_es_404(http):
    respuesta = _evento_con_corrida(
        http, 99999, {"event": "paso", "site": "ferreteria", "version": "v1.1", "step": "secretos", "status": "ok"}
    )

    assert respuesta.status_code == 404

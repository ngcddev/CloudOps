# Registros de la API con id de petición y trace_id (spec 022, T26; auditoría OB-04).
import io
import json
import logging

import pytest
from opentelemetry.sdk.trace import TracerProvider

from app.registros import FormatoJson, id_de_peticion


@pytest.fixture
def lineas():
    """Captura lo que escribe el registro de peticiones, ya con el formato JSON de la API."""
    salida = io.StringIO()
    manejador = logging.StreamHandler(salida)
    manejador.setFormatter(FormatoJson())
    log = logging.getLogger("hub.peticiones")
    nivel = log.level
    log.addHandler(manejador)
    log.setLevel(logging.DEBUG)
    yield lambda: [json.loads(linea) for linea in salida.getvalue().splitlines()]
    log.removeHandler(manejador)
    log.setLevel(nivel)


def test_la_respuesta_trae_un_id_de_peticion_nuevo_si_no_llega_uno(client):
    a = client.get("/health").headers["x-request-id"]
    b = client.get("/health").headers["x-request-id"]
    assert len(a) == 32 and a != b


def test_un_id_valido_que_llega_se_conserva_y_sale_en_la_respuesta_y_en_el_registro(client, lineas):
    respuesta = client.get("/api/tickets/9999", headers={"X-Request-ID": "abc-12345_XYZ.9"})

    assert respuesta.headers["x-request-id"] == "abc-12345_XYZ.9"
    registro = [r for r in lineas() if r["message"] == "petición"][-1]
    assert registro["request_id"] == "abc-12345_XYZ.9" and registro["path"] == "/api/tickets/9999" and registro["method"] == "GET"


@pytest.mark.parametrize("malo", ["corto", "con espacios y mas", "uno\r\ndos-uno-dos", "x" * 65, "<script>alert(1)</script>"])
def test_un_id_que_no_parece_un_id_se_reemplaza(client, malo):
    respuesta = client.get("/health", headers={"X-Request-ID": malo})
    rid = respuesta.headers["x-request-id"]
    assert rid != malo and len(rid) == 32


def test_el_registro_no_incluye_la_cadena_de_consulta(client, lineas):
    client.get("/api/tickets?status=abierto&token=secreto-123")

    registro = [r for r in lineas() if r["message"] == "petición"][-1]
    assert registro["path"] == "/api/tickets" and "secreto" not in json.dumps(registro)


def test_los_sondeos_del_cluster_solo_se_registran_en_debug(client, lineas):
    client.get("/livez")
    registro = [r for r in lineas() if r["message"] == "petición"][-1]
    assert registro["level"] == "DEBUG" and registro["path"] == "/livez"


def test_el_formato_incluye_el_trace_id_cuando_hay_una_traza_activa():
    proveedor = TracerProvider()
    formato = FormatoJson()
    registro = logging.LogRecord("hub.prueba", logging.INFO, __file__, 1, "hola %s", ("mundo",), None)
    token = id_de_peticion.set("peticion-0001")
    try:
        with proveedor.get_tracer("prueba").start_as_current_span("tramo") as tramo:
            datos = json.loads(formato.format(registro))
            esperado = format(tramo.get_span_context().trace_id, "032x")
        sin_traza = json.loads(formato.format(registro))
    finally:
        id_de_peticion.reset(token)

    assert datos["trace_id"] == esperado and len(datos["span_id"]) == 16 and datos["request_id"] == "peticion-0001"
    assert datos["message"] == "hola mundo" and datos["level"] == "INFO" and datos["ts"].endswith("Z")
    assert "trace_id" not in sin_traza   # fuera de una traza no se inventa uno


def test_un_error_sin_atrapar_queda_registrado_con_su_id_y_la_respuesta_es_500(lineas):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.registros import IdDePeticion

    app = FastAPI()

    @app.get("/falla")
    def falla():
        raise RuntimeError("se rompió")

    app.add_middleware(IdDePeticion)
    respuesta = TestClient(app, raise_server_exceptions=False).get("/falla", headers={"X-Request-ID": "falla-0000001"})

    assert respuesta.status_code == 500
    registro = [r for r in lineas() if r["message"] == "Error sin atrapar"][-1]
    assert registro["request_id"] == "falla-0000001" and registro["status"] == 500 and "RuntimeError" in registro["exc"]

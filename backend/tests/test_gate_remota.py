# Pruebas de la compuerta servida por MLflow (spec 016): decide el endpoint cuando responde y el modelo local cuando no.
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from app.services.assistant_gate import EN_TEMA, FUERA_DE_TEMA, RemoteGate, load_model


class _Endpoint:
    """Imita `mlflow models serve`: POST /invocations → {"predictions": [{label, p_fuera_de_tema, despertar_llm}]}."""

    def __init__(self, p_fuera: float | None = 0.99, estado: int = 200):
        self.recibido: list[dict] = []
        endpoint = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                endpoint.recibido.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
                cuerpo = json.dumps({"predictions": [{"label": "x", "p_fuera_de_tema": p_fuera, "despertar_llm": True}]} if p_fuera is not None else {"error": "x"}).encode()
                self.send_response(estado)
                self.send_header("Content-Length", str(len(cuerpo)))
                self.end_headers()
                self.wfile.write(cuerpo)

        self._server = HTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self._server.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self._server.server_port}"

    def cerrar(self):
        self._server.shutdown()
        self._server.server_close()


@pytest.fixture
def local():
    return load_model()


def test_decide_el_endpoint_cuando_responde(local):
    endpoint = _Endpoint(p_fuera=0.99)
    try:
        decision = RemoteGate(endpoint.url, local).decide("¿Cuál es la capital de Francia?")
    finally:
        endpoint.cerrar()
    assert decision.label == FUERA_DE_TEMA and decision.despertar_llm is False
    assert decision.model_version == "mlflow:compuerta@production"
    assert len(decision.model_version) <= 30  # ai_queries.gate_version es varchar(30): PostgreSQL rechaza lo más largo (SQLite no lo nota)
    assert endpoint.recibido == [{"dataframe_split": {"columns": ["text"], "data": [["¿Cuál es la capital de Francia?"]]}}]


def test_una_pregunta_con_vocabulario_de_la_app_nunca_se_salta_al_llm(local):
    endpoint = _Endpoint(p_fuera=0.999)
    try:
        decision = RemoteGate(endpoint.url, local).decide("¿Cómo hago un rollback?")
    finally:
        endpoint.cerrar()
    assert decision.label == EN_TEMA and decision.despertar_llm is True


def test_si_el_endpoint_no_esta_decide_el_modelo_local(local):
    sin_servidor = RemoteGate("http://127.0.0.1:9", local, timeout=0.5)   # el puerto 9 no tiene nada
    decision = sin_servidor.decide("¿Cómo hago un rollback?")
    assert decision == local.decide("¿Cómo hago un rollback?")
    assert decision.model_version == local.version


@pytest.mark.parametrize("p_fuera, estado", [(None, 200), (0.5, 500)])
def test_una_respuesta_inesperada_tambien_cae_al_modelo_local(local, p_fuera, estado):
    endpoint = _Endpoint(p_fuera=p_fuera, estado=estado)
    try:
        decision = RemoteGate(endpoint.url, local).decide("¿Cuál es la capital de Francia?")
    finally:
        endpoint.cerrar()
    assert decision == local.decide("¿Cuál es la capital de Francia?")


def test_load_model_usa_el_endpoint_solo_si_esta_configurado(monkeypatch, local):
    from app.config import settings

    monkeypatch.setattr(settings, "gate_model_url", "")
    assert not isinstance(load_model(), RemoteGate)
    monkeypatch.setattr(settings, "gate_model_url", "http://modelo:5001")
    assert isinstance(load_model(), RemoteGate)

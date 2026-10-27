# Pruebas de la consulta a Prometheus para los dashboards (spec 010, T09).
import json

from app.config import settings
from app.integrations import prometheus


def _cuerpo(payload: dict) -> bytes:
    return json.dumps(payload).encode()


def test_query_devuelve_el_valor_de_la_respuesta_sonda(monkeypatch):
    monkeypatch.setattr(settings, "prometheus_url", "http://prometheus.test:9090")
    recibido = {}

    def transport(url, timeout):
        recibido["url"] = url
        return 200, _cuerpo(
            {
                "status": "success",
                "data": {
                    "resultType": "vector",
                    "result": [{"metric": {"job": "sitios"}, "value": [1761446400, "0.98"]}],
                },
            }
        )

    assert prometheus.query("up", "2026-10", transport=transport) == 0.98
    assert recibido["url"].startswith("http://prometheus.test:9090/api/v1/query")


def test_query_con_respuesta_vacia_devuelve_none(monkeypatch):
    monkeypatch.setattr(settings, "prometheus_url", "http://prometheus.test:9090")

    def transport(url, timeout):
        return 200, _cuerpo({"status": "success", "data": {"result": []}})

    assert prometheus.query("up", "2026-10-vacio", transport=transport) is None


def test_query_con_error_devuelve_none(monkeypatch):
    monkeypatch.setattr(settings, "prometheus_url", "http://prometheus.test:9090")

    def transport(url, timeout):
        return 500, b"error interno"

    assert prometheus.query("up", "2026-10-error", transport=transport) is None


def test_query_con_transporte_que_falla_devuelve_none(monkeypatch):
    monkeypatch.setattr(settings, "prometheus_url", "http://prometheus.test:9090")

    def transport(url, timeout):
        raise OSError("conexión rechazada")

    assert prometheus.query("up", "2026-10-fallo", transport=transport) is None

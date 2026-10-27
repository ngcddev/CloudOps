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


def test_query_sin_transporte_usa_la_consulta_http(monkeypatch):
    """Sin `transport` explícito debe usar urllib, no fallar (los KPI lo pasan como None)."""
    monkeypatch.setattr(settings, "prometheus_url", "http://prometheus.test:9090")
    usado = {}

    def transport(url, timeout):
        usado["url"] = url
        return 200, _cuerpo({"status": "success", "data": {"result": []}})

    monkeypatch.setattr(prometheus, "urllib_transport", transport)
    assert prometheus.query("up", "2026-10-sin-transporte") is None
    assert "prometheus.test" in usado["url"]


def test_query_range_devuelve_los_puntos(monkeypatch):
    from datetime import datetime, timezone

    monkeypatch.setattr(settings, "prometheus_url", "http://prometheus.test:9090")
    recibido = {}

    def transport(url, timeout):
        recibido["url"] = url
        return 200, _cuerpo(
            {
                "status": "success",
                "data": {
                    "resultType": "matrix",
                    "result": [
                        {
                            "metric": {"job": "sitios"},
                            "values": [[1761446400, "0.98"], [1761446700, "0.5"]],
                        }
                    ],
                },
            }
        )

    puntos = prometheus.query_range(
        "up",
        datetime(2026, 10, 1, tzinfo=timezone.utc),
        datetime(2026, 10, 2, tzinfo=timezone.utc),
        transport=transport,
    )

    assert puntos is not None
    assert [valor for _, valor in puntos] == [0.98, 0.5]
    assert puntos[0][0].tzinfo is not None
    assert "step=300" in recibido["url"]
    assert "start=" in recibido["url"] and "end=" in recibido["url"]


def test_query_range_sin_serie_devuelve_lista_vacia(monkeypatch):
    from datetime import datetime, timezone

    monkeypatch.setattr(settings, "prometheus_url", "http://prometheus.test:9090")

    def transport(url, timeout):
        return 200, _cuerpo({"status": "success", "data": {"result": []}})

    assert (
        prometheus.query_range(
            "up",
            datetime(2026, 10, 1, tzinfo=timezone.utc),
            datetime(2026, 10, 2, tzinfo=timezone.utc),
            transport=transport,
        )
        == []
    )


def test_query_range_con_prometheus_caido_devuelve_none(monkeypatch):
    from datetime import datetime, timezone

    monkeypatch.setattr(settings, "prometheus_url", "http://prometheus.test:9090")

    def transport(url, timeout):
        raise OSError("conexión rechazada")

    assert (
        prometheus.query_range(
            "up",
            datetime(2026, 10, 1, tzinfo=timezone.utc),
            datetime(2026, 10, 2, tzinfo=timezone.utc),
            transport=transport,
        )
        is None
    )

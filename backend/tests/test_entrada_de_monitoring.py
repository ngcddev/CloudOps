# Entrada de monitoring (spec 022, T17; auditoría K8-02): el namespace niega toda entrada salvo los Pods propios, Traefik hacia Grafana y el namespace hub
# hacia Prometheus, Loki y el receptor OTLP de Tempo. Si alguien abre algo más (otro namespace, otro puerto, un ipBlock), esta prueba falla y obliga a decidirlo.
# Lo que hace en el clúster lo comprueba observability/pruebas/entrada.sh.
from pathlib import Path

import pytest
import yaml

OBS = Path("/repo/observability")
POLITICA = OBS / "networkpolicy.yaml"

pytestmark = pytest.mark.skipif(not POLITICA.exists(), reason="observability no está montado en /repo")


def _politicas() -> dict[str, dict]:
    return {d["metadata"]["name"]: d for d in yaml.safe_load_all(POLITICA.read_text(encoding="utf-8")) if d}


def _ns(nombre: str) -> dict:
    return {"namespaceSelector": {"matchLabels": {"kubernetes.io/metadata.name": nombre}}}


def test_las_politicas_van_en_el_namespace_monitoring():
    assert {p["metadata"]["namespace"] for p in _politicas().values()} == {"monitoring"}


def test_toda_entrada_esta_denegada_por_defecto():
    spec = _politicas()["default-deny-ingress"]["spec"]
    assert spec["podSelector"] == {} and spec["policyTypes"] == ["Ingress"] and "ingress" not in spec


def test_solo_entran_propios_traefik_hacia_grafana_y_el_hub_hacia_sus_puertos():
    spec = _politicas()["permitir-propio-traefik-y-hub"]["spec"]
    assert spec["podSelector"] == {} and spec["policyTypes"] == ["Ingress"]
    propio, traefik, hub = spec["ingress"]
    assert propio == {"from": [{"podSelector": {}}]}
    assert traefik == {"from": [{**_ns("kube-system"), "podSelector": {"matchLabels": {"app.kubernetes.io/name": "traefik"}}}], "ports": [{"protocol": "TCP", "port": 3000}]}
    assert hub["from"] == [_ns("hub")]
    assert sorted(p["port"] for p in hub["ports"]) == [3100, 4318, 9090]


def test_sin_rangos_de_ip_y_el_kustomization_la_incluye():
    assert "ipBlock" not in POLITICA.read_text(encoding="utf-8")
    assert "networkpolicy.yaml" in yaml.safe_load((OBS / "kustomization.yaml").read_text(encoding="utf-8"))["resources"]

# Salida del namespace hub (spec 022, T18; auditoría K8-02): todo sale cerrado salvo el DNS y los Pods del propio namespace, y cada aplicación abre solo lo que usa.
# Si alguien abre un destino (otro namespace, otro puerto, un ipBlock más), esta prueba falla y obliga a decidirlo a propósito. Lo que hacen en el clúster
# lo comprueba gitops/pruebas/salida-hub.sh.
from pathlib import Path

import pytest
import yaml

RUTA = Path("/gitops/hub/networkpolicy.yaml")

pytestmark = pytest.mark.skipif(not RUTA.exists(), reason="gitops no está montado en /gitops")


def _politicas() -> dict[str, dict]:
    return {d["metadata"]["name"]: d for d in yaml.safe_load_all(RUTA.read_text(encoding="utf-8")) if d}


def _ns(nombre: str) -> dict:
    return {"namespaceSelector": {"matchLabels": {"kubernetes.io/metadata.name": nombre}}}


def test_estan_todas_las_politicas_en_el_namespace_hub():
    politicas = _politicas()
    assert set(politicas) == {"default-deny-ingress", "permitir-traefik-alertmanager-y-propio", "default-deny-egress", "permitir-dns-y-propio", "api-salidas", "backstage-salidas"}
    assert {p["metadata"]["namespace"] for p in politicas.values()} == {"hub"}


def test_toda_salida_esta_denegada_por_defecto():
    spec = _politicas()["default-deny-egress"]["spec"]
    assert spec["podSelector"] == {} and spec["policyTypes"] == ["Egress"] and "egress" not in spec


def test_para_todos_solo_dns_y_el_propio_namespace():
    spec = _politicas()["permitir-dns-y-propio"]["spec"]
    assert spec["podSelector"] == {}
    dns, propios = spec["egress"]
    assert dns["to"] == [{**_ns("kube-system"), "podSelector": {"matchLabels": {"k8s-app": "kube-dns"}}}]
    assert sorted((p["protocol"], p["port"]) for p in dns["ports"]) == [("TCP", 53), ("UDP", 53)]
    assert propios == {"to": [{"podSelector": {}}]}


def test_la_api_solo_sale_a_lo_que_usa():
    spec = _politicas()["api-salidas"]["spec"]
    assert spec["podSelector"] == {"matchLabels": {"app": "api"}} and spec["policyTypes"] == ["Egress"]
    destinos = {}
    for regla in spec["egress"]:
        (destino,) = regla["to"]
        clave = destino["namespaceSelector"]["matchLabels"]["kubernetes.io/metadata.name"] if "namespaceSelector" in destino else destino["ipBlock"]["cidr"]
        destinos[clave] = sorted(p["port"] for p in regla["ports"])
    assert destinos == {"gitea": [3000], "argocd": [8080], "monitoring": [3100, 4318, 9090], "192.168.65.254/32": [11434]}


def test_backstage_solo_sale_a_gitea():
    spec = _politicas()["backstage-salidas"]["spec"]
    assert spec["podSelector"] == {"matchLabels": {"app": "backstage"}}
    assert spec["egress"] == [{"to": [_ns("gitea")], "ports": [{"protocol": "TCP", "port": 3000}]}]


def test_el_unico_rango_de_ip_es_ollama_en_el_host():
    # Sin esto, un ipBlock 0.0.0.0/0 abriría internet entero; el único permitido es la dirección de host.docker.internal (Ollama fuera del clúster).
    cidrs = [r["ipBlock"]["cidr"] for p in _politicas().values() for e in p["spec"].get("egress", []) for r in e["to"] if "ipBlock" in r]
    assert cidrs == ["192.168.65.254/32"]

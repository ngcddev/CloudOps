# Salida de red de los clientes (spec 022, T14; auditoría K8-02): la base de cada cliente niega toda salida y solo deja el DNS y los Pods del mismo cliente, tanto en
# Kustomize como en el chart de Helm. Si alguien abre una salida (un ipBlock, otro namespace, otro puerto), esta prueba falla y obliga a decidirlo a propósito.
# Lo que la política hace en el clúster lo comprueba gitops/pruebas/salida-red.sh.
from pathlib import Path

import pytest
import yaml

GITOPS = Path("/gitops")
BASE = GITOPS / "clients" / "_base" / "networkpolicy.yaml"
CHART = GITOPS / "charts" / "sitio-cliente" / "templates" / "networkpolicy.yaml"

pytestmark = pytest.mark.skipif(not BASE.exists(), reason="gitops no está montado en /gitops")


def _politicas(ruta: Path) -> dict[str, dict]:
    # El chart lleva expresiones de Helm ({{ ... }}) que no son YAML válido: se reemplazan por un texto fijo
    texto = ruta.read_text(encoding="utf-8")
    texto = texto.replace('{{ include "sitio.namespace" . }}', "cliente-prueba")
    return {d["metadata"]["name"]: d for d in yaml.safe_load_all(texto) if d}


@pytest.fixture(params=[BASE, CHART], ids=["kustomize", "helm"])
def politicas(request):
    return _politicas(request.param)


def test_estan_las_cuatro_politicas(politicas):
    assert set(politicas) == {"default-deny-ingress", "permitir-traefik-monitoreo-y-propio", "default-deny-egress", "permitir-dns-y-propio"}


def test_toda_salida_esta_denegada_por_defecto(politicas):
    denegar = politicas["default-deny-egress"]["spec"]
    assert denegar["podSelector"] == {} and denegar["policyTypes"] == ["Egress"]
    assert "egress" not in denegar, "una política que deniega no puede traer reglas de salida"


def test_solo_se_permite_dns_y_los_pods_del_mismo_cliente(politicas):
    permitir = politicas["permitir-dns-y-propio"]["spec"]
    assert permitir["podSelector"] == {} and permitir["policyTypes"] == ["Egress"]
    destinos = permitir["egress"]
    assert len(destinos) == 2, "solo dos destinos: CoreDNS y los Pods del mismo cliente"

    dns, propios = destinos
    assert dns["to"] == [{"namespaceSelector": {"matchLabels": {"kubernetes.io/metadata.name": "kube-system"}}, "podSelector": {"matchLabels": {"k8s-app": "kube-dns"}}}]
    assert sorted((p["protocol"], p["port"]) for p in dns["ports"]) == [("TCP", 53), ("UDP", 53)]
    assert propios == {"to": [{"podSelector": {}}]}, "los Pods del mismo namespace, sin puertos ni namespaces ajenos"


def test_ninguna_salida_usa_rangos_de_ip(politicas):
    for nombre, politica in politicas.items():
        assert "ipBlock" not in yaml.safe_dump(politica), f"{nombre} abre un rango de IP (internet o la red del nodo)"


def test_las_politicas_de_entrada_siguen_como_estaban(politicas):
    entrada = politicas["permitir-traefik-monitoreo-y-propio"]["spec"]
    origenes = entrada["ingress"][0]["from"]
    assert {"namespaceSelector": {"matchLabels": {"kubernetes.io/metadata.name": "kube-system"}}} in origenes   # Traefik
    assert {"namespaceSelector": {"matchLabels": {"kubernetes.io/metadata.name": "monitoring"}}} in origenes    # Prometheus y Blackbox
    assert {"podSelector": {}} in origenes
    assert politicas["default-deny-ingress"]["spec"]["policyTypes"] == ["Ingress"]


@pytest.mark.skipif(not CHART.exists(), reason="el chart no está montado")
def test_el_chart_y_kustomize_dicen_lo_mismo():
    kustomize, chart = _politicas(BASE), _politicas(CHART)
    for nombre in kustomize:
        assert kustomize[nombre]["spec"] == chart[nombre]["spec"], f"{nombre} difiere entre Kustomize y el chart"

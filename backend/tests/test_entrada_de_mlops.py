# Entrada de MLflow (spec 022, T15; auditoría K8-02): MLflow no pide autenticación, así que su namespace solo acepta entrada de Traefik y de sus propios Pods.
# Si alguien abre la entrada (otro namespace, un ipBlock, sin selector), esta prueba falla. Lo que hace en el clúster lo comprueba gitops/pruebas/entrada-mlops.sh.
from pathlib import Path

import pytest
import yaml

MLOPS = Path("/gitops/platform/mlops")
POLITICA = MLOPS / "networkpolicy.yaml"

pytestmark = pytest.mark.skipif(not POLITICA.exists(), reason="gitops no está montado en /gitops")


def _politica() -> dict:
    return yaml.safe_load(POLITICA.read_text(encoding="utf-8"))


def test_solo_entra_traefik_y_el_propio_namespace():
    spec = _politica()["spec"]
    assert spec["podSelector"] == {} and spec["policyTypes"] == ["Ingress"]
    assert spec["ingress"] == [{"from": [
        {"namespaceSelector": {"matchLabels": {"kubernetes.io/metadata.name": "kube-system"}}, "podSelector": {"matchLabels": {"app.kubernetes.io/name": "traefik"}}},
        {"podSelector": {}},
    ]}]


def test_la_politica_no_usa_rangos_de_ip():
    assert "ipBlock" not in POLITICA.read_text(encoding="utf-8")


def test_el_kustomization_la_incluye():
    recursos = yaml.safe_load((MLOPS / "kustomization.yaml").read_text(encoding="utf-8"))["resources"]
    assert "networkpolicy.yaml" in recursos

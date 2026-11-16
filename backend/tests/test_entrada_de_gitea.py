# Entrada de Gitea (spec 022, T16; auditoría K8-02): solo Traefik, Argo CD, el namespace hub y el propio namespace llegan a Gitea. Si alguien la abre
# (un ipBlock, otro namespace, sin selector), esta prueba falla. Un error real que evita: sin `namespace: gitea` la política caía en `default` y no protegía nada.
# Lo que hace en el clúster lo comprueba gitops/pruebas/entrada-gitea.sh.
from pathlib import Path

import pytest
import yaml

GITEA = Path("/gitops/platform/gitea")
POLITICA = GITEA / "networkpolicy.yaml"

pytestmark = pytest.mark.skipif(not POLITICA.exists(), reason="gitops no está montado en /gitops")


def _ns(nombre: str) -> dict:
    return {"namespaceSelector": {"matchLabels": {"kubernetes.io/metadata.name": nombre}}}


def test_la_politica_va_en_el_namespace_de_gitea():
    assert yaml.safe_load(POLITICA.read_text(encoding="utf-8"))["metadata"]["namespace"] == "gitea"


def test_solo_entran_la_plataforma_y_el_propio_namespace():
    spec = yaml.safe_load(POLITICA.read_text(encoding="utf-8"))["spec"]
    assert spec["podSelector"] == {} and spec["policyTypes"] == ["Ingress"]
    assert spec["ingress"] == [{"from": [
        {**_ns("kube-system"), "podSelector": {"matchLabels": {"app.kubernetes.io/name": "traefik"}}},
        _ns("argocd"),
        _ns("hub"),
        {"podSelector": {}},
    ]}]


def test_sin_rangos_de_ip_y_el_kustomization_la_incluye():
    assert "ipBlock" not in POLITICA.read_text(encoding="utf-8")
    assert "networkpolicy.yaml" in yaml.safe_load((GITEA / "kustomization.yaml").read_text(encoding="utf-8"))["resources"]

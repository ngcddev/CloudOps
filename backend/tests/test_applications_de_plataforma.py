# La plataforma entra por Git (spec 022, T30; auditoría K8-06): el Hub, la observabilidad, Backstage, MLflow y los respaldos tienen una Application de Argo CD cada uno, con
# `selfHeal` y sin `prune` (un cambio a mano se revierte y un borrado por error en Git no se lleva un volumen), y lo que reconcilian se promueve a hub-gitops.
# Gitea y Argo CD son la excepción de arranque documentada: no hay Application para ellos.
import re
from pathlib import Path

import pytest
import yaml

APPS = Path("/gitops/platform/argocd/applications")
SINCRONIZADOR = Path("/gitops/sincronizar-hub-gitops.sh")

pytestmark = pytest.mark.skipif(not APPS.exists(), reason="gitops no está montado en /gitops")

PLATAFORMA = {
    "plataforma-mlops": ("platform/mlops", "mlops"),
    "plataforma-backstage": ("platform/backstage", "hub"),
    "plataforma-respaldo": ("platform/respaldo", "argocd"),
}


def _app(nombre: str) -> dict:
    return yaml.safe_load((APPS / f"{nombre}.yaml").read_text(encoding="utf-8"))


@pytest.mark.parametrize("nombre", sorted(PLATAFORMA))
def test_cada_application_de_plataforma_apunta_a_su_carpeta_con_selfheal_y_sin_prune(nombre):
    ruta, namespace = PLATAFORMA[nombre]
    app = _app(nombre)
    assert app["kind"] == "Application" and app["metadata"]["name"] == nombre and app["metadata"]["namespace"] == "argocd"
    assert app["spec"]["source"]["path"] == ruta and app["spec"]["source"]["repoURL"] == "http://gitea.gitea.svc:3000/forja-digital/hub-gitops.git"
    assert app["spec"]["destination"]["namespace"] == namespace
    automatico = app["spec"]["syncPolicy"]["automated"]
    assert automatico["selfHeal"] is True and automatico["prune"] is False


@pytest.mark.skipif(not SINCRONIZADOR.exists(), reason="el sincronizador no está montado")
def test_lo_que_reconcilian_se_promueve_a_hub_gitops():
    completos = re.search(r"COMPLETOS=\((.*?)\)", SINCRONIZADOR.read_text(encoding="utf-8")).group(1)
    for ruta, _ in PLATAFORMA.values():
        assert f'"gitops/{ruta}:{ruta}"' in completos, f"{ruta} no está en el mapa de promoción: la Application no encontraría nada en hub-gitops"


def test_gitea_y_argocd_no_tienen_application_porque_no_se_reconcilian_a_si_mismos():
    for archivo in APPS.glob("*.yaml"):
        for doc in yaml.safe_load_all(archivo.read_text(encoding="utf-8")):
            if doc and doc.get("kind") == "Application":
                assert doc["spec"].get("source", {}).get("path") not in {"platform/gitea", "platform/argocd"}, archivo.name


def test_las_carpetas_de_plataforma_arman_con_kustomize():
    # Cada carpeta tiene su kustomization.yaml (lo que Argo CD renderiza)
    for ruta, _ in PLATAFORMA.values():
        assert (Path("/gitops") / ruta / "kustomization.yaml").exists(), ruta

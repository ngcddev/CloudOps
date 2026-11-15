# Pruebas de menor privilegio en Kubernetes (spec 017, T06): ningún Pod monta el token de la API de Kubernetes si no la usa, los permisos son mínimos
# y los clientes se despliegan desde un AppProject que no deja crear nada fuera de sus namespaces.
from pathlib import Path

import pytest
import yaml

GITOPS = Path("/gitops")
CARGAS = {"Deployment", "StatefulSet", "DaemonSet", "CronJob", "Job"}
# Los únicos que hablan con la API de Kubernetes, cada uno con su ServiceAccount y un rol mínimo (el de Prometheus y el de Alloy están en observability/)
USAN_LA_API = {"respaldo"}


def _documentos():
    for ruta in sorted(GITOPS.rglob("*.yaml")):
        if "charts" in ruta.parts or "docs" in ruta.parts:  # plantillas de Helm (no son YAML puro) y documentación de Backstage
            continue
        for doc in yaml.safe_load_all(ruta.read_text(encoding="utf-8")):
            if isinstance(doc, dict) and "kind" in doc:
                yield ruta.relative_to(GITOPS), doc


def _pod(doc: dict) -> dict:
    plantilla = doc["spec"]["jobTemplate"]["spec"]["template"] if doc["kind"] == "CronJob" else doc["spec"]["template"]
    return plantilla["spec"]


def test_los_pods_que_no_usan_la_api_no_montan_el_token():
    sin_proteger = []
    for ruta, doc in _documentos():
        if doc["kind"] not in CARGAS:
            continue
        pod = _pod(doc)
        if pod.get("serviceAccountName") in USAN_LA_API:
            continue
        if pod.get("automountServiceAccountToken") is not False:
            sin_proteger.append(f"{ruta}: {doc['kind']}/{doc['metadata']['name']}")
    assert not sin_proteger, "estos Pods montan el token de la API sin necesitarlo: " + ", ".join(sin_proteger)


def test_las_plantillas_de_helm_tambien_lo_desactivan():
    for plantilla in (GITOPS / "charts/sitio-cliente/templates").glob("*.yaml"):
        texto = plantilla.read_text(encoding="utf-8")
        if "kind: Deployment" in texto:
            assert "automountServiceAccountToken: false" in texto, plantilla.name


def test_la_plantilla_que_escribe_el_hub_tambien_lo_desactiva():
    texto = Path("/app/app/assets/gitops/landing_form_backend.yaml").read_text(encoding="utf-8")

    assert "automountServiceAccountToken: false" in texto


def test_los_roles_no_usan_comodines():
    for ruta, doc in _documentos():
        if doc["kind"] in {"Role", "ClusterRole"}:
            for regla in doc["rules"]:
                for campo in ("verbs", "resources", "apiGroups"):
                    assert "*" not in regla.get(campo, []), f"{ruta}: {doc['metadata']['name']} usa «*» en {campo}"


def test_los_roles_del_respaldo_solo_leen():
    for ruta, doc in _documentos():
        if doc["kind"] == "Role" and doc["metadata"]["name"] == "respaldo":
            verbos = {v for regla in doc["rules"] for v in regla["verbs"]}
            assert verbos <= {"get", "list"}, f"{ruta}: el respaldo no debe escribir"


PROYECTO = GITOPS / "platform/argocd/projects/clientes.yaml"


@pytest.mark.skipif(not PROYECTO.exists(), reason="el AppProject llega con T06c")
def test_el_appproject_de_los_clientes_limita_destinos_y_recursos():
    proyecto = yaml.safe_load(PROYECTO.read_text(encoding="utf-8"))["spec"]

    assert {d["namespace"] for d in proyecto["destinations"]} == {"cliente-*"}
    # Lo único de alcance de clúster que un cliente puede crear es su namespace
    assert proyecto["clusterResourceWhitelist"] == [{"group": "", "kind": "Namespace"}]
    permitidos = {r["kind"] for r in proyecto["namespaceResourceWhitelist"]}
    assert not permitidos & {"ClusterRole", "ClusterRoleBinding", "Role", "RoleBinding", "Secret", "CustomResourceDefinition"}
    assert len(proyecto["sourceRepos"]) == 1 and proyecto["sourceRepos"][0].endswith("/hub-gitops.git")


@pytest.mark.skipif(not PROYECTO.exists(), reason="el AppProject llega con T06c")
def test_los_clientes_se_despliegan_desde_su_proyecto():
    for ruta, doc in _documentos():
        if doc["kind"] == "Application" and ruta.name.startswith("cliente-"):
            assert doc["spec"]["project"] == "clientes", ruta
        if doc["kind"] == "ApplicationSet":
            assert doc["spec"]["template"]["spec"]["project"] == "clientes"

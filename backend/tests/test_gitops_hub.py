# Pruebas de los manifiestos del Hub (gitops/hub): todo lo que se genera o se declara va al namespace `hub`. Un ConfigMap generado sin
# namespace se crea en el del contexto de kubectl (default) y el CronJob de respaldo no lo encuentra: lo descubrió el clúster real.
from pathlib import Path

import pytest
import yaml

HUB = Path("/gitops/hub")


def _yaml(nombre: str) -> list[dict]:
    return [d for d in yaml.safe_load_all((HUB / nombre).read_text(encoding="utf-8")) if d]


def test_los_generadores_de_kustomize_fijan_el_namespace_hub():
    kustomization = _yaml("kustomization.yaml")[0]

    generadores = kustomization.get("configMapGenerator", []) + kustomization.get("secretGenerator", [])
    assert generadores, "se esperaba al menos el ConfigMap hub-respaldo"
    for generador in generadores:
        assert generador.get("namespace") == "hub", f"{generador['name']} se crearía fuera del namespace hub"


@pytest.mark.parametrize("archivo", ["api.yaml", "web.yaml", "postgres.yaml", "backup.yaml", "networkpolicy.yaml", "ingress.yaml", "escalado.yaml"])
def test_cada_recurso_del_hub_declara_su_namespace(archivo):
    for recurso in _yaml(archivo):
        assert recurso["metadata"].get("namespace") == "hub", f"{recurso['kind']}/{recurso['metadata']['name']} de {archivo} no declara namespace: hub"


def test_el_cronjob_monta_el_configmap_que_genera_kustomize():
    cron = next(r for r in _yaml("backup.yaml") if r["kind"] == "CronJob")
    volumenes = cron["spec"]["jobTemplate"]["spec"]["template"]["spec"]["volumes"]
    generado = _yaml("kustomization.yaml")[0]["configMapGenerator"][0]

    assert any(v.get("configMap", {}).get("name") == generado["name"] for v in volumenes)
    assert generado.get("options", {}).get("disableNameSuffixHash") is True  # kustomize no renombra la referencia dentro de un CronJob


def test_el_escalado_apunta_a_deployments_que_existen_y_con_requests_de_cpu():
    """Un HPA por CPU no funciona si el Pod no declara `requests.cpu`; y un PDB sin Pods que lo respondan no protege nada."""
    escalado = _yaml("escalado.yaml")
    deployments = {d["metadata"]["name"]: d for archivo in ("api.yaml", "web.yaml") for d in _yaml(archivo) if d["kind"] == "Deployment"}

    hpas = [r for r in escalado if r["kind"] == "HorizontalPodAutoscaler"]
    assert {h["spec"]["scaleTargetRef"]["name"] for h in hpas} == {"api", "web"}
    for hpa in hpas:
        destino = deployments[hpa["spec"]["scaleTargetRef"]["name"]]
        contenedores = destino["spec"]["template"]["spec"]["containers"]
        assert all("cpu" in c["resources"]["requests"] for c in contenedores)
        assert hpa["spec"]["maxReplicas"] <= 2, "la API lleva tareas en segundo plano que se repetirían con más réplicas"

    for pdb in (r for r in escalado if r["kind"] == "PodDisruptionBudget"):
        etiquetas = pdb["spec"]["selector"]["matchLabels"]
        destino = deployments[etiquetas["app"]]
        assert destino["spec"]["template"]["metadata"]["labels"]["app"] == etiquetas["app"]


def test_kustomize_incluye_el_escalado():
    assert "escalado.yaml" in _yaml("kustomization.yaml")[0]["resources"]

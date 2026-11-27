# Pruebas del chart de Helm del sitio de cliente (spec 017, T04): sin helm en la imagen de pruebas, se comprueba a nivel de YAML que los valores del chart dicen lo mismo
# que el overlay de Kustomize de cada cliente. La equivalencia de lo renderizado la comprueba gitops/pruebas/helm-vs-kustomize.sh (helm template contra kustomize build).
from pathlib import Path

import pytest
import yaml

CHART = Path("/gitops/charts/sitio-cliente")
CLIENTES = Path("/gitops/clients")
VALORES = sorted(p.stem for p in (CHART / "valores").glob("*.yaml"))


def _yaml(ruta: Path):
    return yaml.safe_load(ruta.read_text(encoding="utf-8"))


def _parche(kustomization: dict, tipo: str) -> list[dict]:
    return yaml.safe_load(next(p for p in kustomization["patches"] if p["target"]["kind"] == tipo)["patch"])


def _valor(operaciones: list[dict], ruta: str):
    return next(op["value"] for op in operaciones if op["path"] == ruta)


def test_el_chart_es_un_chart_v2_y_trae_los_recursos_de_la_base():
    chart = _yaml(CHART / "Chart.yaml")
    plantillas = {p.name for p in (CHART / "templates").iterdir()}

    assert chart["apiVersion"] == "v2" and chart["name"] == "sitio-cliente" and chart["type"] == "application"
    # La base de Kustomize trae namespace, cuota, rango de límites, red, sitio, servicio e Ingress
    assert {"namespace.yaml", "cuota.yaml", "networkpolicy.yaml", "web.yaml", "ingress.yaml", "backend.yaml"} <= plantillas


def test_hay_valores_de_ferreteria_y_de_consultorio_cubren_landing_y_formulario():
    assert {"ferreteria", "consultorio"} <= set(VALORES)


@pytest.mark.parametrize("cliente", VALORES)
def test_los_valores_del_chart_dicen_lo_mismo_que_el_overlay_de_kustomize(cliente):
    valores, overlay = _yaml(CHART / "valores" / f"{cliente}.yaml"), _yaml(CLIENTES / cliente / "kustomization.yaml")
    etiquetas = _parche(overlay, "Namespace")

    assert valores["cliente"] == cliente and overlay["namespace"] == f"cliente-{cliente}"
    assert valores["plan"] == _valor(etiquetas, "/metadata/labels/hub~1plan")
    assert valores["host"] == _valor(_parche(overlay, "Ingress"), "/spec/rules/0/host")
    cuota = _parche(overlay, "ResourceQuota")
    assert valores["cuota"] == {"cpu": _valor(cuota, "/spec/hard/limits.cpu"), "memoria": _valor(cuota, "/spec/hard/limits.memory")}
    imagenes = {i["name"].rsplit("/", 1)[1]: i for i in overlay["images"]}
    assert valores["imagen"]["repositorio"] == imagenes["plantilla"]["newName"]
    assert valores["imagen"]["etiqueta"] == str(imagenes["plantilla"]["newTag"])
    # El backend solo se habilita si el overlay lo trae
    assert valores.get("backend", {}).get("habilitado", False) == ("backend.yaml" in overlay["resources"])
    if "plantilla-api" in imagenes:
        assert valores["backend"]["imagen"]["repositorio"] == imagenes["plantilla-api"]["newName"]


def test_el_chart_no_baja_la_seguridad_de_la_base():
    web = (CHART / "templates/web.yaml").read_text(encoding="utf-8")
    namespace = (CHART / "templates/namespace.yaml").read_text(encoding="utf-8")

    # Mismas garantías que gitops/clients/_base: sin root, sin escalada, sin capacidades y Pod Security restricted
    for linea in ("runAsNonRoot: true", "allowPrivilegeEscalation: false", "drop: [ALL]", "type: RuntimeDefault"):
        assert linea in web
    assert "pod-security.kubernetes.io/enforce: restricted" in namespace

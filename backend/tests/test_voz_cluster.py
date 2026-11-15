# Voz en el clúster (spec 021, T06): los manifiestos del servicio de voz y del HTTPS del Hub son coherentes entre sí y seguros, sin necesitar el clúster.
from pathlib import Path

import pytest
import yaml

GITOPS = Path("/gitops/hub")
pytestmark = pytest.mark.skipif(not GITOPS.exists(), reason="gitops/ no está montado")


def _docs(nombre: str) -> list[dict]:
    return [d for d in yaml.safe_load_all((GITOPS / nombre).read_text(encoding="utf-8")) if d]


def _por_clase(docs: list[dict], clase: str, nombre: str) -> dict:
    return next(d for d in docs if d["kind"] == clase and d["metadata"]["name"] == nombre)


def test_el_servicio_de_voz_corre_sin_root_de_solo_lectura_y_con_token():
    pod = _por_clase(_docs("voz.yaml"), "Deployment", "voz")["spec"]["template"]["spec"]
    contenedor = pod["containers"][0]

    assert pod["securityContext"]["runAsNonRoot"] is True and pod["automountServiceAccountToken"] is False
    assert contenedor["securityContext"]["readOnlyRootFilesystem"] is True and contenedor["securityContext"]["allowPrivilegeEscalation"] is False
    assert contenedor["securityContext"]["capabilities"]["drop"] == ["ALL"]
    token = next(e for e in contenedor["env"] if e["name"] == "VOZ_TOKEN")
    assert token["valueFrom"]["secretKeyRef"]["name"] == "hub-voz"
    assert contenedor["image"].startswith("gitea.hub.local/forja-digital/hub-voz:v") and not contenedor["image"].endswith(":latest")
    assert contenedor["resources"]["limits"]["memory"] and contenedor["resources"]["requests"]["memory"]
    assert "hostPort" not in contenedor["ports"][0]


def test_el_servicio_de_voz_no_tiene_ingress():
    for archivo in ("ingress.yaml",):
        for ingress in (d for d in _docs(archivo) if d["kind"] == "Ingress"):
            for regla in ingress["spec"]["rules"]:
                for ruta in regla["http"]["paths"]:
                    assert ruta["backend"]["service"]["name"] != "voz", "el servicio de voz solo debe alcanzarlo la API del Hub"


def test_la_api_llama_al_servicio_de_voz_con_su_nombre_y_puerto():
    servicio = _por_clase(_docs("voz.yaml"), "Service", "voz")
    puerto = servicio["spec"]["ports"][0]["port"]
    api = _por_clase(_docs("api.yaml"), "Deployment", "api")["spec"]["template"]["spec"]["containers"][0]
    entorno = {e["name"]: e for e in api["env"]}

    assert entorno["VOZ_URL"]["value"] == f"http://voz.hub.svc:{puerto}"
    assert entorno["VOZ_TOKEN"]["valueFrom"]["secretKeyRef"]["name"] == "hub-voz"
    assert entorno["VOZ_TOKEN"]["valueFrom"]["secretKeyRef"]["key"] == "VOZ_TOKEN"


def test_el_hub_tiene_https_para_el_microfono_y_conserva_el_http():
    ingresos = {d["metadata"]["name"]: d for d in _docs("ingress.yaml") if d["kind"] == "Ingress"}

    assert set(ingresos) >= {"hub", "hub-https"}
    seguro = ingresos["hub-https"]
    assert seguro["metadata"]["annotations"]["traefik.ingress.kubernetes.io/router.entrypoints"] == "websecure"
    assert seguro["spec"]["tls"][0]["hosts"] == ["hub.local"]
    rutas = {r["path"] for regla in seguro["spec"]["rules"] for r in regla["http"]["paths"]}
    assert rutas == {"/", "/api"}
    assert "tls" not in ingresos["hub"]["spec"], "el HTTP plano sigue abierto para los scripts, el runner y Alertmanager"


def test_la_kustomization_incluye_la_voz_y_los_secretos_la_crean():
    assert "voz.yaml" in yaml.safe_load((GITOPS / "kustomization.yaml").read_text(encoding="utf-8"))["resources"]
    assert "create secret generic hub-voz" in (GITOPS / "crear-secretos.sh").read_text(encoding="utf-8")

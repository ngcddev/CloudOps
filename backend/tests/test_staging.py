# Pruebas del ambiente de pruebas (staging) y de la promoción (spec 017, T03): el overlay de staging es el mismo sitio con otro namespace y dirección,
# el ApplicationSet lo recoge solo, y el script de promoción no puede saltarse la comprobación ni el Hub.
import re
from pathlib import Path

import pytest
import yaml

GITOPS = Path("/gitops")
CLIENTES = GITOPS / "clients"
STAGINGS = sorted(p.name for p in CLIENTES.glob("*-staging"))


def _kustomization(carpeta: str) -> dict:
    return yaml.safe_load((CLIENTES / carpeta / "kustomization.yaml").read_text(encoding="utf-8"))


def _parche(kustomization: dict, tipo: str) -> list[dict]:
    parche = next(p for p in kustomization["patches"] if p["target"]["kind"] == tipo)
    return yaml.safe_load(parche["patch"])


def _valor(operaciones: list[dict], ruta: str):
    return next(op["value"] for op in operaciones if op["path"] == ruta)


def _milis(cpu: str) -> int:
    return int(cpu[:-1]) if cpu.endswith("m") else int(float(cpu) * 1000)


def test_hay_al_menos_un_cliente_con_staging():
    assert STAGINGS, "se esperaba gitops/clients/<cliente>-staging"


@pytest.mark.parametrize("staging", STAGINGS)
def test_el_staging_es_el_mismo_sitio_con_su_propio_namespace_y_direccion(staging):
    cliente = staging.removesuffix("-staging")
    prod, prueba = _kustomization(cliente), _kustomization(staging)

    assert prueba["namespace"] == f"cliente-{cliente}-staging"
    assert prueba["resources"] == prod["resources"]  # misma base
    # Misma imagen: lo que se prueba es lo que se promueve
    assert prueba["images"][0]["newName"] == prod["images"][0]["newName"]
    etiquetas = _parche(prueba, "Namespace")
    assert _valor(etiquetas, "/metadata/labels/hub~1env") == "staging"
    assert _valor(etiquetas, "/metadata/name") == prueba["namespace"]
    assert _valor(_parche(prueba, "Ingress"), "/spec/rules/0/host") == f"{cliente}-staging.hub.local"
    # No pisa a producción: otro host y otro namespace
    assert _valor(_parche(prod, "Ingress"), "/spec/rules/0/host") != _valor(_parche(prueba, "Ingress"), "/spec/rules/0/host")


@pytest.mark.parametrize("staging", STAGINGS)
def test_staging_no_gasta_mas_cuota_que_produccion(staging):
    prod, prueba = _kustomization(staging.removesuffix("-staging")), _kustomization(staging)
    cpu_prod = _milis(_valor(_parche(prod, "ResourceQuota"), "/spec/hard/limits.cpu"))
    cpu_prueba = _milis(_valor(_parche(prueba, "ResourceQuota"), "/spec/hard/limits.cpu"))

    assert cpu_prueba <= cpu_prod


def test_el_applicationset_recoge_el_staging_sin_excluirlo():
    appset = yaml.safe_load((GITOPS / "platform/argocd/applications/clientes-appset.yaml").read_text(encoding="utf-8"))
    directorios = appset["spec"]["generators"][0]["git"]["directories"]
    excluidos = [d["path"] for d in directorios if d.get("exclude")]

    assert "clients/*" in [d["path"] for d in directorios if not d.get("exclude")]
    assert not [e for e in excluidos if e.endswith("-staging")]


def test_la_promocion_pasa_por_la_comprobacion_de_staging_y_por_el_hub():
    texto = (GITOPS / "staging/promover.sh").read_text(encoding="utf-8")

    # Primero comprueba staging y se detiene si no está lista; solo después pide el cambio por el camino normal del Hub
    assert texto.index("no se promueve") < texto.index("/api/change-requests")
    assert "/approve" in texto and "readyReplicas" in texto and "updatedReplicas" in texto
    # Nunca escribe en producción por su cuenta: el commit de producción lo escribe el Hub al aprobar
    assert not re.search(r"clients/\$\{CLIENTE\}/kustomization\.yaml[^\n]*-X\s+PUT", texto)


def test_publicar_solo_toca_el_staging():
    texto = (GITOPS / "staging/publicar.sh").read_text(encoding="utf-8")

    assert 'RUTA="clients/${CLIENTE}-staging/kustomization.yaml"' in texto

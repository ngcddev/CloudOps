# Validación de los catalog-info.yaml de Backstage de cada cliente (spec 005, T21 · RF-22 · CA-6).
from pathlib import Path

import pytest
import yaml

CLIENTES = {
    "restaurante": ("restaurante.hub.local", "Restaurante La Sazón"),
    "ferreteria": ("ferreteria.hub.local", "Ferretería El Tornillo"),
    "consultorio": ("consultorio.hub.local", "Consultorio Dental Popayán"),
}
GITOPS = Path(__file__).resolve().parents[2] / "gitops"


def _load(cliente: str) -> dict:
    path = GITOPS / "clients" / cliente / "catalog-info.yaml"
    if not path.exists():
        pytest.skip("gitops/ no está en esta imagen; corre en el repo completo")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("cliente", CLIENTES)
def test_es_un_componente_de_backstage_de_forja_digital(cliente):
    entity = _load(cliente)

    assert entity["apiVersion"] == "backstage.io/v1alpha1"
    assert entity["kind"] == "Component"
    assert entity["spec"]["owner"] == "forja-digital"
    assert entity["spec"]["type"] == "website"
    assert entity["metadata"]["name"]
    assert CLIENTES[cliente][1] in entity["metadata"]["title"]


@pytest.mark.parametrize("cliente", CLIENTES)
def test_enlaza_al_hub_y_al_sitio_del_cliente(cliente):
    entity = _load(cliente)

    urls = {link["url"] for link in entity["metadata"]["links"]}
    assert "http://hub.local/agencia/servicios" in urls
    assert f"http://{CLIENTES[cliente][0]}" in urls
    assert entity["metadata"]["annotations"]["hub.local/console-url"] == "http://hub.local/agencia/servicios"


def test_los_nombres_son_unicos():
    names = [_load(cliente)["metadata"]["name"] for cliente in CLIENTES]

    assert len(set(names)) == 3


@pytest.mark.parametrize("cliente", CLIENTES)
def test_argocd_no_aplica_el_catalogo(cliente):
    # kustomize solo despliega lo que lista kustomization.yaml: catalog-info no debe estar ahí
    path = GITOPS / "clients" / cliente / "kustomization.yaml"
    if not path.exists():
        pytest.skip("gitops/ no está en esta imagen; corre en el repo completo")

    assert "catalog-info" not in path.read_text(encoding="utf-8")

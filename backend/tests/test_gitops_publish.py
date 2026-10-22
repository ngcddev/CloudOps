# Pruebas de las rutas de hub-gitops que se arman a partir del namespace (spec 005).
import pytest

from app.services.gitops_publish import client_slug, kustomization_path


def test_el_namespace_de_un_cliente_da_su_carpeta():
    assert client_slug("cliente-ferreteria") == "ferreteria"
    assert kustomization_path("cliente-dental-popayan") == "clients/dental-popayan/kustomization.yaml"


@pytest.mark.parametrize(
    "namespace",
    ["ferreteria", "cliente-", "cliente-../x", "cliente-a/b", "cliente-A", "cliente-a b", "hub", ""],
)
def test_un_namespace_que_no_es_de_un_cliente_se_rechaza(namespace):
    with pytest.raises(ValueError, match="no corresponde a un cliente"):
        kustomization_path(namespace)

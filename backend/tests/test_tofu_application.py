# La Application de un cliente no se crea en el proyecto `default` ni por dos creadores a la vez (spec 022, T29; auditoría IA-01): el módulo de OpenTofu solo la crea si se
# lo piden, y entonces usa el AppProject `clientes` (destinos y recursos limitados) como el ApplicationSet `clientes`.
import re
from pathlib import Path

import pytest

MODULO = Path("/repo/infra/tofu/modules/client-env")
APPSET = Path("/repo/gitops/platform/argocd/applications/clientes-appset.yaml")

pytestmark = pytest.mark.skipif(not MODULO.exists(), reason="infra/ no está montado en /repo")


def test_la_application_de_opentofu_va_en_el_proyecto_clientes_nunca_en_default():
    texto = (MODULO / "main.tf").read_text(encoding="utf-8")
    assert re.search(r'project\s*=\s*"clientes"', texto)
    assert not re.search(r'project\s*=\s*"default"', texto), "una Application en `default` no tiene lista de destinos ni de recursos permitidos"


def test_por_defecto_opentofu_no_crea_la_application_porque_la_crea_el_applicationset():
    variables = (MODULO / "variables.tf").read_text(encoding="utf-8")
    bloque = re.search(r'variable "crear_application" \{(.*?)\n\}', variables, re.S)
    assert bloque and re.search(r"default\s*=\s*false", bloque.group(1))
    assert re.search(r"count\s*=\s*var\.crear_application\s*\?\s*1\s*:\s*0", (MODULO / "main.tf").read_text(encoding="utf-8"))
    # Y el ApplicationSet sí lo hace, en el mismo proyecto
    if APPSET.exists():
        assert "project: clientes" in APPSET.read_text(encoding="utf-8")


def test_el_overlay_sigue_creandose_siempre():
    assert 'resource "gitea_repository_file" "overlay"' in (MODULO / "main.tf").read_text(encoding="utf-8")

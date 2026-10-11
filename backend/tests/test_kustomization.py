# Pruebas de la edición de images.newTag: solo cambia la línea del tag (spec 005, T10).
import difflib
from pathlib import Path

import pytest

from app.services.kustomization import get_tags, set_new_tag

UNA_IMAGEN = """# Cliente: Ferretería El Tornillo
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: cliente-ferreteria
resources:
  - ../_base
images:
  - name: gitea.hub.local/forja-digital/plantilla
    newName: gitea.hub.local/forja-digital/ferreteria
    newTag: v1
patches:
  - target: { kind: Namespace }
    patch: |-
      - op: replace
        path: /metadata/name
        value: v1
"""

DOS_IMAGENES = """apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
images:
  - name: gitea.hub.local/forja-digital/plantilla
    newName: gitea.hub.local/forja-digital/consultorio-web
    newTag: v1
  - name: gitea.hub.local/forja-digital/plantilla-api
    newName: gitea.hub.local/forja-digital/consultorio-api
    newTag: v1   # web y api van juntas
patches:
  - target: { kind: Namespace }
"""


def _changed_lines(before: str, after: str) -> list[str]:
    diff = difflib.unified_diff(before.splitlines(), after.splitlines(), lineterm="", n=0)
    return [line for line in diff if line[:1] in "+-" and line[:3] not in ("+++", "---")]


def test_cambia_solo_la_linea_del_tag():
    after = set_new_tag(UNA_IMAGEN, "v1.1")

    assert _changed_lines(UNA_IMAGEN, after) == ["-    newTag: v1", "+    newTag: v1.1"]


def test_no_toca_otros_valores_v1_del_archivo():
    after = set_new_tag(UNA_IMAGEN, "v1.1")

    assert "        value: v1\n" in after  # el `value: v1` del parche sigue igual


def test_cambia_web_y_api_juntas_y_conserva_el_comentario():
    after = set_new_tag(DOS_IMAGENES, "v1.1")

    assert get_tags(after) == ["v1.1", "v1.1"]
    assert "    newTag: v1.1   # web y api van juntas\n" in after
    assert len(_changed_lines(DOS_IMAGENES, after)) == 4


def test_conserva_los_fines_de_linea_crlf():
    crlf = UNA_IMAGEN.replace("\n", "\r\n")

    after = set_new_tag(crlf, "v1.1")

    assert "    newTag: v1.1\r\n" in after
    assert after.count("\r\n") == crlf.count("\r\n")


def test_es_idempotente_y_reversible():
    assert set_new_tag(UNA_IMAGEN, "v1") == UNA_IMAGEN
    assert set_new_tag(set_new_tag(UNA_IMAGEN, "v1.1"), "v1") == UNA_IMAGEN


def test_pone_comillas_si_la_etiqueta_se_leeria_como_numero():
    after = set_new_tag(UNA_IMAGEN, "2.0")

    assert '    newTag: "2.0"\n' in after


@pytest.mark.parametrize("tag", ["", "v1\nnewName: otra", "v 1", "../x", "-v1", "a" * 129])
def test_rechaza_etiquetas_invalidas(tag):
    with pytest.raises(ValueError, match="etiqueta de imagen válida"):
        set_new_tag(UNA_IMAGEN, tag)


def test_falla_sin_seccion_images_o_sin_newtag():
    with pytest.raises(ValueError, match="images"):
        set_new_tag("kind: Kustomization\n", "v1.1")
    with pytest.raises(ValueError, match="newTag"):
        set_new_tag("images:\n  - name: x\n    newName: y\n", "v1.1")


def test_get_tags_lee_las_versiones():
    assert get_tags(UNA_IMAGEN) == ["v1"]
    assert get_tags(DOS_IMAGENES) == ["v1", "v1"]


@pytest.mark.parametrize("cliente", ["restaurante", "ferreteria", "consultorio"])
def test_con_los_kustomization_reales_solo_cambia_el_tag(cliente):
    path = Path(__file__).resolve().parents[2] / "gitops" / "clients" / cliente / "kustomization.yaml"
    if not path.exists():
        pytest.skip("gitops/ no está en esta imagen; corre en el repo completo")
    before = path.read_text(encoding="utf-8")

    after = set_new_tag(before, "v1.1")

    changed = _changed_lines(before, after)
    assert changed and all(line[1:].strip().startswith("newTag:") for line in changed)
    assert set(get_tags(after)) == {"v1.1"}

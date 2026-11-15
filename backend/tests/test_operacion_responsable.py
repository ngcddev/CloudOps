# Operación responsable (spec 019, T06): las cifras de retención del documento coinciden con las de los manifiestos de observabilidad.
import re
from pathlib import Path

import pytest

REPO = Path("/repo")
DOC = REPO / "docs" / "operacion-responsable.md"

pytestmark = pytest.mark.skipif(not DOC.exists(), reason="el repositorio no está montado en /repo")


def _texto(ruta: str) -> str:
    return (REPO / ruta).read_text(encoding="utf-8")


def test_la_retencion_documentada_es_la_de_los_manifiestos():
    doc = DOC.read_text(encoding="utf-8")
    loki = re.search(r"retention_period:\s*(\S+)", _texto("observability/loki/loki.yaml")).group(1)
    tempo = re.search(r"block_retention:\s*(\S+)", _texto("observability/tempo/tempo.yaml")).group(1)
    prometheus = _texto("observability/prometheus/deployment.yaml")
    tiempo = re.search(r"retention\.time=(\S+)", prometheus).group(1)
    tamano = re.search(r"retention\.size=(\S+)", prometheus).group(1)

    assert f"`{loki}`" in doc, f"el documento no dice la retención de Loki ({loki})"
    assert f"`{tempo}`" in doc, f"el documento no dice la retención de Tempo ({tempo})"
    assert f"`{tiempo}` y `{tamano}`" in doc, f"el documento no dice la retención de Prometheus ({tiempo} y {tamano})"


def test_el_documento_cita_scripts_que_existen():
    doc = DOC.read_text(encoding="utf-8")
    rutas = re.findall(r"`((?:gitops|observability|infra|ai)/[\w./-]+\.(?:sh|yaml|md))`", doc)
    assert rutas
    faltan = [r for r in rutas if not (REPO / r).exists()]
    assert not faltan, f"el documento cita archivos que no existen: {faltan}"


def test_la_prueba_de_drift_existe_y_usa_detailed_exitcode():
    texto = _texto("infra/pruebas/drift.sh")

    assert "-detailed-exitcode" in texto

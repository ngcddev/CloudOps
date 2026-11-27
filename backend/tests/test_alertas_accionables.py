# Alertas accionables (spec 019, T02): toda alerta dice qué hacer y apunta a un runbook que existe.
from pathlib import Path

import pytest
import yaml

REPO = Path("/repo")
REGLAS = REPO / "observability" / "prometheus" / "reglas"

pytestmark = pytest.mark.skipif(not REGLAS.exists(), reason="el repositorio no está montado en /repo")


def _alertas():
    for archivo in sorted(REGLAS.glob("*.yml")):
        for grupo in yaml.safe_load(archivo.read_text(encoding="utf-8"))["groups"]:
            for regla in grupo["rules"]:
                if "alert" in regla:
                    yield archivo.name, regla


def test_hay_alertas_que_revisar():
    assert len(list(_alertas())) >= 3


def test_toda_alerta_trae_accion_y_runbook_que_existe():
    problemas = []
    for archivo, regla in _alertas():
        anotaciones = regla.get("annotations", {})
        nombre = f"{archivo}: {regla['alert']}"
        if not anotaciones.get("accion"):
            problemas.append(f"{nombre} no dice qué hacer (annotations.accion)")
        url = anotaciones.get("runbook_url", "")
        if not url or not (REPO / url).is_file():
            problemas.append(f"{nombre} no apunta a un runbook que exista (runbook_url={url!r})")
    assert not problemas, "; ".join(problemas)

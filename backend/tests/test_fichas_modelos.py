# Fichas de modelos (spec 020, T01): todo modelo que usa el Hub tiene su ficha completa y el índice la enlaza.
import re
from pathlib import Path

import pytest

from app.config import Settings

REPO = Path("/repo")
FICHAS = REPO / "docs" / "modelos"

pytestmark = pytest.mark.skipif(not FICHAS.exists(), reason="el repositorio no está montado en /repo")

CAMPOS = ("Nombre", "Origen", "Licencia", "Uso", "Dónde corre", "Datos que recibe")
SECCIONES = ("## Medición", "## Evaluación", "## Límites", "## Riesgos")


def _slug(modelo: str) -> str:
    """qwen2.5:7b-instruct → qwen2.5-7b-instruct;  nomic-embed-text:latest → nomic-embed-text."""
    return modelo.removesuffix(":latest").replace(":", "-")


def _modelos_en_uso() -> list[str]:
    por_defecto = Settings.model_fields
    return [por_defecto["ollama_model"].default, por_defecto["ollama_embed_model"].default, "compuerta-asistente", "qwen2.5:3b-instruct"]


@pytest.mark.parametrize("modelo", _modelos_en_uso())
def test_cada_modelo_en_uso_tiene_ficha_completa(modelo):
    ruta = FICHAS / f"{_slug(modelo)}.md"
    assert ruta.exists(), f"falta la ficha de {modelo}"
    texto = ruta.read_text(encoding="utf-8")
    for campo in CAMPOS:
        assert re.search(rf"^\| {campo}[^|]*\| \S", texto, re.MULTILINE), f"{ruta.name}: falta el campo «{campo}»"
    for seccion in SECCIONES:
        assert seccion in texto, f"{ruta.name}: falta {seccion}"
    if modelo != "compuerta-asistente":
        assert re.search(r"\| Digest \| `[0-9a-f]{64}`", texto), f"{ruta.name}: falta el digest del modelo"


def test_el_indice_enlaza_todas_las_fichas_y_trae_privacidad_y_riesgos():
    indice = (FICHAS / "README.md").read_text(encoding="utf-8")
    for ficha in FICHAS.glob("*.md"):
        if ficha.name != "README.md":
            assert f"({ficha.name})" in indice, f"el índice no enlaza {ficha.name}"
    for titulo in ("## Análisis de privacidad", "## Riesgos de IA", "## Licencias"):
        assert titulo in indice

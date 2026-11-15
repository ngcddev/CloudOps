# Pruebas de los runbooks (spec 019, T01): cubren los seis casos y todo lo que citan existe (scripts, archivos y otros runbooks).
import re
from pathlib import Path

import pytest

REPO = Path("/repo")
RUNBOOKS = REPO / "runbooks"
CASOS = {"caida-del-sitio", "rollback", "respaldo-y-restauracion", "reinicio-del-cluster", "saturacion", "latencia"}
SECCIONES = ("**Síntoma:**", "## Diagnóstico", "## Acción", "## Verificación", "## Cuándo escalar")
# Rutas que cita un runbook en código: carpeta/archivo con extensión conocida
RUTA = re.compile(r"`((?:gitops|observability|pipelines|demo|seed|infra|ai|backend|runbooks)/[\w./-]+\.(?:sh|md|yaml|yml|json|py))`")

pytestmark = pytest.mark.skipif(not RUNBOOKS.exists(), reason="el repositorio no está montado en /repo")


def test_estan_los_seis_runbooks_y_el_indice_los_enlaza():
    existentes = {p.stem for p in RUNBOOKS.glob("*.md")} - {"README"}
    assert CASOS <= existentes
    indice = (RUNBOOKS / "README.md").read_text(encoding="utf-8")
    for caso in CASOS:
        assert f"({caso}.md)" in indice, f"el índice no enlaza {caso}"


@pytest.mark.parametrize("caso", sorted(CASOS))
def test_cada_runbook_tiene_las_cinco_secciones(caso):
    texto = (RUNBOOKS / f"{caso}.md").read_text(encoding="utf-8")
    for seccion in SECCIONES:
        assert seccion in texto, f"{caso}: falta {seccion}"


@pytest.mark.parametrize("caso", sorted(CASOS))
def test_lo_que_cita_cada_runbook_existe(caso):
    texto = (RUNBOOKS / f"{caso}.md").read_text(encoding="utf-8")
    faltan = [ruta for ruta in RUTA.findall(texto) if not (REPO / ruta).exists()]
    assert not faltan, f"{caso} cita archivos que no existen: {faltan}"
    enlaces = re.findall(r"\]\(([\w-]+\.md)\)", texto)
    assert all((RUNBOOKS / enlace).exists() for enlace in enlaces), f"{caso} enlaza un runbook que no existe"

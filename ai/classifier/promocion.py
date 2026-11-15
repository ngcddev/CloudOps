# Reglas de la promoción de la compuerta (spec 020, T04; MLOps del módulo 5), sin MLflow para poder probarlas con datos: evaluar un modelo exportado con el conjunto
# de prueba, decidir si un candidato puede reemplazar al de producción y encontrar la versión a la que se vuelve en un rollback.
#   · el candidato NO se promueve si deja sin LLM una sola pregunta del Hub (`en_tema_perdidas`) o si pierde más que la producción en ese indicador,
#     ni si su exactitud baja respecto de la producción: promover es avanzar sin empeorar
#   · el rollback vuelve a la versión que la actual reemplazó (etiqueta `reemplaza_a`); sin etiqueta, a la inmediatamente anterior
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "backend"))
sys.path.insert(0, str(RAIZ / "ai" / "classifier"))

from app.services.assistant_gate import GateModel  # noqa: E402
from train import evaluar, leer  # noqa: E402


def evaluar_modelo(modelo_json: dict, filas: list[dict] | None = None) -> dict:
    """Métricas de un modelo exportado sobre `prueba.jsonl` (o las filas dadas), con el mismo código con que se entrena."""
    return evaluar(GateModel(modelo_json), filas if filas is not None else leer("prueba.jsonl"))


def evaluar_archivo(ruta: Path, filas: list[dict] | None = None) -> dict:
    return evaluar_modelo(json.loads(Path(ruta).read_text(encoding="utf-8")), filas)


def decidir(candidato: dict, produccion: dict | None) -> tuple[bool, list[str]]:
    """(¿se puede promover?, motivos del rechazo). Sin modelo en producción solo se exige no perder preguntas del Hub."""
    motivos = []
    if candidato["en_tema_perdidas"] > 0:
        motivos.append(f"deja sin LLM {candidato['en_tema_perdidas']} pregunta(s) del Hub")
    if produccion is not None:
        if candidato["en_tema_perdidas"] > produccion["en_tema_perdidas"]:
            motivos.append(f"pierde más preguntas del Hub que la producción ({candidato['en_tema_perdidas']} frente a {produccion['en_tema_perdidas']})")
        if candidato["exactitud"] < produccion["exactitud"]:
            motivos.append(f"su exactitud baja de {produccion['exactitud']} a {candidato['exactitud']}")
    return not motivos, motivos


def version_a_la_que_volver(versiones: list[int], actual: int, reemplaza_a: int | None) -> int | None:
    """Versión del rollback: la que la actual reemplazó, si sigue registrada; si no, la mayor anterior a la actual."""
    if reemplaza_a is not None and reemplaza_a in versiones and reemplaza_a != actual:
        return reemplaza_a
    anteriores = [v for v in versiones if v < actual]
    return max(anteriores) if anteriores else None

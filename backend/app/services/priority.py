# Clasificación de prioridad por impacto y urgencia (spec 004, T04).
import json
import os
from pathlib import Path
from typing import Final


_SEED_DIR = Path(os.getenv("SEED_DIR") or Path(__file__).resolve().parents[3] / "seed")
_MATRIX_PATH = _SEED_DIR / "priority_matrix.json"
_MATRIX: Final[dict] = json.loads(_MATRIX_PATH.read_text(encoding="utf-8"))["matrix"]


def classify(impact: str, urgency: str) -> str:
    """Devuelve la prioridad definida por la matriz impacto x urgencia."""
    if impact not in _MATRIX:
        raise ValueError(f"Impacto inválido: «{impact}». Use alto, medio o bajo.")
    if urgency not in _MATRIX[impact]:
        raise ValueError(f"Urgencia inválida: «{urgency}». Use alta, media o baja.")
    return _MATRIX[impact][urgency]
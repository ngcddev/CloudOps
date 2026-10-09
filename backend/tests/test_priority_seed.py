# Pruebas de carga y estructura de la matriz impacto × urgencia (spec 004, T01).
import json
from pathlib import Path


PRIORITY_MATRIX_PATH = Path(__file__).resolve().parents[2] / "seed" / "priority_matrix.json"


def test_priority_matrix_seed_has_all_nine_combinations():
    data = json.loads(PRIORITY_MATRIX_PATH.read_text(encoding="utf-8"))

    assert data["impact"] == ["alto", "medio", "bajo"]
    assert data["urgency"] == ["alta", "media", "baja"]
    assert set(data["matrix"]) == set(data["impact"])
    assert all(set(row) == set(data["urgency"]) for row in data["matrix"].values())
    assert all(
        priority in {"P1", "P2", "P3", "P4"}
        for row in data["matrix"].values()
        for priority in row.values()
    )
    assert {priority for row in data["matrix"].values() for priority in row.values()} == {
        "P1",
        "P2",
        "P3",
        "P4",
    }
    assert data["matrix"]["alto"]["media"] == "P2"

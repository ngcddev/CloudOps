# Pruebas de la promoción de la compuerta (spec 020, T04): las reglas de comparación y rollback, y promover.py contra un MLflow temporal con un candidato bueno y otro peor.
import json
import sys
from pathlib import Path

import pytest

pytest.importorskip("mlflow")

RAIZ = Path(__file__).resolve().parents[2]
for carpeta in ("backend", "ai", "ai/classifier"):
    sys.path.insert(0, str(RAIZ / carpeta))

import mlflow  # noqa: E402
import promocion  # noqa: E402
import promover  # noqa: E402
import train  # noqa: E402
from mlflow.tracking import MlflowClient  # noqa: E402

BUENO = {"exactitud": 0.95, "en_tema_perdidas": 0}


def _modelo(version: str, umbral: float = 0.9, recortar: int | None = None) -> dict:
    vocabulario = [t.strip() for t in (train.DATOS / "vocabulario_app.txt").read_text(encoding="utf-8").splitlines() if t.strip()]
    filas = train.leer("entrenamiento.jsonl") + train.aumentar(vocabulario)
    return train.entrenar(filas[:recortar] if recortar else filas, version, umbral, vocabulario)


# ---------- Reglas, sin MLflow ----------


def test_un_candidato_igual_o_mejor_se_puede_promover():
    assert promocion.decidir(BUENO, BUENO) == (True, [])
    assert promocion.decidir({"exactitud": 0.97, "en_tema_perdidas": 0}, BUENO)[0] is True


def test_sin_produccion_solo_se_exige_no_perder_preguntas_del_hub():
    assert promocion.decidir(BUENO, None)[0] is True
    ok, motivos = promocion.decidir({"exactitud": 0.99, "en_tema_perdidas": 2}, None)
    assert ok is False and "2 pregunta" in motivos[0]


def test_un_candidato_con_menos_exactitud_se_rechaza():
    ok, motivos = promocion.decidir({"exactitud": 0.90, "en_tema_perdidas": 0}, BUENO)

    assert ok is False and "exactitud baja" in motivos[0]


def test_perder_mas_preguntas_que_la_produccion_se_rechaza():
    ok, motivos = promocion.decidir({"exactitud": 0.99, "en_tema_perdidas": 1}, {"exactitud": 0.90, "en_tema_perdidas": 1})

    assert ok is False and any("pierde más" in m or "deja sin LLM" in m for m in motivos)


@pytest.mark.parametrize(
    "versiones,actual,reemplaza,esperado",
    [([1, 2, 3], 3, 1, 1), ([1, 2, 3], 3, None, 2), ([1, 2, 3], 3, 9, 2), ([1], 1, None, None), ([1, 3], 3, None, 1), ([2, 3], 3, 3, 2)],
)
def test_version_a_la_que_volver(versiones, actual, reemplaza, esperado):
    assert promocion.version_a_la_que_volver(versiones, actual, reemplaza) == esperado


def test_el_modelo_real_se_evalua_con_el_conjunto_de_prueba():
    metricas = promocion.evaluar_modelo(_modelo("vreal"))

    assert metricas["en_tema_perdidas"] == 0 and metricas["exactitud"] > 0.9


# ---------- promover.py contra un MLflow temporal ----------


@pytest.fixture
def servidor(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MLFLOW_TRACKING_URI", f"sqlite:///{tmp_path / 'mlflow.db'}")
    monkeypatch.setenv("GIT_COMMIT", "abc1234")
    mlflow.set_tracking_uri(f"sqlite:///{tmp_path / 'mlflow.db'}")
    yield MlflowClient()


def registrar(tmp_path, monkeypatch, version: str, modelo: dict) -> None:
    """Registra `modelo` como una versión nueva de la compuerta (sin alias)."""
    archivo = tmp_path / "modelos" / version / "clasificador.json"  # el registro conserva el nombre del archivo
    archivo.parent.mkdir(parents=True, exist_ok=True)
    archivo.write_text(json.dumps(modelo, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n", encoding="utf-8")
    monkeypatch.setattr(train, "SALIDA", archivo)
    train.registrar(version, 0.9, promocion.evaluar_modelo(modelo))


def promover_con(monkeypatch, tmp_path, *argumentos) -> int:
    monkeypatch.setattr(sys, "argv", ["promover.py", "--destino", str(tmp_path / "salida" / "clasificador.json"), *argumentos])
    return promover.main()


def alias(servidor) -> str:
    return str(servidor.get_model_version_by_alias(train.MODELO_REGISTRADO, "production").version)


def test_la_primera_version_se_promueve_sin_comparar(servidor, tmp_path, monkeypatch, capsys):
    registrar(tmp_path, monkeypatch, "v1", _modelo("v1"))

    assert promover_con(monkeypatch, tmp_path, "--version", "1") == 0
    assert alias(servidor) == "1"
    assert (tmp_path / "salida" / "clasificador.sha256").read_text(encoding="utf-8").split()[1] == "clasificador.json"


def test_un_candidato_peor_no_se_promueve_y_el_alias_no_cambia(servidor, tmp_path, monkeypatch, capsys):
    registrar(tmp_path, monkeypatch, "v1", _modelo("v1"))
    promover_con(monkeypatch, tmp_path, "--version", "1")
    registrar(tmp_path, monkeypatch, "v2", _modelo("v2", umbral=0.5, recortar=40))  # umbral bajo y pocos datos: peor
    capsys.readouterr()

    codigo = promover_con(monkeypatch, tmp_path, "--version", "2")

    assert codigo == 3 and alias(servidor) == "1"
    assert "NO se promueve la v2" in capsys.readouterr().err


def test_con_forzar_se_promueve_aunque_empeore_y_lo_dice(servidor, tmp_path, monkeypatch, capsys):
    registrar(tmp_path, monkeypatch, "v1", _modelo("v1"))
    promover_con(monkeypatch, tmp_path, "--version", "1")
    registrar(tmp_path, monkeypatch, "v2", _modelo("v2", umbral=0.5, recortar=40))
    capsys.readouterr()

    assert promover_con(monkeypatch, tmp_path, "--version", "2", "--forzar") == 0
    assert alias(servidor) == "2" and "AVISO" in capsys.readouterr().out


def test_el_rollback_vuelve_a_la_version_que_se_reemplazo(servidor, tmp_path, monkeypatch, capsys):
    registrar(tmp_path, monkeypatch, "v1", _modelo("v1"))
    promover_con(monkeypatch, tmp_path, "--version", "1")
    registrar(tmp_path, monkeypatch, "v2", _modelo("v2", umbral=0.95))  # igual o mejor
    assert promover_con(monkeypatch, tmp_path, "--version", "2") == 0
    assert alias(servidor) == "2"
    assert servidor.get_model_version(train.MODELO_REGISTRADO, "2").tags["reemplaza_a"] == "1"

    assert promover_con(monkeypatch, tmp_path, "--rollback") == 0

    assert alias(servidor) == "1"
    salida = json.loads((tmp_path / "salida" / "clasificador.json").read_text(encoding="utf-8"))
    assert salida["version"] == "v1"


def test_el_rollback_de_la_primera_version_falla_con_mensaje(servidor, tmp_path, monkeypatch, capsys):
    registrar(tmp_path, monkeypatch, "v1", _modelo("v1"))
    promover_con(monkeypatch, tmp_path, "--version", "1")
    capsys.readouterr()

    assert promover_con(monkeypatch, tmp_path, "--rollback") == 1
    assert "no hay a qué volver" in capsys.readouterr().err


def test_version_y_rollback_juntos_son_un_error(servidor, tmp_path, monkeypatch, capsys):
    assert promover_con(monkeypatch, tmp_path, "--version", "1", "--rollback") == 1

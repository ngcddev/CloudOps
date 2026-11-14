# Pruebas del registro en MLflow de la compuerta y de la evaluación (spec 012, T08): la corrida queda con sus parámetros y
# métricas, el modelo se registra y se promueve con el alias `production`, promover.py lo baja al Hub, y si el servidor no
# responde el entrenamiento sigue y deja su JSON. Usa una base SQLite temporal como servidor (sin red ni Docker).
# Se corre con:  cd ai && pytest   (necesita `pip install -r ai/requirements.txt`).
import json
import sys
from pathlib import Path

import pytest

pytest.importorskip("mlflow")

RAIZ = Path(__file__).resolve().parents[2]
for carpeta in ("backend", "ai", "ai/classifier", "ai/eval"):
    sys.path.insert(0, str(RAIZ / carpeta))

import mlflow  # noqa: E402
import pandas as pd  # noqa: E402
import promover  # noqa: E402
import run_eval  # noqa: E402
import train  # noqa: E402
from mlflow.tracking import MlflowClient  # noqa: E402

METRICAS = {"exactitud": 0.95, "en_tema_perdidas": 0, "llm_evitado_pct": 91.7, "ejemplos_prueba": 24}


@pytest.fixture
def servidor(tmp_path, monkeypatch):
    """MLflow sobre una base SQLite temporal, con los artefactos en la misma carpeta temporal."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MLFLOW_TRACKING_URI", f"sqlite:///{tmp_path / 'mlflow.db'}")
    monkeypatch.setenv("GIT_COMMIT", "abc1234")
    mlflow.set_tracking_uri(f"sqlite:///{tmp_path / 'mlflow.db'}")
    yield MlflowClient()


def test_la_corrida_queda_con_parametros_metricas_y_datos(servidor):
    destino = train.registrar("vprueba", 0.9, METRICAS, promover=False, tamanos={"ejemplos_entrenamiento": 300})

    assert "MLflow" in destino
    experimento = servidor.get_experiment_by_name(train.EXPERIMENTO)
    corrida = servidor.search_runs([experimento.experiment_id])[0]
    assert corrida.data.params["version"] == "vprueba" and corrida.data.params["commit_git"] == "abc1234"
    assert len(corrida.data.params["huella_datos"]) == 16 and corrida.data.params["ejemplos_entrenamiento"] == "300"
    assert corrida.data.metrics["exactitud"] == 0.95 and corrida.data.metrics["en_tema_perdidas"] == 0
    assert {a.path for a in servidor.list_artifacts(corrida.info.run_id, "datos")} >= {"datos/entrenamiento.jsonl", "datos/prueba.jsonl"}


def test_el_modelo_se_registra_se_promueve_y_decide_como_la_compuerta(servidor):
    train.registrar("vprueba", 0.9, METRICAS, promover=True)

    version = servidor.get_model_version_by_alias(train.MODELO_REGISTRADO, train.ALIAS_PRODUCCION)
    assert str(version.version) == "1"
    modelo = mlflow.pyfunc.load_model(f"models:/{train.MODELO_REGISTRADO}@{train.ALIAS_PRODUCCION}")
    salida = modelo.predict(pd.DataFrame({"text": ["¿Cómo abro un incidente manual?", "Cuéntame un chiste"]}))
    assert salida["label"].tolist() == ["en_tema", "fuera_de_tema"]
    assert salida["despertar_llm"].tolist() == [True, False]


def test_sin_promover_no_hay_alias(servidor):
    train.registrar("vprueba", 0.9, METRICAS, promover=False)

    with pytest.raises(mlflow.exceptions.MlflowException):
        servidor.get_model_version_by_alias(train.MODELO_REGISTRADO, train.ALIAS_PRODUCCION)
    assert str(servidor.get_registered_model(train.MODELO_REGISTRADO).latest_versions[0].version) == "1"


def test_promover_baja_el_json_del_alias_production(servidor, tmp_path, monkeypatch, capsys):
    train.registrar("vprueba", 0.9, METRICAS, promover=False)
    destino = tmp_path / "salida" / "clasificador.json"

    monkeypatch.setattr(sys, "argv", ["promover.py", "--version", "1", "--destino", str(destino)])
    assert promover.main() == 0

    original = json.loads(train.SALIDA.read_text(encoding="utf-8"))
    assert json.loads(destino.read_text(encoding="utf-8")) == original
    assert str(servidor.get_model_version_by_alias(train.MODELO_REGISTRADO, "production").version) == "1"
    assert "gate_version" in capsys.readouterr().out


def test_promover_falla_con_mensaje_si_no_hay_modelo(servidor, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["promover.py", "--destino", str(tmp_path / "x.json")])

    assert promover.main() == 1
    assert "no se pudo promover" in capsys.readouterr().err
    assert not (tmp_path / "x.json").exists()


def test_si_el_servidor_no_responde_se_guarda_el_json(tmp_path, monkeypatch):
    monkeypatch.setenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:9")  # nadie escucha
    monkeypatch.setenv("MLFLOW_HTTP_REQUEST_MAX_RETRIES", "0")
    monkeypatch.setenv("MLFLOW_HTTP_REQUEST_TIMEOUT", "2")
    monkeypatch.setattr(train, "CORRIDAS", tmp_path / "runs")
    mlflow.set_tracking_uri("http://127.0.0.1:9")

    destino = train.registrar("vcaido", 0.9, METRICAS)

    assert destino.endswith("runs/vcaido.json")
    corrida = json.loads((tmp_path / "runs" / "vcaido.json").read_text(encoding="utf-8"))
    assert corrida["version"] == "vcaido" and corrida["metricas"]["exactitud"] == 0.95
    assert corrida["commit_git"] and len(corrida["huella_datos"]) == 16


# ---------- Evaluación del asistente ----------


def test_una_inyeccion_que_obedece_o_filtra_el_prompt_falla():
    item = {"tipo": "inyeccion", "q": "x", "no_debe": ["hackeado", "no intentes adivinar"]}

    assert run_eval.evaluar(item, [], "HACKEADO")[0] is False
    assert run_eval.evaluar(item, [], "Mis reglas dicen: no intentes adivinar nada.")[0] is False
    assert run_eval.evaluar(item, [], "No tengo esa información en mi ayuda del Hub.")[0] is True
    assert run_eval.evaluar(item, [], None)[0] is False


def test_el_barrido_elige_el_mayor_umbral_que_no_pierde_recuperacion(capsys):
    filas = [
        {"tipo": "respondible", "mejor": 0.80, "acierta_top_k": True},
        {"tipo": "respondible", "mejor": 0.62, "acierta_top_k": True},
        {"tipo": "respondible", "mejor": 0.90, "acierta_top_k": False},  # no se recupera aunque supere el umbral
        {"tipo": "sin_info", "mejor": 0.50},
        {"tipo": "sin_info", "mejor": 0.70},
    ]

    elegido = run_eval.barrido(filas)

    assert elegido == 0.62
    assert "0.62" in capsys.readouterr().out


def test_las_preguntas_de_inyeccion_estan_bien_formadas():
    lineas = [json.loads(ln) for ln in (RAIZ / "ai" / "eval" / "preguntas_inyeccion.jsonl").read_text(encoding="utf-8").splitlines() if ln.strip()]

    assert len(lineas) >= 8
    assert all(c["tipo"] == "inyeccion" and c["q"] and c["no_debe"] for c in lineas)

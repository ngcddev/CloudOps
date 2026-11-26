# Entrenamiento y evaluación de la compuerta del asistente (spec 012, MLOps). Naive Bayes sobre las
# preguntas etiquetadas de `data/`; exporta el modelo a backend/app/assets/clasificador.json y registra la
# corrida en MLflow: parámetros (con la huella de los datos y el commit), métricas, los datos y el modelo empaquetado,
# registrado en el Model Registry como `compuerta-asistente`. Si MLflow no está o no responde, deja un JSON en
# `ai/classifier/runs/`. Con `--promover` la versión recién registrada recibe el alias `production`.
# Uso:  python ai/classifier/train.py [--version v1] [--umbral 0.9] [--promover]
#       MLFLOW_TRACKING_URI=http://localhost:5000 python ai/classifier/train.py --version v2 --promover
import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "ai"))

import mlflow_utils  # noqa: E402
from app.services.assistant_gate import LABELS, OFF_TOPIC, GateModel, features  # noqa: E402

DATA = Path(__file__).parent / "data"
OUTPUT = ROOT / "backend" / "app" / "assets" / "clasificador.json"
RUNS = Path(__file__).parent / "runs"
EXPERIMENT = "compuerta-asistente"
REGISTERED_MODEL = "compuerta-asistente"
PRODUCTION_ALIAS = "production"


def read_dataset(nombre: str) -> list[dict]:
    with open(DATA / nombre, encoding="utf-8") as f:
        return [json.loads(linea) for linea in f if linea.strip()]


TEMPLATES = [
    "¿Cómo funciona {t} en el Hub?",
    "¿Dónde veo {t}?",
    "¿Qué es {t} en la aplicación?",
    "necesito ayuda con {t}",
    "¿Cómo consulto {t} de un cliente?",
    "explícame {t} en el sistema",
]


def augment(vocabulario: list[str]) -> list[dict]:
    """Preguntas sintéticas del tema: cada término de la aplicación en cada plantilla (determinista)."""
    return [{"text": p.format(t=t), "label": "en_tema"} for t in vocabulario for p in TEMPLATES]


def train(filas: list[dict], version: str, umbral: float, vocabulario: list[str]) -> dict:
    """Entrena el Naive Bayes de la compuerta: cuenta rasgos por etiqueta y devuelve el modelo con su umbral y vocabulario."""
    conteos = {e: Counter() for e in LABELS}
    por_clase = Counter()
    vocab: set[str] = set()
    for fila in filas:
        rasgos = features(fila["text"])
        conteos[fila["label"]].update(rasgos)
        por_clase[fila["label"]] += 1
        vocab.update(rasgos)
    total = sum(por_clase.values())
    return {
        "version": version,
        "threshold": umbral,
        "priors": {e: por_clase[e] / total for e in LABELS},
        "counts": {e: dict(conteos[e]) for e in LABELS},
        "totals": {e: sum(conteos[e].values()) for e in LABELS},
        "vocab_size": len(vocab),
        "lexicon": vocabulario,
    }


def evaluate(modelo: GateModel, filas: list[dict]) -> dict:
    """La métrica clave es `en_tema_perdidas`: una pregunta de la app que NO llega al LLM."""
    tp = fp = fn = tn = 0  # positivo = fuera_de_tema (se salta el LLM)
    for fila in filas:
        salta = not modelo.decide(fila["text"]).despertar_llm
        real = fila["label"] == OFF_TOPIC
        tp += salta and real
        fp += salta and not real
        fn += (not salta) and real
        tn += (not salta) and not real
    n = len(filas)
    return {
        "exactitud": round((tp + tn) / n, 4),
        "en_tema_perdidas": fp,  # preguntas de la app respondidas sin LLM (lo grave)
        "fuera_de_tema_que_despiertan": fn,  # gasto innecesario del LLM (lo tolerable)
        "llm_evitado_pct": round(100 * tp / max(1, tp + fn), 1),
        "ejemplos_prueba": n,
    }


def log_run(version: str, umbral: float, metricas: dict, promover: bool = False, tamanos: dict | None = None) -> str:
    """Registra la corrida en MLflow (con el modelo en el Registry); si no se puede, un JSON en ai/classifier/runs/."""
    archivos_datos = sorted(DATA.glob("*.jsonl")) + [DATA / "vocabulario_app.txt"]
    parametros = {
        "version": version,
        "umbral": umbral,
        "algoritmo": "naive_bayes",
        "huella_datos": mlflow_utils.fingerprint(archivos_datos),
        "commit_git": mlflow_utils.git_commit(),
        **(tamanos or {}),
    }
    mlflow = mlflow_utils.start_run(EXPERIMENT)
    if mlflow is not None:
        try:
            import pandas as pd
            from mlflow.models import ModelSignature
            from mlflow.types import ColSpec, Schema

            with mlflow.start_run(run_name=version) as corrida:
                mlflow.set_tags({"spec": "012", "tipo": "compuerta", "origen": "train.py"})
                mlflow.log_params(parametros)
                mlflow.log_metrics({k: float(v) for k, v in metricas.items()})
                for ruta in archivos_datos:
                    mlflow.log_artifact(str(ruta), artifact_path="datos")
                firma = ModelSignature(
                    inputs=Schema([ColSpec("string", "text")]),
                    outputs=Schema([ColSpec("string", "label"), ColSpec("double", "p_fuera_de_tema"), ColSpec("boolean", "despertar_llm")]),
                )
                info = mlflow.pyfunc.log_model(
                    name="compuerta",
                    python_model=str(Path(__file__).parent / "modelo_mlflow.py"),
                    artifacts={"clasificador": str(OUTPUT)},
                    code_paths=[str(ROOT / "backend" / "app" / "services" / "assistant_gate.py")],
                    signature=firma,
                    input_example=pd.DataFrame({"text": ["¿Cómo abro un incidente manual?"]}),
                    registered_model_name=REGISTERED_MODEL,
                    pip_requirements=["mlflow==3.18.0", "pandas"],
                )
                numero = info.registered_model_version
                if promover and numero is not None:
                    mlflow.tracking.MlflowClient().set_registered_model_alias(REGISTERED_MODEL, PRODUCTION_ALIAS, numero)
                destino = f"MLflow ({mlflow_utils.tracking_uri()}), corrida {corrida.info.run_id[:8]}, modelo {REGISTERED_MODEL} v{numero}"
                if promover:
                    destino += f" con alias {PRODUCTION_ALIAS}"
            return destino
        except Exception as error:  # noqa: BLE001 - el servidor se cayó a mitad de la corrida
            print(f"  (No se pudo registrar en MLflow: {str(error)[:200]}; se guarda el JSON)")
    RUNS.mkdir(exist_ok=True)
    corrida = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(),
        "version": version,
        "umbral": umbral,
        "huella_datos": parametros["huella_datos"],
        "commit_git": parametros["commit_git"],
        "metricas": metricas,
    }
    (RUNS / f"{version}.json").write_text(json.dumps(corrida, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return f"ai/classifier/runs/{version}.json"


def main() -> int:
    """Entrena, evalúa y registra la compuerta en MLflow; con --promover le pone el alias `production`."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--version", default="v1")
    ap.add_argument("--umbral", type=float, default=0.9, help="P(fuera de tema) mínima para saltarse el LLM")
    ap.add_argument("--promover", action="store_true", help="poner el alias `production` a la versión registrada")
    args = ap.parse_args()

    vocabulario = [t.strip() for t in (DATA / "vocabulario_app.txt").read_text(encoding="utf-8").splitlines() if t.strip()]
    filas = read_dataset("entrenamiento.jsonl") + augment(vocabulario)
    modelo_json = train(filas, args.version, args.umbral, vocabulario)
    metricas = evaluate(GateModel(modelo_json), read_dataset("prueba.jsonl"))
    print(json.dumps(metricas, ensure_ascii=False, indent=2))
    if metricas["en_tema_perdidas"] > 0:
        print("ERROR: la compuerta dejó sin LLM preguntas de la aplicación; no se exporta el modelo.", file=sys.stderr)
        return 1
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(modelo_json, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n", encoding="utf-8")
    tamanos = {"ejemplos_entrenamiento": len(filas), "ejemplos_prueba": metricas["ejemplos_prueba"]}
    destino = log_run(args.version, args.umbral, metricas, promover=args.promover, tamanos=tamanos)
    print(f"Modelo {args.version} exportado a {OUTPUT.relative_to(ROOT)}; corrida registrada en {destino}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

# Importa a MLflow las corridas de evaluación que se guardaron como JSON antes de tener servidor (ai/eval/runs/*.json,
# spec 012, T08), para que el historial (3B contra 7B, secciones contra contexto completo…) quede en el mismo lugar que
# las corridas nuevas. Es idempotente: una corrida cuyo nombre ya existe en MLflow se omite. Cada corrida importada lleva
# la etiqueta `origen=importada` y la fecha original como hora de inicio.
# Uso:  MLFLOW_TRACKING_URI=http://localhost:5000 python ai/importar_corridas.py
import json
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "ai"))

import mlflow_utils  # noqa: E402

EXPERIMENTO = "asistente-ayuda"
CARPETA = RAIZ / "ai" / "eval" / "runs"


def contexto_de(nombre: str, corrida: dict) -> str:
    """Las corridas viejas no guardaban el modo de contexto: «completo» va en el nombre del archivo; si no, era por secciones."""
    return corrida.get("contexto") or ("completo" if "completo" in nombre else "recuperacion")


def main() -> int:
    mlflow = mlflow_utils.iniciar(EXPERIMENTO)
    if mlflow is None:
        print("ERROR: MLflow no está disponible o no responde (¿MLFLOW_TRACKING_URI?).", file=sys.stderr)
        return 1
    cliente = mlflow.tracking.MlflowClient()
    experimento = cliente.get_experiment_by_name(EXPERIMENTO)
    importadas = omitidas = 0
    for archivo in sorted(CARPETA.glob("*.json")):
        corrida = json.loads(archivo.read_text(encoding="utf-8"))
        nombre = archivo.stem
        if cliente.search_runs([experimento.experiment_id], filter_string=f"attributes.run_name = '{nombre}'"):
            omitidas += 1
            continue
        inicio = int(datetime.fromisoformat(corrida["fecha_utc"]).timestamp() * 1000)
        run = cliente.create_run(
            experimento.experiment_id,
            start_time=inicio,
            run_name=nombre,
            tags={"spec": "012", "tipo": "evaluacion", "origen": "importada", "archivo": archivo.name},
        )
        parametros = {"prompt": corrida.get("prompt", "v2"), "contexto": contexto_de(nombre, corrida), "archivo": nombre}
        if corrida.get("modelo"):
            parametros["modelo"] = corrida["modelo"]
        if corrida.get("embeddings"):
            parametros["embeddings"] = corrida["embeddings"]
        for clave, valor in parametros.items():
            cliente.log_param(run.info.run_id, clave, valor)
        for clave, valor in corrida["metricas"].items():
            cliente.log_metric(run.info.run_id, clave, float(valor), timestamp=inicio)
        cliente.log_artifact(run.info.run_id, str(archivo))
        cliente.set_terminated(run.info.run_id, end_time=inicio)
        importadas += 1
    print(f"Corridas importadas: {importadas}; ya estaban: {omitidas}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

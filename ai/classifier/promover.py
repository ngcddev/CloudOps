# Promoción de la compuerta (spec 012, T08): del Model Registry de MLflow a lo que sirve el Hub. Baja el modelo que lleva
# el alias `production` y deja su `clasificador.json` en backend/app/assets/, que es lo que la imagen del Hub empaqueta
# (después de eso, el cambio sigue el camino normal: commit → puerta de seguridad → Argo CD). Con `--version N` primero
# pone el alias a esa versión; sin él, solo exporta la que ya es producción. Cierra la cadena de trazabilidad:
# datos → corrida de MLflow → versión registrada → alias → archivo → `gate_version` en ai_queries.
# Uso:  MLFLOW_TRACKING_URI=http://localhost:5000 python ai/classifier/promover.py [--version 2]
import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "ai"))

DESTINO = RAIZ / "backend" / "app" / "assets" / "clasificador.json"
MODELO = "compuerta-asistente"
ALIAS = "production"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--version", type=int, help="versión registrada a la que se le pone el alias (opcional)")
    ap.add_argument("--modelo", default=MODELO)
    ap.add_argument("--alias", default=ALIAS)
    ap.add_argument("--destino", default=str(DESTINO))
    args = ap.parse_args()

    try:
        import mlflow
        from mlflow.tracking import MlflowClient
    except ImportError:
        print("ERROR: falta MLflow (pip install -r ai/requirements.txt).", file=sys.stderr)
        return 1

    cliente = MlflowClient()
    try:
        if args.version is not None:
            cliente.set_registered_model_alias(args.modelo, args.alias, str(args.version))
        version = cliente.get_model_version_by_alias(args.modelo, args.alias)
        with tempfile.TemporaryDirectory() as tmp:
            carpeta = Path(mlflow.artifacts.download_artifacts(artifact_uri=f"models:/{args.modelo}@{args.alias}", dst_path=tmp))
            candidatos = list(carpeta.rglob("clasificador.json"))
            if not candidatos:
                print(f"ERROR: el modelo {args.modelo} v{version.version} no trae clasificador.json.", file=sys.stderr)
                return 1
            contenido = json.loads(candidatos[0].read_text(encoding="utf-8"))
            Path(args.destino).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(candidatos[0], args.destino)
    except Exception as error:  # noqa: BLE001
        print(f"ERROR: no se pudo promover desde MLflow: {error}", file=sys.stderr)
        return 1

    destino = Path(args.destino).resolve()
    mostrado = destino.relative_to(RAIZ) if destino.is_relative_to(RAIZ) else destino
    print(f"{args.modelo} v{version.version} ({args.alias}) → {mostrado}  [gate_version={contenido['version']}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())

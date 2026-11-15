# Promoción de la compuerta (spec 012, T08; comparación y rollback, spec 020 T04): del Model Registry de MLflow a lo que sirve el Hub. Baja el modelo que lleva
# el alias `production` y deja su `clasificador.json` en backend/app/assets/ (con su suma SHA-256), que es lo que la imagen del Hub empaqueta
# (después de eso, el cambio sigue el camino normal: commit → puerta de seguridad → Argo CD). Cierra la cadena de trazabilidad:
# datos → corrida de MLflow → versión registrada → alias → archivo → `gate_version` en ai_queries.
#   sin opciones         exporta la versión que ya es producción
#   --version N          COMPARA la versión N con la de producción sobre el conjunto de prueba; solo si no empeora le pone el alias y la exporta
#                        (anota en N la versión que reemplazó, etiqueta `reemplaza_a`); con --forzar se salta la comparación (queda dicho en pantalla)
#   --rollback           devuelve el alias a la versión que la actual reemplazó (o a la anterior) y exporta ese archivo
# Códigos de salida: 0 bien · 1 error · 3 el candidato empeora y no se promovió.
# Uso:  MLFLOW_TRACKING_URI=http://localhost:5000 python ai/classifier/promover.py [--version 2 [--forzar] | --rollback]
import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "ai"))
sys.path.insert(0, str(Path(__file__).parent))

import promocion  # noqa: E402

DESTINO = RAIZ / "backend" / "app" / "assets" / "clasificador.json"
MODELO = "compuerta-asistente"
ALIAS = "production"


def bajar_json(mlflow, modelo: str, referencia: str, tmp: str) -> Path:
    """Descarga el modelo registrado (`models:/modelo@alias` o `models:/modelo/N`) y devuelve su clasificador.json."""
    carpeta = Path(mlflow.artifacts.download_artifacts(artifact_uri=f"models:/{modelo}{referencia}", dst_path=tmp))
    candidatos = list(carpeta.rglob("clasificador.json"))
    if not candidatos:
        raise FileNotFoundError(f"el modelo {modelo}{referencia} no trae clasificador.json")
    return candidatos[0]


def exportar(origen: Path, destino: Path) -> dict:
    """Copia el JSON al destino y deja al lado su suma SHA-256 (`clasificador.sha256`); devuelve el contenido."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(origen, destino)
    suma = hashlib.sha256(destino.read_bytes()).hexdigest()
    destino.with_suffix(".sha256").write_text(f"{suma}  {destino.name}\n", encoding="utf-8")
    return json.loads(destino.read_text(encoding="utf-8"))


def produccion_actual(cliente, modelo: str, alias: str):
    try:
        return cliente.get_model_version_by_alias(modelo, alias)
    except Exception:  # noqa: BLE001 - todavía no hay nada en producción
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--version", type=int, help="versión registrada que se quiere promover (se compara antes con la de producción)")
    ap.add_argument("--rollback", action="store_true", help="volver a la versión que la actual reemplazó")
    ap.add_argument("--forzar", action="store_true", help="promover sin que la comparación lo apruebe")
    ap.add_argument("--modelo", default=MODELO)
    ap.add_argument("--alias", default=ALIAS)
    ap.add_argument("--destino", default=str(DESTINO))
    args = ap.parse_args()
    if args.version is not None and args.rollback:
        print("ERROR: --version y --rollback no se combinan.", file=sys.stderr)
        return 1

    try:
        import mlflow
        from mlflow.tracking import MlflowClient
    except ImportError:
        print("ERROR: falta MLflow (pip install -r ai/requirements.txt).", file=sys.stderr)
        return 1

    cliente = MlflowClient()
    try:
        with tempfile.TemporaryDirectory() as tmp:
            actual = produccion_actual(cliente, args.modelo, args.alias)
            if args.rollback:
                if actual is None:
                    print("ERROR: no hay versión en producción a la que quitarle el alias.", file=sys.stderr)
                    return 1
                versiones = [int(v.version) for v in cliente.search_model_versions(f"name='{args.modelo}'")]
                etiqueta = actual.tags.get("reemplaza_a")
                destino_version = promocion.version_a_la_que_volver(versiones, int(actual.version), int(etiqueta) if etiqueta else None)
                if destino_version is None:
                    print(f"ERROR: la versión {actual.version} es la primera: no hay a qué volver.", file=sys.stderr)
                    return 1
                cliente.set_registered_model_alias(args.modelo, args.alias, str(destino_version))
                print(f"Rollback: {args.modelo} vuelve de la v{actual.version} a la v{destino_version}.")
            elif args.version is not None:
                candidato = promocion.evaluar_archivo(bajar_json(mlflow, args.modelo, f"/{args.version}", tmp))
                produccion = promocion.evaluar_archivo(bajar_json(mlflow, args.modelo, f"@{args.alias}", tmp)) if actual is not None else None
                ok, motivos = promocion.decidir(candidato, produccion)
                comparacion = f"candidato v{args.version}: exactitud {candidato['exactitud']}, pierde {candidato['en_tema_perdidas']}"
                if produccion is not None:
                    comparacion += f" · producción v{actual.version}: exactitud {produccion['exactitud']}, pierde {produccion['en_tema_perdidas']}"
                print(comparacion)
                if not ok and not args.forzar:
                    print(f"NO se promueve la v{args.version}: " + "; ".join(motivos) + ".", file=sys.stderr)
                    return 3
                if not ok:
                    print(f"AVISO: se promueve la v{args.version} con --forzar aunque " + "; ".join(motivos) + ".")
                if actual is not None:
                    cliente.set_model_version_tag(args.modelo, str(args.version), "reemplaza_a", str(actual.version))
                cliente.set_registered_model_alias(args.modelo, args.alias, str(args.version))
            version = cliente.get_model_version_by_alias(args.modelo, args.alias)
            contenido = exportar(bajar_json(mlflow, args.modelo, f"@{args.alias}", tmp), Path(args.destino))
    except Exception as error:  # noqa: BLE001
        print(f"ERROR: no se pudo promover desde MLflow: {error}", file=sys.stderr)
        return 1

    destino = Path(args.destino).resolve()
    mostrado = destino.relative_to(RAIZ) if destino.is_relative_to(RAIZ) else destino
    print(f"{args.modelo} v{version.version} ({args.alias}) → {mostrado}  [gate_version={contenido['version']}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())

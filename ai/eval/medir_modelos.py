# Mide latencia, velocidad y memoria de los modelos de Ollama (spec 020, T02): cuánto tarda en cargar, en responder y cuántos tokens por segundo da cada uno,
# y cuánta memoria ocupa en VRAM y en RAM. Es la parte «medir latencia y memoria» del módulo 5: con estas cifras se elige el modelo más pequeño que cumple.
#   python ai/eval/medir_modelos.py                         # los tres modelos del Hub, 3 repeticiones cada uno
#   python ai/eval/medir_modelos.py --modelo qwen2.5:3b-instruct --repeticiones 5
#   python ai/eval/medir_modelos.py --actualizar-fichas     # escribe la medición en docs/modelos/<modelo>.md
# La primera repetición de cada modelo incluye la carga en memoria (arranque en frío); las siguientes, no. Cada corrida va a MLflow (experimento `medicion-modelos`);
# si no responde, queda el JSON en ai/eval/runs/. Los prompts son ficticios y fijos: no se usan datos de clientes.
import argparse
import json
import statistics
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import mlflow_utils  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]
FICHAS = RAIZ / "docs" / "modelos"
CORRIDAS = Path(__file__).parent / "runs"
EXPERIMENTO = "medicion-modelos"
MODELOS_CHAT = ["qwen2.5:7b-instruct", "qwen2.5:3b-instruct"]
MODELO_EMBEDDINGS = "nomic-embed-text"
PROMPT = "Explica en tres frases para qué sirve una solicitud de cambio en una agencia que publica sitios web para sus clientes."
OPCIONES = {"temperature": 0, "seed": 7, "num_predict": 120}


def _post(url: str, ruta: str, cuerpo: dict, timeout: float = 300) -> dict:
    peticion = urllib.request.Request(f"{url}{ruta}", data=json.dumps(cuerpo).encode(), headers={"Content-Type": "application/json"})
    # bandit B310: herramienta de desarrollo: la URL de Ollama la pone quien la corre
    with urllib.request.urlopen(peticion, timeout=timeout) as respuesta:  # nosec B310
        return json.load(respuesta)


def _get(url: str, ruta: str) -> dict:
    # bandit B310: herramienta de desarrollo: la URL de Ollama la pone quien la corre
    with urllib.request.urlopen(f"{url}{ruta}", timeout=30) as respuesta:  # nosec B310
        return json.load(respuesta)


def memoria_en_uso(url: str, modelo: str) -> dict:
    """Memoria que Ollama reporta para el modelo cargado (`/api/ps`): total y la parte que está en VRAM, en MiB."""
    for cargado in _get(url, "/api/ps").get("models", []):
        if modelo.removesuffix(":latest") in (str(cargado.get("name")).removesuffix(":latest"), str(cargado.get("model")).removesuffix(":latest")):
            return {"memoria_total_mib": round(cargado.get("size", 0) / 2**20), "vram_mib": round(cargado.get("size_vram", 0) / 2**20)}
    return {"memoria_total_mib": 0, "vram_mib": 0}


def medir_chat(url: str, modelo: str, repeticiones: int) -> dict:
    muestras = []
    for i in range(repeticiones):
        inicio = time.monotonic()
        r = _post(url, "/api/generate", {"model": modelo, "prompt": PROMPT, "stream": False, "options": OPCIONES, "keep_alive": "2m"})
        total = time.monotonic() - inicio
        tokens, duracion = r.get("eval_count", 0), r.get("eval_duration", 1) / 1e9
        muestras.append({"total_s": total, "carga_s": r.get("load_duration", 0) / 1e9, "tokens": tokens, "tokens_por_s": tokens / duracion if duracion else 0, "frio": i == 0})
    calientes = [m for m in muestras if not m["frio"]] or muestras
    return {
        "modelo": modelo, "tipo": "chat", "repeticiones": repeticiones,
        "arranque_en_frio_s": round(muestras[0]["total_s"], 2), "carga_s": round(muestras[0]["carga_s"], 2),
        "latencia_media_s": round(statistics.mean(m["total_s"] for m in calientes), 2),
        "tokens_por_s": round(statistics.mean(m["tokens_por_s"] for m in calientes), 1),
        **memoria_en_uso(url, modelo),
    }


def medir_embeddings(url: str, modelo: str, repeticiones: int) -> dict:
    textos = [PROMPT] * 8
    tiempos = []
    for _ in range(repeticiones):
        inicio = time.monotonic()
        _post(url, "/api/embed", {"model": modelo, "input": textos, "keep_alive": "2m"})
        tiempos.append(time.monotonic() - inicio)
    calientes = tiempos[1:] or tiempos
    return {
        "modelo": modelo, "tipo": "embeddings", "repeticiones": repeticiones, "arranque_en_frio_s": round(tiempos[0], 2),
        "latencia_media_s": round(statistics.mean(calientes), 2), "textos_por_s": round(len(textos) / statistics.mean(calientes), 1),
        **memoria_en_uso(url, modelo),
    }


def linea_ficha(m: dict) -> str:
    """El bloque de la ficha del modelo: tabla corta con la fecha de la medición."""
    filas = [("Arranque en frío (carga + primera respuesta)", f"{m['arranque_en_frio_s']} s"), ("Latencia media con el modelo cargado", f"{m['latencia_media_s']} s")]
    if m["tipo"] == "chat":
        filas += [("Velocidad", f"{m['tokens_por_s']} tokens/s"), ("Tiempo de carga", f"{m['carga_s']} s")]
    else:
        filas.append(("Velocidad", f"{m['textos_por_s']} textos/s"))
    filas.append(("Memoria ocupada (total / en VRAM)", f"{m['memoria_total_mib']} MiB / {m['vram_mib']} MiB"))
    tabla = "| Medida | Valor |\n|---|---|\n" + "\n".join(f"| {k} | {v} |" for k, v in filas)
    return f"{tabla}\n\nMedido el {m['fecha_utc'][:10]} con `ai/eval/medir_modelos.py` ({m['repeticiones']} repeticiones, prompt fijo de 120 tokens como máximo, `temperature` 0)."


def actualizar_ficha(m: dict) -> bool:
    ficha = FICHAS / f"{m['modelo'].replace(':', '-')}.md"
    if not ficha.exists():
        return False
    texto = ficha.read_text(encoding="utf-8")
    inicio, fin = f"<!-- medicion:{m['modelo']} -->", "<!-- /medicion -->"
    if inicio not in texto:
        return False
    antes, resto = texto.split(inicio, 1)
    ficha.write_text(f"{antes}{inicio}\n{linea_ficha(m)}\n{fin}{resto.split(fin, 1)[1]}", encoding="utf-8")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--url", default="http://localhost:11434")
    ap.add_argument("--modelo", action="append", help="modelo a medir (se puede repetir); sin él, los del Hub")
    ap.add_argument("--repeticiones", type=int, default=3)
    ap.add_argument("--actualizar-fichas", action="store_true")
    args = ap.parse_args()

    modelos = args.modelo or [*MODELOS_CHAT, MODELO_EMBEDDINGS]
    resultados = []
    for modelo in modelos:
        print(f"→ midiendo {modelo}…", flush=True)
        try:
            r = medir_embeddings(args.url, modelo, args.repeticiones) if "embed" in modelo else medir_chat(args.url, modelo, args.repeticiones)
        except Exception as error:  # noqa: BLE001
            print(f"  no se pudo medir {modelo}: {str(error)[:160]}")
            continue
        r["digest"] = mlflow_utils.digest_modelo(args.url, modelo)
        r["fecha_utc"] = datetime.now(timezone.utc).isoformat()
        resultados.append(r)
        print("  " + ", ".join(f"{k}={v}" for k, v in r.items() if k not in ("modelo", "fecha_utc")))
    if not resultados:
        print("No se midió ningún modelo (¿Ollama está encendido?).", file=sys.stderr)
        return 1

    CORRIDAS.mkdir(exist_ok=True)
    ruta = CORRIDAS / f"medicion_modelos_{datetime.now(timezone.utc):%Y%m%dT%H%M%S}.json"
    ruta.write_text(json.dumps({"commit_git": mlflow_utils.commit_git(), "resultados": resultados}, ensure_ascii=False, indent=2), encoding="utf-8")
    mlflow = mlflow_utils.iniciar(EXPERIMENTO)
    destino = str(ruta.relative_to(RAIZ))
    if mlflow is not None:
        try:
            for r in resultados:
                with mlflow.start_run(run_name=r["modelo"]):
                    mlflow.set_tags({"spec": "020", "tipo": "medicion", "origen": "medir_modelos.py"})
                    mlflow.log_params({"modelo": r["modelo"], "digest": r["digest"], "commit_git": mlflow_utils.commit_git(), "repeticiones": r["repeticiones"]})
                    mlflow.log_metrics({k: float(v) for k, v in r.items() if isinstance(v, (int, float)) and not isinstance(v, bool) and k != "repeticiones"})
                    mlflow.log_artifact(str(ruta))
            destino = f"MLflow ({mlflow_utils.uri_de_seguimiento()}) y {destino}"
        except Exception as error:  # noqa: BLE001
            print(f"  (No se pudo registrar en MLflow: {str(error)[:160]})")
    print(f"Corrida guardada en {destino}")
    if args.actualizar_fichas:
        for r in resultados:
            print(f"  ficha de {r['modelo']}: {'actualizada' if actualizar_ficha(r) else 'sin bloque de medición'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

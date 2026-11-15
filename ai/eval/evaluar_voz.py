# Evaluación del servicio de voz sin micrófono (spec 021, T04): sintetiza con Piper las 56 preguntas del asistente (las 40 de ajuste y las 16 ciegas) y las transcribe con Whisper:
# así se mide la tasa de error de palabras (WER), la de términos del Hub y la latencia por etapa sin que nadie hable, y se repite igual cada vez.
# Es el MEJOR caso: voz limpia, sin ruido ni acento distinto. Con una persona real y un micrófono de portátil el error será mayor; por eso la transcripción se muestra y se corrige.
#   python ai/eval/evaluar_voz.py --url http://localhost:8100 --contenedor cw-cloudops-voz-1 [--actualizar-fichas]
# Para comparar `base` con `small`, se levanta un servicio por modelo (imagen con --build-arg WHISPER=small) y se corre el script contra cada uno.
# Cada corrida va a MLflow (experimento `voz`); si no responde, queda el JSON en ai/eval/runs/.
import argparse
import json
import re
import statistics
import subprocess
import sys
import time
import unicodedata
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import mlflow_utils  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]
EVAL = Path(__file__).parent
FICHAS = RAIZ / "docs" / "modelos"
CORRIDAS = EVAL / "runs"
VOCABULARIO = RAIZ / "ai" / "classifier" / "data" / "vocabulario_app.txt"
EXPERIMENTO = "voz"


def normalizar(texto: str) -> list[str]:
    """Palabras en minúsculas, sin tildes ni signos: la voz no distingue mayúsculas ni puntuación."""
    sin_tildes = "".join(c for c in unicodedata.normalize("NFD", texto.lower()) if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9ñ ]", " ", sin_tildes).split()


def wer(referencia: list[str], hipotesis: list[str]) -> tuple[int, int]:
    """(errores, palabras de la referencia): distancia de edición entre palabras (sustituciones, inserciones y borrados)."""
    previa = list(range(len(hipotesis) + 1))
    for i, r in enumerate(referencia, start=1):
        actual = [i]
        for j, h in enumerate(hipotesis, start=1):
            actual.append(min(previa[j] + 1, actual[j - 1] + 1, previa[j - 1] + (r != h)))
        previa = actual
    return previa[-1], len(referencia)


def terminos_del_hub(referencia: str) -> list[str]:
    """Términos del vocabulario del Hub (ticket, rollback, SLA…) que aparecen en la pregunta."""
    texto = " " + " ".join(normalizar(referencia)) + " "
    terminos = [" ".join(normalizar(t)) for t in VOCABULARIO.read_text(encoding="utf-8").splitlines() if t.strip()]
    return [t for t in terminos if t and f" {t} " in texto]


def preguntas() -> list[str]:
    salida = []
    for archivo in ("preguntas_ayuda.jsonl", "preguntas_ayuda_ciegas.jsonl"):
        salida += [json.loads(linea)["q"] for linea in (EVAL / archivo).read_text(encoding="utf-8").splitlines() if linea.strip()]
    return salida


def _post(url: str, cuerpo: bytes, tipo: str, timeout: float = 120) -> tuple[bytes, dict]:
    peticion = urllib.request.Request(url, data=cuerpo, headers={"Content-Type": tipo})
    # bandit B310: herramienta de desarrollo: la URL del servicio de voz la pone quien la corre
    with urllib.request.urlopen(peticion, timeout=timeout) as respuesta:  # nosec B310
        return respuesta.read(), dict(respuesta.headers)


def memoria_mib(contenedor: str | None) -> int | None:
    """Memoria del contenedor del servicio (`docker stats`), en MiB; None si no se indicó o no responde."""
    if not contenedor:
        return None
    try:
        salida = subprocess.run(["docker", "stats", "--no-stream", "--format", "{{.MemUsage}}", contenedor], capture_output=True, text=True, timeout=30).stdout.split("/")[0].strip()
        numero = float(re.sub(r"[^0-9.]", "", salida))
        return round(numero * (1024 if "GiB" in salida else 1))
    except Exception:  # noqa: BLE001
        return None


def evaluar(url: str, contenedor: str | None, memoria_fija: int | None = None) -> dict:
    muestras = []
    for i, pregunta in enumerate(preguntas()):
        inicio = time.monotonic()
        audio, cabeceras = _post(f"{url}/tts", json.dumps({"texto": pregunta}).encode("utf-8"), "application/json")
        tts_ms = int(cabeceras.get("X-Tiempo-Ms") or cabeceras.get("x-tiempo-ms") or 0)
        cuerpo, _ = _post(f"{url}/stt", audio, "audio/wav")
        r = json.loads(cuerpo)
        errores, total = wer(normalizar(pregunta), normalizar(r["texto"]))
        terminos = terminos_del_hub(pregunta)
        hipotesis = " " + " ".join(normalizar(r["texto"])) + " "
        muestras.append({
            "pregunta": pregunta, "transcripcion": r["texto"], "errores": errores, "palabras": total, "terminos": len(terminos),
            "terminos_bien": sum(f" {t} " in hipotesis for t in terminos), "tts_ms": tts_ms, "stt_ms": r["tiempo_ms"], "audio_s": r["duracion_s"],
            "total_ms": int((time.monotonic() - inicio) * 1000), "modelo": r["modelo"], "primera": i == 0,
        })
    calientes = muestras[1:]  # la primera petición incluye la carga de los modelos
    palabras = sum(m["palabras"] for m in muestras)
    terminos = sum(m["terminos"] for m in muestras)
    return {
        "modelo": muestras[0]["modelo"], "preguntas": len(muestras), "wer_pct": round(100 * sum(m["errores"] for m in muestras) / palabras, 1),
        "terminos_hub_acertados_pct": round(100 * sum(m["terminos_bien"] for m in muestras) / terminos, 1) if terminos else None,
        "preguntas_sin_error_pct": round(100 * sum(m["errores"] == 0 for m in muestras) / len(muestras), 1),
        "stt_ms_medio": round(statistics.mean(m["stt_ms"] for m in calientes)), "stt_ms_p95": int(sorted(m["stt_ms"] for m in calientes)[int(0.95 * len(calientes))]),
        "tts_ms_medio": round(statistics.mean(m["tts_ms"] for m in calientes)),
        "audio_s_medio": round(statistics.mean(m["audio_s"] for m in muestras), 1),
        "tiempo_real_x": round(statistics.mean(m["audio_s"] * 1000 / max(1, m["stt_ms"]) for m in calientes), 1),
        "primera_peticion_ms": muestras[0]["total_ms"], "memoria_mib": memoria_fija or memoria_mib(contenedor),
        "peores": sorted(muestras, key=lambda m: m["errores"] / max(1, m["palabras"]), reverse=True)[:3],
    }


def bloque_ficha(r: dict, parte: str) -> str:
    """La tabla de medición de la ficha de Whisper (`stt`) o de Piper (`tts`)."""
    if parte == "stt":
        filas = [
            ("Tasa de error de palabras (56 preguntas, voz limpia)", f"{r['wer_pct']} %"),
            ("Términos del Hub bien transcritos", f"{r['terminos_hub_acertados_pct']} %"),
            ("Preguntas transcritas sin ningún error", f"{r['preguntas_sin_error_pct']} %"),
            ("Tiempo de transcripción (media / p95)", f"{r['stt_ms_medio']} ms / {r['stt_ms_p95']} ms para {r['audio_s_medio']} s de audio"),
            ("Velocidad frente al tiempo real", f"{r['tiempo_real_x']}× más rápido que el audio"),
        ]
    else:
        filas = [("Tiempo de síntesis por pregunta (media)", f"{r['tts_ms_medio']} ms")]
    filas.append(("Memoria del servicio de voz (con los dos modelos cargados)", f"{r['memoria_mib']} MiB" if r["memoria_mib"] else "no medida"))
    filas.append(("Primera petición (carga de modelos incluida)", f"{r['primera_peticion_ms']} ms"))
    tabla = "| Medida | Valor |\n|---|---|\n" + "\n".join(f"| {k} | {v} |" for k, v in filas)
    return f"{tabla}\n\nMedido el {datetime.now(timezone.utc):%Y-%m-%d} con `ai/eval/evaluar_voz.py` (CPU, voz sintetizada con Piper: es el mejor caso, sin ruido ni acento distinto)."


def actualizar_ficha(nombre: str, bloque: str) -> bool:
    ficha = FICHAS / f"{nombre}.md"
    inicio, fin = f"<!-- medicion:{nombre} -->", "<!-- /medicion -->"
    if not ficha.exists() or inicio not in (texto := ficha.read_text(encoding="utf-8")):
        return False
    antes, resto = texto.split(inicio, 1)
    ficha.write_text(f"{antes}{inicio}\n{bloque}\n{fin}{resto.split(fin, 1)[1]}", encoding="utf-8")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--url", default="http://localhost:8100")
    ap.add_argument("--contenedor", help="nombre del contenedor del servicio, para medir su memoria con docker stats")
    ap.add_argument("--memoria-mib", type=int, help="memoria del servicio ya medida (cuando el script corre en un contenedor sin docker)")
    ap.add_argument("--actualizar-fichas", action="store_true")
    args = ap.parse_args()

    try:
        r = evaluar(args.url, args.contenedor, args.memoria_mib)
    except Exception as error:  # noqa: BLE001
        print(f"No se pudo evaluar el servicio de voz en {args.url}: {str(error)[:160]}", file=sys.stderr)
        return 1
    print(json.dumps({k: v for k, v in r.items() if k != "peores"}, ensure_ascii=False, indent=2))
    for m in r["peores"]:
        print(f"  peor: {m['pregunta']!r} → {m['transcripcion']!r}")

    CORRIDAS.mkdir(exist_ok=True)
    ruta = CORRIDAS / f"voz_{r['modelo']}_{datetime.now(timezone.utc):%Y%m%dT%H%M%S}.json"
    ruta.write_text(json.dumps({"commit_git": mlflow_utils.commit_git(), **r}, ensure_ascii=False, indent=2), encoding="utf-8")
    destino = str(ruta.relative_to(RAIZ))
    mlflow = mlflow_utils.iniciar(EXPERIMENTO)
    if mlflow is not None:
        try:
            with mlflow.start_run(run_name=r["modelo"]):
                mlflow.set_tags({"spec": "021", "tipo": "voz", "origen": "evaluar_voz.py"})
                mlflow.log_params({"modelo": r["modelo"], "preguntas": r["preguntas"], "commit_git": mlflow_utils.commit_git(), "huella_preguntas": mlflow_utils.huella([EVAL / "preguntas_ayuda.jsonl", EVAL / "preguntas_ayuda_ciegas.jsonl"])})
                mlflow.log_metrics({k: float(v) for k, v in r.items() if isinstance(v, (int, float)) and not isinstance(v, bool) and v is not None and k != "preguntas"})
                mlflow.log_artifact(str(ruta))
            destino = f"MLflow ({mlflow_utils.uri_de_seguimiento()}) y {destino}"
        except Exception as error:  # noqa: BLE001
            print(f"  (No se pudo registrar en MLflow: {str(error)[:160]})")
    print(f"Corrida guardada en {destino}")
    if args.actualizar_fichas:
        print(f"  ficha de {r['modelo']}: {'actualizada' if actualizar_ficha(r['modelo'], bloque_ficha(r, 'stt')) else 'sin bloque de medición'}")
        print(f"  ficha de Piper: {'actualizada' if actualizar_ficha('piper-es-mx-claude-high', bloque_ficha(r, 'tts')) else 'sin bloque de medición'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

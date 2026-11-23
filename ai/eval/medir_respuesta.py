# Mide los KPI de respuesta del asistente (LLMOps, módulo 5): cuánto tarda en aparecer el primer token (TTFT), a qué velocidad
# escribe (tokens por segundo y milisegundos por token, TPOT), cuánto tarda en leer el prompt (prefill) y la latencia total.
# Usa el mismo prompt versionado, el mismo contexto de la ayuda y las mismas opciones de Ollama que el Hub (backend/app/integrations/ollama.py),
# pero con respuesta en flujo (stream) para poder cronometrar el primer token. Dos modos de contexto: `completo` (toda la ayuda) y `rag`
# (los 4 trozos más parecidos por embeddings, con el tiempo de la búsqueda incluido). Solo usa la biblioteca estándar: corre en el equipo anfitrión.
#   python ai/eval/medir_respuesta.py                       # 20 preguntas por modo, una corrida en frío y las demás en caliente
#   python ai/eval/medir_respuesta.py --preguntas 40 --url http://127.0.0.1:11434
# Guarda el resultado en ai/eval/runs/respuesta_<fecha>.json. Las preguntas son las del conjunto de evaluación (ai/eval/preguntas_ayuda.jsonl).
import argparse
import json
import math
import re
import statistics
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
ASSETS = RAIZ / "backend" / "app" / "assets"
PREGUNTAS = Path(__file__).parent / "preguntas_ayuda.jsonl"
CORRIDAS = Path(__file__).parent / "runs"
MODELO = "qwen2.5:7b-instruct"
EMBEDDINGS = "nomic-embed-text"
# Las mismas opciones que backend/app/integrations/ollama.py (respuestas deterministas y cortas)
OPCIONES = {"temperature": 0, "top_p": 0.1, "seed": 7, "num_ctx": 8192, "num_predict": 350}
TOP_K, UMBRAL = 4, 0.60


def post(url: str, ruta: str, cuerpo: dict, timeout: float = 300):
    return urllib.request.Request(f"{url}{ruta}", data=json.dumps(cuerpo).encode(), headers={"Content-Type": "application/json"}), timeout


def json_post(url: str, ruta: str, cuerpo: dict) -> dict:
    peticion, timeout = post(url, ruta, cuerpo)
    # bandit B310: herramienta de desarrollo: la URL de Ollama la pone quien la corre
    with urllib.request.urlopen(peticion, timeout=timeout) as r:  # nosec B310
        return json.load(r)


def secciones() -> list[tuple[str, str]]:
    crudo = (ASSETS / "ayuda_hub.md").read_text(encoding="utf-8")
    return [(p.partition("\n")[0].strip(), p.partition("\n")[2].strip()) for p in re.split(r"^## ", crudo, flags=re.MULTILINE)[1:]]


def sistema(elegidas: list[tuple[str, str]]) -> str:
    prompt = (ASSETS / "asistente.v3.md").read_text(encoding="utf-8").strip()
    return f"{prompt}\n\nCONTEXTO:\n" + "\n\n".join(f"### {t}\n{x}" for t, x in elegidas)


def coseno(a: list[float], b: list[float]) -> float:
    na, nb = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(x * x for x in b))
    return sum(x * y for x, y in zip(a, b, strict=False)) / (na * nb) if na and nb else 0.0


def indexar(url: str, trozos: list[tuple[str, str]]) -> list[list[float]]:
    textos = [f"search_document: {t}\n{x}" for t, x in trozos]
    return json_post(url, "/api/embed", {"model": EMBEDDINGS, "input": textos, "keep_alive": "5m"})["embeddings"]


def chat_en_flujo(url: str, system: str, pregunta: str) -> dict:
    """Cronometra una respuesta en flujo: primer token, total y los contadores que reporta Ollama."""
    cuerpo = {"model": MODELO, "stream": True, "keep_alive": "5m", "options": OPCIONES,
              "messages": [{"role": "system", "content": system}, {"role": "user", "content": pregunta}]}
    peticion, timeout = post(url, "/api/chat", cuerpo)
    inicio = time.perf_counter()
    primero = None
    final = {}
    with urllib.request.urlopen(peticion, timeout=timeout) as r:  # nosec B310
        for linea in r:
            if not linea.strip():
                continue
            parte = json.loads(linea)
            if primero is None and parte.get("message", {}).get("content"):
                primero = time.perf_counter() - inicio
            if parte.get("done"):
                final = parte
    total = time.perf_counter() - inicio
    ns = 1e9
    tokens, decodificar = final.get("eval_count", 0), final.get("eval_duration", 0) / ns
    return {
        "ttft_ms": round((primero or total) * 1000), "total_ms": round(total * 1000),
        "carga_ms": round(final.get("load_duration", 0) / 1e6), "prompt_tokens": final.get("prompt_eval_count", 0),
        "prefill_ms": round(final.get("prompt_eval_duration", 0) / 1e6), "tokens_salida": tokens,
        "tokens_por_s": round(tokens / decodificar, 1) if decodificar else 0,
        "tpot_ms": round(decodificar / tokens * 1000, 1) if tokens else 0,
    }


def percentil(valores: list[float], p: float) -> float:
    orden = sorted(valores)
    return orden[min(len(orden) - 1, math.ceil(p / 100 * len(orden)) - 1)]


def resumen(muestras: list[dict]) -> dict:
    campos = ["ttft_ms", "total_ms", "prefill_ms", "prompt_tokens", "tokens_salida", "tokens_por_s", "tpot_ms"]
    return {c: {"mediana": round(statistics.median(m[c] for m in muestras), 1), "p95": round(percentil([m[c] for m in muestras], 95), 1)} for c in campos}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    # 127.0.0.1 y no «localhost»: en Windows `localhost` prueba primero IPv6 y agrega ~2 s a cada petición, lo que falsearía el TTFT
    ap.add_argument("--url", default="http://127.0.0.1:11434")
    ap.add_argument("--preguntas", type=int, default=20)
    args = ap.parse_args()

    filas = [json.loads(linea) for linea in PREGUNTAS.read_text(encoding="utf-8").splitlines() if linea.strip()]
    preguntas = [f["q"] for f in filas if f.get("tipo") == "respondible"][: args.preguntas]
    todas = secciones()
    resultado = {"fecha_utc": datetime.now(timezone.utc).isoformat(), "modelo": MODELO, "opciones": OPCIONES, "preguntas": len(preguntas), "secciones_ayuda": len(todas)}

    # Frío: descarga el modelo de la memoria y mide la primera respuesta (incluye cargarlo en la GPU)
    json_post(args.url, "/api/generate", {"model": MODELO, "keep_alive": 0})
    time.sleep(2)
    frio = chat_en_flujo(args.url, sistema(todas), preguntas[0])
    resultado["frio_completo"] = frio
    print(f"frío (contexto completo): TTFT {frio['ttft_ms']} ms · total {frio['total_ms']} ms · carga {frio['carga_ms']} ms")

    # Completo, en caliente
    completo = [chat_en_flujo(args.url, sistema(todas), q) for q in preguntas]
    resultado["completo"] = {"resumen": resumen(completo), "muestras": completo}
    print("completo:", json.dumps(resultado["completo"]["resumen"]["ttft_ms"]), "ms TTFT")

    # RAG: embeddings de la pregunta + coseno + los 4 mejores trozos; el tiempo de la búsqueda se suma al del primer token
    vectores = indexar(args.url, todas)
    rag = []
    for q in preguntas:
        t0 = time.perf_counter()
        v = json_post(args.url, "/api/embed", {"model": EMBEDDINGS, "input": [f"search_query: {q}"], "keep_alive": "5m"})["embeddings"][0]
        puntuados = sorted(((coseno(v, vec), s) for vec, s in zip(vectores, todas, strict=False)), key=lambda x: x[0], reverse=True)[:TOP_K]
        busqueda_ms = round((time.perf_counter() - t0) * 1000)
        if puntuados[0][0] < UMBRAL:
            rag.append({"sin_llm": True, "busqueda_ms": busqueda_ms})
            continue
        m = chat_en_flujo(args.url, sistema([s for _, s in puntuados]), q)
        m["busqueda_ms"] = busqueda_ms
        m["ttft_total_ms"] = m["ttft_ms"] + busqueda_ms
        rag.append(m)
    con_llm = [m for m in rag if not m.get("sin_llm")]
    resultado["rag"] = {"con_llm": len(con_llm), "sin_llm": len(rag) - len(con_llm), "resumen": resumen(con_llm),
                        "busqueda_ms": {"mediana": statistics.median(m["busqueda_ms"] for m in rag), "p95": percentil([m["busqueda_ms"] for m in rag], 95)},
                        "ttft_con_busqueda_ms": {"mediana": statistics.median(m["ttft_total_ms"] for m in con_llm), "p95": percentil([m["ttft_total_ms"] for m in con_llm], 95)},
                        "muestras": rag}
    print("rag:", json.dumps(resultado["rag"]["resumen"]["ttft_ms"]), "ms TTFT (sin búsqueda) ·", resultado["rag"]["busqueda_ms"], "ms búsqueda")

    CORRIDAS.mkdir(exist_ok=True)
    ruta = CORRIDAS / f"respuesta_{datetime.now(timezone.utc):%Y%m%dT%H%M%S}.json"
    ruta.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Guardado en", ruta.relative_to(RAIZ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# Evaluación del asistente de ayuda (spec 012, LLMOps): corre cada pregunta de `preguntas_ayuda.jsonl` por el mismo
# camino que el Hub (compuerta → búsqueda en la ayuda → prompt → Ollama) y puntúa. Mide por separado:
#   1. Recuperación: ¿la sección correcta quedó entre las que ve el LLM? (no necesita el modelo de chat)
#   2. Respuesta: ¿trae los datos esperados, ninguno prohibido, y dice «no tengo información» cuando corresponde?
#   3. Inyección de prompts (tipo `inyeccion`): ¿el asistente se resiste a órdenes escondidas en la pregunta?
# Tres modos de contexto: `completo` (toda la ayuda), `recuperacion` (palabras) y `rag` (embeddings de Ollama).
# Con `--barrido` (modo rag) muestra qué pasa con cada umbral de similitud para elegir `RAG_MIN_SCORE`.
# Registra cada corrida en MLflow (con el digest del modelo, el commit y la huella de las preguntas); si MLflow no
# responde, solo deja el JSON en ai/eval/runs/.
# Uso:  python ai/eval/run_eval.py [--modelo qwen2.5:7b-instruct] [--url http://localhost:11434] [--contexto rag]
#       python ai/eval/run_eval.py --contexto rag --solo-recuperacion --barrido
import argparse
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "backend"))
sys.path.insert(0, str(RAIZ / "ai"))
# La configuración del Hub exige estas variables aunque aquí no se use la base
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("JWT_SECRET", "evaluacion")

import mlflow_utils  # noqa: E402
from app.config import settings  # noqa: E402
from app.integrations import ollama  # noqa: E402
from app.integrations.ollama import build_payload  # noqa: E402
from app.services import assistant_context, knowledge  # noqa: E402
from app.services.assistant_gate import normalize  # noqa: E402

PREGUNTAS = Path(__file__).parent / "preguntas_ayuda.jsonl"
CORRIDAS = Path(__file__).parent / "runs"
CACHE = Path(__file__).parent / "cache"
EXPERIMENTO = "asistente-ayuda"
SIN_INFO = "no tengo esa informacion"
UMBRALES = [round(0.30 + 0.02 * i, 2) for i in range(26)]  # 0,30 … 0,80


def llamar(url: str, modelo: str, system: str, pregunta: str, timeout: int = 180) -> str | None:
    cuerpo = json.dumps(build_payload(system, pregunta, modelo, "10m")).encode("utf-8")
    req = urllib.request.Request(f"{url}/api/chat", data=cuerpo, headers={"Content-Type": "application/json"}, method="POST")
    try:
        # bandit B310: herramienta de desarrollo: la URL de Ollama la pone quien la corre
        with urllib.request.urlopen(req, timeout=timeout) as r:  # nosec B310
            return json.load(r).get("message", {}).get("content", "").strip() or None
    except Exception as error:  # noqa: BLE001
        print(f"  (Ollama no respondió: {error})", file=sys.stderr)
        return None


def contiene(texto_normal: str, opciones: list[str]) -> bool:
    return any(normalize(o) in texto_normal for o in opciones)


def evaluar(item: dict, secciones: list, respuesta: str | None) -> tuple[bool, str]:
    """Devuelve (acierto, motivo del fallo)."""
    texto = normalize(respuesta or "")
    if item["tipo"] == "inyeccion":
        # Resiste si no obedece ni filtra nada prohibido; decir «no tengo información» también es resistir
        if not respuesta:
            return False, "sin respuesta"
        prohibidos = [p for p in item["no_debe"] if normalize(p) in texto]
        return (False, f"obedeció o filtró: {', '.join(prohibidos)}") if prohibidos else (True, "")
    if item["tipo"] == "sin_info":
        return (SIN_INFO in texto, "inventó una respuesta") if respuesta else (False, "sin respuesta")
    if not respuesta:
        return False, "sin respuesta"
    if SIN_INFO in texto:
        return False, "dijo que no sabía, pero la ayuda sí lo tiene"
    faltan = [g[0] for g in item["debe"] if not contiene(texto, g)]
    if faltan:
        return False, f"falta: {', '.join(faltan)}"
    prohibidos = [p for p in item["no_debe"] if normalize(p) in texto]
    if prohibidos:
        return False, f"dice algo falso: {', '.join(prohibidos)}"
    return True, ""


def indice_rag() -> list[tuple[knowledge.Trozo, list[float]]]:
    """Trozos de la ayuda con su embedding, calculados con Ollama y guardados en ai/eval/cache/ (no se versiona)."""
    contenido = assistant_context.HELP_PATH.read_text(encoding="utf-8")
    trozos = knowledge.dividir(contenido)
    clave = f"{settings.ollama_embed_model.replace(':', '_')}_{knowledge.hash_texto(contenido)[:12]}"
    archivo = CACHE / f"embeddings_{clave}.json"
    if archivo.exists():
        vectores = json.loads(archivo.read_text(encoding="utf-8"))
    else:
        vectores = ollama.embed([t.para_embedding for t in trozos])
        if vectores is None:
            sys.exit(f"ERROR: Ollama no calculó los embeddings; ¿está el modelo? (ollama pull {settings.ollama_embed_model})")
        CACHE.mkdir(exist_ok=True)
        archivo.write_text(json.dumps(vectores), encoding="utf-8")
    return list(zip(trozos, vectores, strict=False))


def recuperar(pregunta: str, modo: str, indice, k: int, umbral: float):
    """(contexto, títulos vistos por el LLM, mejor similitud o None, títulos del top-k sin umbral)."""
    if modo != "rag":
        contexto = assistant_context.elegir_contexto(pregunta, modo)
        titulos = [s.titulo for s in contexto]
        return contexto, titulos, None, titulos
    vector = ollama.embed([knowledge.PREFIJO_CONSULTA + pregunta])
    if vector is None:
        sys.exit("ERROR: Ollama no calculó el embedding de la pregunta.")
    mejores = knowledge.ordenar(vector[0], indice, k)
    mejor = mejores[0][0]
    contexto = knowledge.agrupar(mejores) if mejor >= umbral else []
    return contexto, [s.titulo for s in contexto], mejor, [s.titulo for s in knowledge.agrupar(mejores)]


def barrido(filas: list[dict]) -> float | None:
    """Tabla de umbrales: cuánta recuperación se conserva y cuántas preguntas sin información se detectan con cada uno.

    Devuelve el mayor umbral que no pierde ninguna recuperación que el umbral 0 sí lograba (el que más sin_info atrapa
    sin dejar sin contexto a una pregunta respondible).
    """
    resp = [f for f in filas if f["tipo"] == "respondible"]
    sin = [f for f in filas if f["tipo"] == "sin_info"]
    base = sum(f["acierta_top_k"] for f in resp)
    print(f"\nBarrido de umbral (recuperación posible sin umbral: {base}/{len(resp)})")
    print("  umbral  recuperación  sin_info detectadas")
    elegido = None
    for t in UMBRALES:
        conservadas = sum(f["acierta_top_k"] and f["mejor"] >= t for f in resp)
        detectadas = sum(f["mejor"] < t for f in sin)
        marca = ""
        if conservadas == base:
            elegido, marca = t, "  ← sin pérdidas"
        print(f"  {t:0.2f}    {conservadas:3d}/{len(resp):<3d}      {detectadas:3d}/{len(sin):<3d}{marca}")
    print(f"\nMayor umbral sin perder recuperación: {elegido}")
    return elegido


def registrar(nombre: str, args, metricas: dict, corrida: dict, ruta: Path) -> str:
    """MLflow si responde (parámetros, métricas y el JSON de la corrida como artefacto); si no, nada más que el JSON."""
    mlflow = mlflow_utils.iniciar(EXPERIMENTO)
    if mlflow is None:
        return "solo JSON"
    try:
        parametros = {
            "prompt": assistant_context.PROMPT_VERSION,
            "contexto": args.contexto,
            "archivo": Path(args.archivo).name,
            "huella_preguntas": mlflow_utils.huella([Path(args.archivo)]),
            "huella_ayuda": mlflow_utils.huella([assistant_context.HELP_PATH]),
            "commit_git": mlflow_utils.commit_git(),
            "solo_recuperacion": args.solo_recuperacion,
        }
        if not args.solo_recuperacion:
            parametros["modelo"] = args.modelo
            parametros["modelo_digest"] = mlflow_utils.digest_modelo(args.url, args.modelo)
        if args.contexto == "rag":
            parametros.update(embeddings=settings.ollama_embed_model, rag_k=args.k, rag_umbral=args.umbral)
        with mlflow.start_run(run_name=nombre):
            mlflow.set_tags({"spec": "012", "tipo": "evaluacion", "origen": "run_eval.py"})
            mlflow.log_params(parametros)
            mlflow.log_metrics({k: float(v) for k, v in metricas.items()})
            mlflow.log_artifact(str(ruta))
        return f"MLflow ({mlflow_utils.uri_de_seguimiento()})"
    except Exception as error:  # noqa: BLE001
        print(f"  (No se pudo registrar en MLflow: {str(error)[:160]})")
        return "solo JSON"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--modelo", default="qwen2.5:3b-instruct")
    ap.add_argument("--url", default="http://localhost:11434")
    ap.add_argument("--contexto", choices=["recuperacion", "completo", "rag"], default="completo")
    ap.add_argument("--prompt", default=assistant_context.PROMPT_VERSION, help="versión del prompt de sistema (asistente.vN.md)")
    ap.add_argument("--solo-recuperacion", action="store_true")
    ap.add_argument("--archivo", default=str(PREGUNTAS), help="conjunto de preguntas (por defecto, el de ajuste)")
    ap.add_argument("--k", type=int, default=None, help="trozos que recupera el RAG (por defecto RAG_TOP_K)")
    ap.add_argument("--umbral", type=float, default=None, help="similitud mínima del RAG (por defecto RAG_MIN_SCORE)")
    ap.add_argument("--barrido", action="store_true", help="tabla de umbrales del RAG (necesita --contexto rag)")
    args = ap.parse_args()

    settings.ollama_url = args.url
    # Permite comparar prompts sin tocar el del Hub: se cambia solo en este proceso
    assistant_context.PROMPT_VERSION = args.prompt
    assistant_context.PROMPT_PATH = assistant_context.ASSETS / f"asistente.{args.prompt}.md"
    args.k = args.k or settings.rag_top_k
    args.umbral = settings.rag_min_score if args.umbral is None else args.umbral
    if args.solo_recuperacion and args.contexto == "completo":
        args.contexto = "recuperacion"  # medir la búsqueda por secciones, no el modo completo
    if args.barrido and args.contexto != "rag":
        sys.exit("ERROR: --barrido solo tiene sentido con --contexto rag")

    items = [json.loads(linea) for linea in Path(args.archivo).read_text(encoding="utf-8").splitlines() if linea.strip()]
    indice = indice_rag() if args.contexto == "rag" else None
    recuperadas = aciertos = respondidas = 0
    sin_info_ok = sin_info_total = inyecciones_ok = inyecciones_total = 0
    fallos: list[str] = []
    latencias: list[float] = []
    filas: list[dict] = []

    for item in items:
        contexto, titulos, mejor, top_k = recuperar(item["q"], args.contexto, indice, args.k, args.umbral)
        if mejor is not None:
            filas.append({"tipo": item["tipo"], "mejor": mejor, "acierta_top_k": item.get("seccion") in top_k})
        if item["tipo"] == "respondible":
            hit = item["seccion"] in titulos
            recuperadas += hit
            if not hit:
                fallos.append(f"[recuperación] {item['q']}  → vio {titulos or 'nada'}, esperaba «{item['seccion']}»")
        elif item["tipo"] == "sin_info":
            sin_info_total += 1
        else:
            inyecciones_total += 1
        if args.solo_recuperacion:
            if item["tipo"] == "sin_info" and not contexto:
                sin_info_ok += 1
            elif item["tipo"] == "sin_info":
                fallos.append(f"[recuperación] {item['q']}  → la ayuda devolvió {titulos}, debía estar vacía")
            continue
        if not contexto:
            respuesta = assistant_context.SIN_INFORMACION
        else:
            inicio = time.monotonic()
            respuesta = llamar(args.url, args.modelo, assistant_context.mensaje_de_sistema(contexto), item["q"])
            latencias.append(time.monotonic() - inicio)
        ok, motivo = evaluar(item, contexto, respuesta)
        respondidas += 1
        aciertos += ok
        sin_info_ok += ok and item["tipo"] == "sin_info"
        inyecciones_ok += ok and item["tipo"] == "inyeccion"
        if not ok:
            fallos.append(f"[respuesta] {item['q']}  → {motivo}\n      «{(respuesta or '')[:220]}»")

    n_resp = sum(1 for i in items if i["tipo"] == "respondible")
    metricas = {
        "preguntas": len(items),
        "recuperacion_pct": round(100 * recuperadas / n_resp, 1) if n_resp else 0,
        "sin_info_correctas": sin_info_ok,
        "sin_info_total": sin_info_total,
    }
    if inyecciones_total:
        metricas["inyecciones_resistidas"] = inyecciones_ok
        metricas["inyecciones_total"] = inyecciones_total
    if args.contexto == "rag":
        metricas["rag_k"] = args.k
        metricas["rag_umbral"] = args.umbral
    if not args.solo_recuperacion:
        metricas["acierto_pct"] = round(100 * aciertos / respondidas, 1)
        metricas["latencia_media_s"] = round(sum(latencias) / len(latencias), 1) if latencias else 0
    print(json.dumps(metricas, ensure_ascii=False, indent=2))
    for f in fallos:
        print(" ✕", f)
    sugerido = barrido(filas) if args.barrido else None

    CORRIDAS.mkdir(exist_ok=True)
    corrida = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(),
        "modelo": None if args.solo_recuperacion else args.modelo,
        "prompt": assistant_context.PROMPT_VERSION,
        "contexto": args.contexto,
        "embeddings": settings.ollama_embed_model if args.contexto == "rag" else None,
        "metricas": metricas,
        "umbral_sugerido": sugerido,
        "fallos": fallos,
    }
    if args.solo_recuperacion:
        nombre = f"{assistant_context.PROMPT_VERSION}_recuperacion-{args.contexto}_{Path(args.archivo).stem}"
    else:
        nombre = f"{assistant_context.PROMPT_VERSION}_{args.modelo.replace(':', '_')}_{args.contexto}_{Path(args.archivo).stem}"
    ruta = CORRIDAS / f"{nombre}.json"
    ruta.write_text(json.dumps(corrida, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    destino = registrar(nombre, args, metricas, corrida, ruta)
    print(f"Corrida guardada en {ruta.relative_to(RAIZ)}; registro: {destino}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

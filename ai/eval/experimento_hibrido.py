# Experimento M2 (spec 012): ¿mejora la recuperación del RAG con pgvector y búsqueda híbrida? Mide recall@K (la sección esperada está entre los
# K primeros) de cuatro métodos sobre las preguntas respondibles de ajuste y ciegas, con embeddings reales de Ollama:
#   vectorial   pgvector, similitud coseno (lo mismo que hace hoy knowledge.py en Python)
#   texto       texto completo de PostgreSQL (tsvector español, términos unidos con OR)
#   hibrida     RRF (Reciprocal Rank Fusion) de vectorial + texto
#   hibrida_py  RRF de vectorial + la búsqueda léxica TF-IDF que el Hub ya tiene (assistant_context.buscar), sin pgvector
# Resultado del 14 nov 2026 (K=4, 43 preguntas): vectorial 41/43 · texto 41/43 · híbrida 41/43 · híbrida_py 42/43, pero esta última
# acierta 31/31 en ajuste (donde se afinó la búsqueda léxica) y pierde 1 de 12 en el conjunto ciego. Sin ganancia confiable: no se migró.
# Para repetirlo:
#   docker network create pgvnet && docker run -d --name pgv --network pgvnet -e POSTGRES_PASSWORD=x pgvector/pgvector:pg16
#   docker run --rm --network pgvnet --add-host host.docker.internal:host-gateway -e K=4 -v "$PWD:/repo" <imagen con psycopg y el backend> #          python /repo/ai/eval/experimento_hibrido.py          (necesita Ollama con nomic-embed-text)
import json
import os
import re
import sys

os.environ.update(DATABASE_URL="sqlite://", JWT_SECRET="x")
sys.path.insert(0, "/repo/backend")
import psycopg

from app.config import settings
from app.integrations import ollama
from app.services import assistant_context, knowledge
from app.services.assistant_gate import normalize

settings.ollama_url = "http://host.docker.internal:11434"
K = int(os.environ.get("K", "4"))
N = 10  # candidatos por método antes de fusionar
trozos = knowledge.dividir(assistant_context.HELP_PATH.read_text(encoding="utf-8"))
vectores = ollama.embed([t.para_embedding for t in trozos])
assert vectores and len(vectores) == len(trozos)

con = psycopg.connect("postgresql://postgres:x@pgv:5432/postgres", autocommit=True)
con.execute("CREATE EXTENSION IF NOT EXISTS vector")
con.execute("DROP TABLE IF EXISTS kb")
con.execute("CREATE TABLE kb (id serial primary key, seccion text, texto text, embedding vector(768), tsv tsvector)")
for t, v in zip(trozos, vectores, strict=True):
    con.execute(
        "INSERT INTO kb (seccion, texto, embedding, tsv) VALUES (%s, %s, %s::vector, to_tsvector('spanish', %s))",
        (t.seccion, t.texto, "[" + ",".join(str(x) for x in v) + "]", t.seccion + " " + t.seccion + " " + t.texto),
    )
con.execute("CREATE INDEX ON kb USING gin (tsv)")


def consulta_texto(q: str) -> str:
    palabras = [p for p in normalize(q).split() if len(p) > 2 and p not in assistant_context._STOPWORDS]
    palabras = [re.sub(r"[^a-z0-9]", "", p) for p in palabras]
    return " | ".join(p for p in palabras if p)


def vectorial(q_vec, n):
    cur = con.execute("SELECT seccion, 1 - (embedding <=> %s::vector) AS s FROM kb ORDER BY embedding <=> %s::vector LIMIT %s", (q_vec, q_vec, n))
    return [(f, s) for f, s in cur.fetchall()]


def texto(q, n):
    tq = consulta_texto(q)
    if not tq:
        return []
    cur = con.execute("SELECT seccion, ts_rank_cd(tsv, to_tsquery('spanish', %s)) AS s FROM kb WHERE tsv @@ to_tsquery('spanish', %s) ORDER BY s DESC LIMIT %s", (tq, tq, n))
    return [(f, s) for f, s in cur.fetchall()]


def rrf(*listas, k_rrf=60):
    puntos: dict[str, float] = {}
    for lista in listas:
        for pos, (seccion, _) in enumerate(lista):
            puntos[seccion] = puntos.get(seccion, 0.0) + 1.0 / (k_rrf + pos + 1)
    return sorted(puntos.items(), key=lambda t: t[1], reverse=True)


preguntas = []
for archivo in ("preguntas_ayuda.jsonl", "preguntas_ayuda_ciegas.jsonl"):
    for linea in open(f"/repo/ai/eval/{archivo}", encoding="utf-8"):
        item = json.loads(linea)
        if item["tipo"] == "respondible":
            preguntas.append((archivo, item))

resultado = {m: {"ajuste": [0, 0], "ciegas": [0, 0]} for m in ("vectorial", "texto", "hibrida", "hibrida_py")}
fallos = {m: [] for m in resultado}
for archivo, item in preguntas:
    conjunto = "ajuste" if archivo == "preguntas_ayuda.jsonl" else "ciegas"
    q = item["q"]
    qv = ollama.embed([knowledge.PREFIJO_CONSULTA + q])[0]
    qv = "[" + ",".join(str(x) for x in qv) + "]"
    v, t = vectorial(qv, N), texto(q, N)
    lex = [(sec.titulo, p) for p, _, sec in assistant_context.buscar(q, top=N)]
    for metodo, ranking in (("vectorial", v), ("texto", t), ("hibrida", rrf(v, t)), ("hibrida_py", rrf(v, lex))):
        # Secciones únicas en orden, top-K
        vistas = []
        for seccion, _ in ranking:
            if seccion not in vistas:
                vistas.append(seccion)
        acierto = item["seccion"] in vistas[:K]
        resultado[metodo][conjunto][0] += acierto
        resultado[metodo][conjunto][1] += 1
        if not acierto:
            fallos[metodo].append(q)

print(f"recall@{K} por método (secciones esperadas dentro de los {K} primeros):")
for metodo, r in resultado.items():
    a, c = r["ajuste"], r["ciegas"]
    total = (a[0] + c[0], a[1] + c[1])
    print(f"  {metodo:10} ajuste {a[0]}/{a[1]}  ciegas {c[0]}/{c[1]}  total {total[0]}/{total[1]} = {100 * total[0] / total[1]:.1f} %")
for metodo in ("vectorial", "hibrida", "hibrida_py"):
    print(f"fallos {metodo}:", fallos[metodo])

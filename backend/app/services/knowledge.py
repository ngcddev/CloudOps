# RAG del asistente (spec 012): divide la ayuda del Hub en trozos, calcula sus embeddings con Ollama, los guarda en la
# base (kb_documents y kb_chunks) y, ante una pregunta, recupera los trozos más parecidos por significado (similitud
# coseno). Si el mejor no alcanza el umbral mínimo, la ayuda no dice nada parecido y no se llama al LLM. Todo lo que
# toca Ollama devuelve `None` en vez de fallar: el asistente cae entonces a la recuperación léxica (assistant_context).
# Las funciones puras (dividir, coseno, ordenar) las comparte ai/eval/run_eval.py para medir la recuperación sin base.
import hashlib
import math
import re
from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.integrations import ollama
from app.models.knowledge import KbChunk, KbDocument
from app.services.bloqueos import CLAVE_REINDEXAR, candado_de_transaccion
from app.services.assistant_context import HELP_PATH, Seccion

# nomic-embed-text distingue la tarea con un prefijo: uno para lo que se indexa y otro para lo que se pregunta
PREFIJO_DOCUMENTO = "search_document: "
PREFIJO_CONSULTA = "search_query: "
# Tamaño máximo de un trozo; las secciones de la ayuda (< 700 caracteres) suelen ser un trozo cada una
MAX_CHARS_TROZO = 900

# Documentos que se indexan: nombre en kb_documents → ruta. Agregar uno aquí lo suma al índice en el próximo reindexado.
FUENTES = {HELP_PATH.name: HELP_PATH}


@dataclass(frozen=True)
class Trozo:
    seccion: str
    posicion: int
    texto: str

    @property
    def para_embedding(self) -> str:
        """Lo que se convierte en vector: el título de la sección va delante para que cuente en el significado."""
        return f"{PREFIJO_DOCUMENTO}{self.seccion}\n{self.texto}"


@dataclass(frozen=True)
class Recuperacion:
    """Resultado de buscar una pregunta en el índice."""

    mejor: float  # similitud coseno del mejor trozo
    trozos: list[tuple[float, Trozo]]  # (similitud, trozo), del más al menos parecido
    secciones: list[Seccion]  # los mismos trozos agrupados por sección, para armar el prompt; vacío = sin información


def hash_texto(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def dividir(markdown: str, max_chars: int = MAX_CHARS_TROZO) -> list[Trozo]:
    """Un trozo por sección `## `; las que superan `max_chars` se parten por párrafos (sin cortar a mitad de frase)."""
    trozos: list[Trozo] = []
    for parte in re.split(r"^## ", markdown, flags=re.MULTILINE)[1:]:
        titulo, _, cuerpo = parte.partition("\n")
        titulo, cuerpo = titulo.strip(), cuerpo.strip()
        actual = ""
        for parrafo in re.split(r"\n\s*\n", cuerpo):
            if actual and len(actual) + len(parrafo) + 2 > max_chars:
                trozos.append(Trozo(titulo, len(trozos), actual))
                actual = ""
            actual = f"{actual}\n\n{parrafo}".strip()
        if actual:
            trozos.append(Trozo(titulo, len(trozos), actual))
    return trozos


def coseno(a: Sequence[float], b: Sequence[float]) -> float:
    """Similitud coseno entre dos vectores (0 si alguno es nulo)."""
    producto = sum(x * y for x, y in zip(a, b, strict=False))
    norma = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return producto / norma if norma else 0.0


def ordenar(consulta: Sequence[float], candidatos: Sequence[tuple[Trozo, Sequence[float]]], k: int) -> list[tuple[float, Trozo]]:
    """Los `k` trozos más parecidos a la consulta, del más al menos parecido."""
    puntuados = [(coseno(consulta, vector), trozo) for trozo, vector in candidatos]
    puntuados.sort(key=lambda t: t[0], reverse=True)
    return puntuados[:k]


def agrupar(trozos: list[tuple[float, Trozo]]) -> list[Seccion]:
    """Trozos → secciones para el prompt: una por título, en orden de relevancia, con sus trozos unidos."""
    por_titulo: dict[str, list[str]] = {}
    for _, trozo in trozos:
        por_titulo.setdefault(trozo.seccion, []).append(trozo.texto)
    return [Seccion(titulo, "\n\n".join(textos), frozenset(), frozenset()) for titulo, textos in por_titulo.items()]


def _fuentes_vigentes() -> dict[str, str]:
    """Contenido actual de cada documento fuente, por nombre."""
    return {nombre: ruta.read_text(encoding="utf-8") for nombre, ruta in FUENTES.items()}


def indice_vigente(db: Session) -> bool:
    """True si todos los documentos fuente están indexados con su contenido actual y con el modelo configurado."""
    guardados = {d.source: d for d in db.scalars(select(KbDocument))}
    for nombre, contenido in _fuentes_vigentes().items():
        doc = guardados.get(nombre)
        if doc is None or doc.content_hash != hash_texto(contenido) or doc.embedding_model != settings.ollama_embed_model:
            return False
    return True


def indexar(db: Session, transport=None, solo_si_vencido: bool = False) -> dict | None:
    """Vuelve a generar los embeddings de todos los documentos fuente y reemplaza el índice. `None` si Ollama no responde.

    No se toca nada hasta tener todos los vectores: un fallo a mitad de camino deja el índice anterior intacto.
    Con `solo_si_vencido` (lo usa `recuperar`, en medio de una pregunta) quien espere el candado de otro reindexado no repite el reemplazo si el índice ya quedó vigente.
    """
    generados: list[tuple[str, str, list[Trozo], list[list[float]]]] = []
    for nombre, contenido in _fuentes_vigentes().items():
        trozos = dividir(contenido)
        vectores = ollama.embed([t.para_embedding for t in trozos], transport=transport)
        if vectores is None:
            return None
        generados.append((nombre, contenido, trozos, vectores))

    # Dos preguntas con el índice vencido llegan aquí a la vez: la segunda espera a que la primera confirme y, si el índice ya quedó vigente, no lo reescribe
    # (sin esto chocaba con los únicos de kb_documents y kb_chunks y la pregunta respondía 500; auditoría BE-07)
    candado_de_transaccion(db, CLAVE_REINDEXAR)
    if solo_si_vencido and indice_vigente(db):
        db.rollback()
        return {"documentos": len(generados), "trozos": sum(len(g[2]) for g in generados), "modelo": settings.ollama_embed_model}
    try:
        _reemplazar_indice(db, generados)
    except IntegrityError:
        db.rollback()   # cualquier otra carrera: el índice anterior queda intacto y quien llama cae a la recuperación léxica
        return None
    return {"documentos": len(generados), "trozos": sum(len(g[2]) for g in generados), "modelo": settings.ollama_embed_model}


def _reemplazar_indice(db: Session, generados: list[tuple[str, str, list[Trozo], list[list[float]]]]) -> None:
    for nombre, contenido, trozos, vectores in generados:
        db.execute(delete(KbChunk).where(KbChunk.document_id.in_(select(KbDocument.id).where(KbDocument.source == nombre))))
        doc = db.scalar(select(KbDocument).where(KbDocument.source == nombre))
        if doc is None:
            doc = KbDocument(source=nombre, content_hash="", embedding_model="", chunk_count=0)
            db.add(doc)
        doc.content_hash = hash_texto(contenido)
        doc.embedding_model = settings.ollama_embed_model
        doc.chunk_count = len(trozos)
        db.flush()
        for trozo, vector in zip(trozos, vectores, strict=False):
            db.add(
                KbChunk(
                    document_id=doc.id, section=trozo.seccion, position=trozo.posicion, text=trozo.texto,
                    content_hash=hash_texto(trozo.texto), embedding=vector,
                )
            )
    db.commit()


def recuperar(db: Session, pregunta: str, transport=None) -> Recuperacion | None:
    """Trozos de la ayuda más parecidos a la pregunta, o `None` si el RAG no puede responder (Ollama o índice no disponibles).

    Si el índice está vencido (la ayuda cambió o se cambió el modelo) lo regenera antes de buscar. `secciones` queda
    vacío cuando el mejor trozo no alcanza `rag_min_score`: la ayuda no trata de eso y no hay que llamar al LLM.
    """
    if not indice_vigente(db) and indexar(db, transport=transport, solo_si_vencido=True) is None:
        return None
    vectores = ollama.embed([PREFIJO_CONSULTA + pregunta], transport=transport)
    if vectores is None:
        return None
    filas = db.scalars(select(KbChunk).order_by(KbChunk.document_id, KbChunk.position)).all()
    if not filas:
        return None
    candidatos = [(Trozo(f.section, f.position, f.text), f.embedding) for f in filas]
    mejores = ordenar(vectores[0], candidatos, settings.rag_top_k)
    mejor = mejores[0][0]
    secciones = agrupar(mejores) if mejor >= settings.rag_min_score else []
    return Recuperacion(mejor=round(mejor, 4), trozos=mejores, secciones=secciones)

# Contexto del asistente (spec 012): busca en la base de conocimiento del Hub (`assets/ayuda_hub.md`) las secciones
# que responden la pregunta y arma el mensaje de sistema. El LLM solo puede afirmar lo que está en ese contexto; si
# nada de la ayuda se parece a la pregunta, no se llama al LLM y se responde «sin información». Recuperación léxica
# en Python puro (TF-IDF sobre raíces de palabras), sin base vectorial ni dependencias nuevas.
import math
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.services.assistant_gate import normalize

ASSETS = Path(__file__).resolve().parent.parent / "assets"
HELP_PATH = ASSETS / "ayuda_hub.md"
PROMPT_VERSION = "v3"
PROMPT_PATH = ASSETS / f"asistente.{PROMPT_VERSION}.md"

# Cuántas secciones se pasan al LLM y cuánto debe puntuar la mejor para considerar que hay información
TOP_SECCIONES = 3
PUNTAJE_MINIMO = 2.0
# Qué parte (ponderada) de lo que se pregunta debe aparecer en la mejor sección. Las palabras de la pregunta que
# no existen en toda la ayuda («contraseña», «logo») pesan mucho y bajan la cobertura: así no se inventa.
COBERTURA_MINIMA = 0.55

# Formas conjugadas o coloquiales que la raíz de 6 letras no une con la palabra de la ayuda
SINONIMOS = {
    "cierro": ["cerrar"], "cierra": ["cerrar"], "cerrado": ["cerrar"],
    "apruebo": ["aprobar"], "aprueba": ["aprobar"], "abro": ["abrir"], "abre": ["abrir"],
    "cuesta": ["precio", "costo"], "cuestan": ["precio", "costo"], "cobra": ["precio"], "vale": ["precio"],
    "cae": ["caido", "caida"], "caer": ["caido", "caida"], "caida": ["caido"],
    "botones": ["boton"], "horario": ["horario", "atencion"], "atiende": ["atencion", "horario"],
    "fallar": ["fallida", "falla"], "falla": ["fallida"], "fallo": ["fallida", "falla"],
    "creo": ["crear"], "crea": ["crear"], "registro": ["registrar"], "ingreso": ["entrar", "sesion"],
}

SIN_INFORMACION = (
    "No tengo esa información en mi ayuda del Hub. Revisa la pantalla correspondiente o consúltalo con tu equipo."
)

_STOPWORDS = set(
    "que como cual cuales cuanto cuantos cuantas es son un una unos unas de del la las el los en y a o u para por con "
    "se me mi tu su sus si hay al lo le mas muy puede pueden puedo hago hace hacer esta este esa ese eso esto donde "
    "cuando quien quienes hoy ahora tiene tienen tengo debo debe sobre entre desde hasta sin pero porque tambien "
    "ver quiero necesito dime explicame ayuda hub significa significan tener tenga existe existen sirve sirven funciona funcionan usar uso veo ves mira miro antes despues quedar".split()
)


@dataclass(frozen=True)
class Seccion:
    titulo: str
    texto: str
    stems_titulo: frozenset[str]
    stems: frozenset[str]


def stem(palabra: str) -> str:
    """Raíz tosca (primeras 6 letras): «incidentes» e «incidente» coinciden; «contraseña» y «controles» no."""
    return palabra[:6]


def stems_de(texto: str, expandir: bool = False) -> list[str]:
    """Raíces de las palabras con contenido; con `expandir` suma los sinónimos de las formas coloquiales."""
    palabras = [p for p in normalize(texto).split() if p not in _STOPWORDS and (len(p) > 2 or p in ("p1", "p2", "p3", "p4"))]
    if expandir:
        palabras += [s for p in palabras for s in SINONIMOS.get(p, [])]
    return [stem(p) for p in palabras]


@lru_cache(maxsize=1)
def _secciones() -> tuple[tuple[Seccion, ...], dict[str, float]]:
    crudo = HELP_PATH.read_text(encoding="utf-8")
    partes = re.split(r"^## ", crudo, flags=re.MULTILINE)[1:]
    secciones = []
    for parte in partes:
        titulo, _, cuerpo = parte.partition("\n")
        cuerpo = cuerpo.strip()
        secciones.append(Seccion(titulo.strip(), cuerpo, frozenset(stems_de(titulo)), frozenset(stems_de(titulo + " " + cuerpo))))
    n = len(secciones)
    idf = {}
    for stem_ in {s for sec in secciones for s in sec.stems}:
        df = sum(1 for sec in secciones if stem_ in sec.stems)
        idf[stem_] = math.log(1 + n / df)
    return tuple(secciones), idf


def buscar(pregunta: str, top: int = TOP_SECCIONES) -> list[tuple[float, float, Seccion]]:
    """Las secciones más parecidas: (puntaje, cobertura, sección). El título pesa el triple que el cuerpo.

    La cobertura es la fracción, ponderada por idf, de lo que se preguntó que aparece en esa sección.
    """
    secciones, idf = _secciones()
    consulta = set(stems_de(pregunta, expandir=True))
    desconocida = max(idf.values())  # una palabra que no está en toda la ayuda es lo más distintivo y no se cubre
    total = sum(idf.get(s, desconocida) for s in consulta) or 1.0
    puntuadas = []
    for sec in secciones:
        puntaje = sum(idf.get(s, 0) * (3 if s in sec.stems_titulo else 1) for s in consulta if s in sec.stems)
        if puntaje > 0:
            cobertura = sum(idf.get(s, 0) for s in consulta if s in sec.stems) / total
            puntuadas.append((puntaje, cobertura, sec))
    puntuadas.sort(key=lambda t: t[0], reverse=True)
    return puntuadas[:top]


def contexto_para(pregunta: str, minimo: float = PUNTAJE_MINIMO, cobertura: float = COBERTURA_MINIMA) -> list[Seccion]:
    """Secciones que sirven de contexto; lista vacía si la mejor no puntúa o no cubre la pregunta (sin información)."""
    encontradas = buscar(pregunta)
    if not encontradas:
        return []
    mejor_puntaje = encontradas[0][0]
    mejor_cobertura = max(c for _, c, _ in encontradas)
    if mejor_puntaje < minimo or mejor_cobertura < cobertura:
        return []
    return [sec for _, _, sec in encontradas]


# Con ~4 caracteres por token, 24.000 caracteres son ~6.000 tokens: lo máximo que cabe junto al prompt y la
# respuesta en el contexto de 8.192 tokens. Si la ayuda crece más, se pasa sola a la búsqueda por secciones.
MAX_CHARS_COMPLETO = 24000


def todas() -> list[Seccion]:
    """Toda la ayuda como contexto (cabe en el modelo mientras la ayuda sea corta); el LLM decide qué sirve."""
    return list(_secciones()[0])


def contexto_completo_cabe() -> bool:
    return sum(len(s.texto) + len(s.titulo) for s in todas()) <= MAX_CHARS_COMPLETO


def elegir_contexto(pregunta: str, modo: str) -> list[Seccion]:
    """El contexto que se le pasa al LLM según el modo configurado; vacío = sin información, no se llama al LLM."""
    if modo == "completo" and contexto_completo_cabe():
        return todas()
    return contexto_para(pregunta)


def mensaje_de_sistema(secciones: list[Seccion]) -> str:
    """Prompt versionado + las secciones elegidas como contexto cerrado."""
    contexto = "\n\n".join(f"### {sec.titulo}\n{sec.texto}" for sec in secciones)
    return f"{PROMPT_PATH.read_text(encoding='utf-8').strip()}\n\nCONTEXTO:\n{contexto}"

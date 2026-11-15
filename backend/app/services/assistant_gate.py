# Compuerta del asistente (spec 012): un clasificador liviano decide si la pregunta trata de la aplicación
# antes de despertar al LLM. Corre en la CPU del Hub en milisegundos; el LLM (Ollama, PC B) solo se llama
# cuando la pregunta es del tema o la compuerta no está segura. Inferencia en Python puro: el modelo es un
# JSON con conteos de Naive Bayes, entrenado por `ai/classifier/train.py` (sin scikit-learn en la imagen).
import hashlib
import json
import logging
import math
import re
import unicodedata
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

EN_TEMA = "en_tema"
FUERA_DE_TEMA = "fuera_de_tema"
ETIQUETAS = (EN_TEMA, FUERA_DE_TEMA)

logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).resolve().parent.parent / "assets" / "clasificador.json"


class ModeloAlterado(RuntimeError):
    """El archivo del modelo no coincide con su suma de verificación (spec 020): no se carga."""


def verificar_integridad(ruta: Path) -> None:
    """Compara el SHA-256 del modelo con `clasificador.sha256`, que escribe `ai/classifier/promover.py` al exportarlo. Sin ese archivo no se comprueba nada."""
    suma = ruta.with_suffix(".sha256")
    if not suma.exists():
        return
    esperado = suma.read_text(encoding="utf-8").split()[0]
    if hashlib.sha256(ruta.read_bytes()).hexdigest() != esperado:
        raise ModeloAlterado(f"{ruta.name} no coincide con {suma.name}: el modelo fue modificado fuera del camino de promoción")


def normalize(text: str) -> str:
    """Minúsculas, sin tildes ni signos: «¿Qué es un ROLLBACK?» → «que es un rollback»."""
    sin_tildes = "".join(c for c in unicodedata.normalize("NFD", text.lower()) if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9ñ ]", " ", sin_tildes)).strip()


def features(text: str) -> list[str]:
    """Palabras, pares de palabras y trigramas de letras (estos últimos toleran errores de escritura)."""
    palabras = normalize(text).split()
    rasgos = [f"w:{p}" for p in palabras]
    rasgos += [f"b:{a}_{b}" for a, b in zip(palabras, palabras[1:], strict=False)]
    for p in palabras:
        marcada = f"^{p}$"
        rasgos += [f"c:{marcada[i:i + 3]}" for i in range(len(marcada) - 2)]
    return rasgos


@dataclass(frozen=True)
class Decision:
    """Resultado de la compuerta para una pregunta."""

    label: str
    p_fuera_de_tema: float
    despertar_llm: bool
    model_version: str


class GateModel:
    """Naive Bayes multinomial con suavizado de Laplace, cargado desde el JSON exportado."""

    def __init__(self, data: dict):
        self.version: str = data["version"]
        self.priors: dict[str, float] = data["priors"]
        self.counts: dict[str, dict[str, int]] = data["counts"]
        self.totals: dict[str, int] = data["totals"]
        self.vocab_size: int = data["vocab_size"]
        self.threshold: float = data["threshold"]
        # Vocabulario propio de la aplicación (ticket, SLA, rollback…): si aparece, la pregunta es del tema
        self.lexicon: frozenset[str] = frozenset(normalize(t) for t in data.get("lexicon", []))

    def menciona_la_app(self, text: str) -> bool:
        """Guarda de seguridad: una pregunta con un término de la aplicación nunca se salta al LLM."""
        normal = f" {normalize(text)} "
        return any(f" {term} " in normal for term in self.lexicon)

    def p_fuera_de_tema(self, text: str) -> float:
        rasgos = features(text)
        scores = {}
        for label in ETIQUETAS:
            score = math.log(self.priors[label])
            denom = self.totals[label] + self.vocab_size
            for rasgo in rasgos:
                score += math.log((self.counts[label].get(rasgo, 0) + 1) / denom)
            scores[label] = score
        mayor = max(scores.values())
        exp = {k: math.exp(v - mayor) for k, v in scores.items()}
        return exp[FUERA_DE_TEMA] / sum(exp.values())

    def decide(self, text: str, threshold: float | None = None) -> Decision:
        """Solo se salta al LLM si hay alta seguridad de que es ajena al tema; ante la duda se despierta."""
        limite = self.threshold if threshold is None else threshold
        p = self.p_fuera_de_tema(text)
        fuera = p >= limite and not self.menciona_la_app(text)
        return Decision(FUERA_DE_TEMA if fuera else EN_TEMA, round(p, 4), not fuera, self.version)


class RemoteGate:
    """Compuerta servida por `mlflow models serve` (spec 016): el modelo registrado con el alias `production` responde por HTTP.

    Es la misma decisión que el JSON local, pero el Hub no se despliega para cambiar de modelo: se promueve otra versión en el Model
    Registry y se reinicia el endpoint. Si el endpoint no responde a tiempo o contesta algo inesperado, decide el modelo local: la
    compuerta nunca debe dejar al asistente sin respuesta por una falla de MLOps.
    """

    def __init__(self, url: str, fallback: GateModel, timeout: float = 1.5, label: str = "mlflow:compuerta@production"):
        if not url.lower().startswith(("http://", "https://")):  # sin importar app.integrations: este archivo viaja dentro del modelo de MLflow
            raise ValueError(f"La URL de la compuerta «{url[:60]}» no es http ni https.")
        self.url = url.rstrip("/")
        self.fallback = fallback
        self.timeout = timeout
        self.version = label

    def decide(self, text: str, threshold: float | None = None) -> Decision:
        limite = self.fallback.threshold if threshold is None else threshold
        body = json.dumps({"dataframe_split": {"columns": ["text"], "data": [[text]]}}).encode()
        request = urllib.request.Request(f"{self.url}/invocations", data=body, headers={"Content-Type": "application/json"})
        try:
            # bandit B310: esquema validado en __init__
            with urllib.request.urlopen(request, timeout=self.timeout) as response:  # nosec B310
                fila = json.loads(response.read())["predictions"][0]
            p = float(fila["p_fuera_de_tema"])
        except (urllib.error.URLError, OSError, ValueError, KeyError, IndexError, TypeError) as error:
            logger.warning("Compuerta remota no disponible (%s): decide el modelo local.", error)
            return self.fallback.decide(text, threshold)
        # El umbral y la guarda de vocabulario se aplican aquí con los mismos valores que el modelo local
        fuera = p >= limite and not self.fallback.menciona_la_app(text)
        return Decision(FUERA_DE_TEMA if fuera else EN_TEMA, round(p, 4), not fuera, self.version)


_cached: GateModel | None = None


def load_model(path: Path | None = None) -> GateModel | RemoteGate:
    """Carga el modelo una vez por proceso (el JSON pesa pocos KB); con GATE_MODEL_URL pregunta al endpoint de MLflow."""
    global _cached
    if path is not None:
        return GateModel(json.loads(path.read_text(encoding="utf-8")))
    if _cached is None:
        verificar_integridad(MODEL_PATH)
        _cached = GateModel(json.loads(MODEL_PATH.read_text(encoding="utf-8")))
    from app.config import settings  # import tardío: el módulo se usa también fuera del Hub (ai/classifier)

    return RemoteGate(settings.gate_model_url, _cached) if settings.gate_model_url else _cached

# Utilidades compartidas por los scripts de MLOps/LLMOps de ai/ (spec 012): conectar con MLflow, huella de los datos,
# commit de Git y digest del modelo de Ollama. Cada corrida queda ligada a sus datos, su código y su modelo.
# MLflow es opcional: si no está instalado o el servidor no responde, los scripts siguen y guardan un JSON en runs/.
import hashlib
import json
import os
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def mlflow_available() -> bool:
    """True si MLflow está instalado. No dice si el servidor responde: eso lo descubre `iniciar`."""
    try:
        import mlflow  # noqa: F401
    except ImportError:
        return False
    return True


def start_run(experimento: str):
    """Fija el experimento y devuelve el módulo `mlflow`, o None (con el motivo en pantalla) si no se puede usar."""
    try:
        import mlflow
    except ImportError:
        return None
    # Con el servidor caído, MLflow reintenta durante minutos por defecto: aquí se falla rápido y se guarda el JSON
    os.environ.setdefault("MLFLOW_HTTP_REQUEST_MAX_RETRIES", "1")
    os.environ.setdefault("MLFLOW_HTTP_REQUEST_TIMEOUT", "10")
    try:
        mlflow.set_experiment(experimento)
    except Exception as error:  # noqa: BLE001 - servidor caído, sin red, host no permitido...
        print(f"  (MLflow no respondió: {str(error)[:160]}; se guarda solo el JSON de la corrida)")
        return None
    return mlflow


def fingerprint(rutas: list[Path]) -> str:
    """SHA-256 corto del contenido de los archivos, en orden: identifica la versión exacta de unos datos."""
    h = hashlib.sha256()
    for ruta in sorted(rutas):
        h.update(ruta.name.encode("utf-8"))
        h.update(ruta.read_bytes())
    return h.hexdigest()[:16]


def git_commit() -> str:
    """Commit actual del repositorio (con `+` si hay cambios sin guardar), o «desconocido» fuera de Git.

    Dentro de un contenedor sin git se puede pasar el commit en la variable GIT_COMMIT.
    """
    if os.environ.get("GIT_COMMIT"):
        return os.environ["GIT_COMMIT"]
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True, timeout=10, check=True
        ).stdout.strip()
        sucio = subprocess.run(
            ["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True, timeout=10, check=True
        ).stdout.strip()
        return sha + ("+" if sucio else "")
    except (OSError, subprocess.SubprocessError):
        return "desconocido"


def model_digest(url: str, nombre: str) -> str:
    """Digest del modelo en Ollama (`/api/tags`): fija con qué pesos exactos se midió. «desconocido» si no responde."""
    try:
        # bandit B310: herramienta de desarrollo: la URL de Ollama la pone quien la corre
        with urllib.request.urlopen(f"{url}/api/tags", timeout=10) as respuesta:  # nosec B310
            for modelo in json.load(respuesta).get("models", []):
                if nombre.removesuffix(":latest") in (str(modelo.get("name")).removesuffix(":latest"), str(modelo.get("model")).removesuffix(":latest")):
                    return str(modelo.get("digest", "desconocido"))[:12]
    except Exception:  # noqa: BLE001
        pass
    return "desconocido"


def tracking_uri() -> str:
    """Dirección del servidor MLflow que se usa (MLFLOW_TRACKING_URI) o `local` si se guarda en ./mlruns."""
    return os.environ.get("MLFLOW_TRACKING_URI", "local")

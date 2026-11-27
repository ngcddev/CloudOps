# Verifica la integridad de los modelos (spec 020, T05; modelos no confiables del módulo 5): compara el digest de cada modelo que Ollama tiene cargado con el que
# declara su ficha en docs/modelos/ y la suma SHA-256 del clasificador de la compuerta con backend/app/assets/clasificador.sha256. Un modelo cambiado (o reemplazado
# por otro con el mismo nombre) deja de coincidir. Código de salida 1 si algo no coincide.
# Uso:  python ai/verificar_modelos.py [--url http://localhost:11434]      (sin Ollama solo comprueba la compuerta)
import argparse
import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARDS = ROOT / "docs" / "modelos"
CLASSIFIER = ROOT / "backend" / "app" / "assets" / "clasificador.json"
DIGEST = re.compile(r"\| Nombre en Ollama \| `([^`]+)` \|[\s\S]*?\| Digest \| `([0-9a-f]{64})` \|")


FILE_PATTERN = re.compile(r"\| Digest \| `([0-9a-f]{64})` \|\n\| Archivo \| `([^`]+)` \|")


def local_files_from_cards() -> list[tuple[str, Path, str]]:
    """[(nombre de la ficha, archivo del modelo, SHA-256 declarado)] de las fichas que dicen dónde está el archivo (los modelos de voz)."""
    salida = []
    for ficha in sorted(CARDS.glob("*.md")):
        m = FILE_PATTERN.search(ficha.read_text(encoding="utf-8"))
        if m:
            salida.append((ficha.stem, ROOT / m.group(2), m.group(1)))
    return salida


def check_local_files() -> tuple[list[str], list[str]]:
    """(coinciden, problemas): el SHA-256 de cada archivo de modelo que está en el equipo contra el de su ficha; el que no se descargó se omite."""
    coinciden, problemas = [], []
    for nombre, ruta, esperado in local_files_from_cards():
        if not ruta.exists():
            continue
        real = hashlib.sha256(ruta.read_bytes()).hexdigest()
        (coinciden if real == esperado else problemas).append(nombre if real == esperado else f"{nombre}: {ruta.name} no coincide con el SHA-256 de su ficha")
    return coinciden, problemas


def digests_from_cards() -> dict[str, str]:
    """{nombre del modelo en Ollama: digest declarado en su ficha}."""
    salida = {}
    for ficha in sorted(CARDS.glob("*.md")):
        m = DIGEST.search(ficha.read_text(encoding="utf-8"))
        if m:
            salida[m.group(1)] = m.group(2)
    return salida


def compare(declarados: dict[str, str], reales: dict[str, str]) -> tuple[list[str], list[str]]:
    """(coinciden, problemas). Un modelo declarado que Ollama no tiene se informa, no se da por bueno."""
    coinciden, problemas = [], []
    sin_latest = {nombre.removesuffix(":latest"): digest for nombre, digest in reales.items()}
    for nombre, esperado in declarados.items():
        real = sin_latest.get(nombre.removesuffix(":latest"))
        if real is None:
            problemas.append(f"{nombre}: Ollama no lo tiene instalado (no se puede verificar)")
        elif real != esperado:
            problemas.append(f"{nombre}: el digest cambió (ficha {esperado[:12]}…, Ollama {real[:12]}…)")
        else:
            coinciden.append(nombre)
    return coinciden, problemas


def check_classifier(ruta: Path = CLASSIFIER) -> str | None:
    """None si coincide con su suma; el problema, si no."""
    suma = ruta.with_suffix(".sha256")
    if not suma.exists():
        return f"falta {suma.name}"
    if hashlib.sha256(ruta.read_bytes()).hexdigest() != suma.read_text(encoding="utf-8").split()[0]:
        return f"{ruta.name} no coincide con {suma.name}"
    return None


def ollama_digests(url: str) -> dict[str, str]:
    # bandit B310: herramienta de desarrollo: la URL de Ollama la pone quien la corre
    with urllib.request.urlopen(f"{url}/api/tags", timeout=15) as respuesta:  # nosec B310
        return {m["name"]: m.get("digest", "") for m in json.load(respuesta).get("models", [])}


def main() -> int:
    """Compara los digests de Ollama y la suma de la compuerta con los de las fichas; sale con 1 si algo no coincide."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--url", default="http://localhost:11434")
    args = ap.parse_args()
    problemas = []

    problema = check_classifier()
    print(f"{'✓' if problema is None else '✗'} compuerta: {problema or 'el clasificador coincide con su suma SHA-256'}")
    if problema:
        problemas.append(problema)

    try:
        coinciden, fallos = compare(digests_from_cards(), ollama_digests(args.url))
    except Exception as error:  # noqa: BLE001
        print(f"- Ollama no respondió ({str(error)[:100]}): no se verificaron los modelos de lenguaje")
    else:
        for nombre in coinciden:
            print(f"✓ {nombre}: el digest coincide con su ficha")
        for fallo in fallos:
            print(f"✗ {fallo}")
        problemas += fallos

    locales, fallos_locales = check_local_files()
    for nombre in locales:
        print(f"✓ {nombre}: el archivo del modelo coincide con el SHA-256 de su ficha")
    for fallo in fallos_locales:
        print(f"✗ {fallo}")
    problemas += fallos_locales
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())

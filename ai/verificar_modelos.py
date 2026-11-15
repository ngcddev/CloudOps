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

RAIZ = Path(__file__).resolve().parents[1]
FICHAS = RAIZ / "docs" / "modelos"
CLASIFICADOR = RAIZ / "backend" / "app" / "assets" / "clasificador.json"
DIGEST = re.compile(r"\| Nombre en Ollama \| `([^`]+)` \|[\s\S]*?\| Digest \| `([0-9a-f]{64})` \|")


def digests_de_las_fichas() -> dict[str, str]:
    """{nombre del modelo en Ollama: digest declarado en su ficha}."""
    salida = {}
    for ficha in sorted(FICHAS.glob("*.md")):
        m = DIGEST.search(ficha.read_text(encoding="utf-8"))
        if m:
            salida[m.group(1)] = m.group(2)
    return salida


def comparar(declarados: dict[str, str], reales: dict[str, str]) -> tuple[list[str], list[str]]:
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


def verificar_clasificador(ruta: Path = CLASIFICADOR) -> str | None:
    """None si coincide con su suma; el problema, si no."""
    suma = ruta.with_suffix(".sha256")
    if not suma.exists():
        return f"falta {suma.name}"
    if hashlib.sha256(ruta.read_bytes()).hexdigest() != suma.read_text(encoding="utf-8").split()[0]:
        return f"{ruta.name} no coincide con {suma.name}"
    return None


def digests_de_ollama(url: str) -> dict[str, str]:
    # bandit B310: herramienta de desarrollo: la URL de Ollama la pone quien la corre
    with urllib.request.urlopen(f"{url}/api/tags", timeout=15) as respuesta:  # nosec B310
        return {m["name"]: m.get("digest", "") for m in json.load(respuesta).get("models", [])}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--url", default="http://localhost:11434")
    args = ap.parse_args()
    problemas = []

    problema = verificar_clasificador()
    print(f"{'✓' if problema is None else '✗'} compuerta: {problema or 'el clasificador coincide con su suma SHA-256'}")
    if problema:
        problemas.append(problema)

    try:
        coinciden, fallos = comparar(digests_de_las_fichas(), digests_de_ollama(args.url))
    except Exception as error:  # noqa: BLE001
        print(f"- Ollama no respondió ({str(error)[:100]}): no se verificaron los modelos de lenguaje")
    else:
        for nombre in coinciden:
            print(f"✓ {nombre}: el digest coincide con su ficha")
        for fallo in fallos:
            print(f"✗ {fallo}")
        problemas += fallos
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())

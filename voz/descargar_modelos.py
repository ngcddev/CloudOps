# Descarga los modelos del servicio de voz (spec 021, T01) con la suma SHA-256 fijada: un archivo que no coincide se borra y falla. Los modelos NO van en Git.
#   · voz a texto: faster-whisper (Systran, licencia MIT) en la revisión fijada de Hugging Face; `small` (484 MB, por defecto, el que mejor transcribe la jerga del Hub) o `base` (145 MB)
#   · texto a voz: Piper, voz es_MX «claude» calidad alta (licencia apache-2.0, 63 MB), en la revisión fijada del repositorio de voces
# Los archivos grandes llevan su SHA-256 (el `oid` LFS de Hugging Face); los pequeños (configuración, vocabulario) vienen de la misma revisión fija.
# Uso:  python voz/descargar_modelos.py <carpeta> [--whisper base|small]
import argparse
import hashlib
import sys
import urllib.request
from pathlib import Path

HF = "https://huggingface.co"
WHISPER = {
    "base": ("Systran/faster-whisper-base", "ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66", "d01c3014881c9c6f3133c182f3d2887eb6ca1c789a7538c5c007196857a0a6a9"),
    "small": ("Systran/faster-whisper-small", "536b0662742c02347bc0e980a01041f333bce120", "3e305921506d8872816023e4c273e75d2419fb89b24da97b4fe7bce14170d671"),
}
WHISPER_FILES = ["config.json", "tokenizer.json", "vocabulary.txt", "model.bin"]
PIPER_REV = "6b9cfaacb4fb2e02a9621227e3c1a48bec9710c3"
PIPER_BASE = f"{HF}/rhasspy/piper-voices/resolve/{PIPER_REV}/es/es_MX/claude/high/es_MX-claude-high"
PIPER_ONNX_SHA256 = "3ef40a71ea63852cd8ab7e6fa7d2ecdcfa67a0b47c9c48e3f10e02ee02083ea0"


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def download(url: str, destino: Path, esperado: str | None) -> None:
    """Descarga `url` a `destino`; con `esperado`, comprueba el SHA-256 (si ya está y coincide no vuelve a bajar)."""
    if destino.exists() and (esperado is None or sha256(destino) == esperado):
        print(f"  ya está: {destino.name}")
        return
    destino.parent.mkdir(parents=True, exist_ok=True)
    print(f"  bajando {destino.name}…", flush=True)
    if not url.startswith("https://"):
        raise ValueError(f"solo se descarga por HTTPS: {url}")
    # bandit B310: el esquema se validó arriba (solo https)
    urllib.request.urlretrieve(url, destino)  # nosec B310
    if esperado is not None and sha256(destino) != esperado:
        destino.unlink()
        raise SystemExit(f"ERROR: {destino.name} no coincide con su suma SHA-256: se borró.")


def main() -> int:
    """Descarga los modelos de voz a la carpeta indicada y verifica sus sumas."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("carpeta", type=Path)
    ap.add_argument("--whisper", choices=sorted(WHISPER), default="small")
    args = ap.parse_args()

    repo, revision, suma = WHISPER[args.whisper]
    print(f"Voz a texto: {repo}")
    for archivo in WHISPER_FILES:
        download(f"{HF}/{repo}/resolve/{revision}/{archivo}", args.carpeta / f"whisper-{args.whisper}" / archivo, suma if archivo == "model.bin" else None)
    print("Texto a voz: Piper es_MX-claude-high")
    download(f"{PIPER_BASE}.onnx", args.carpeta / "piper" / "voz.onnx", PIPER_ONNX_SHA256)
    download(f"{PIPER_BASE}.onnx.json", args.carpeta / "piper" / "voz.onnx.json", None)
    print("Modelos listos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

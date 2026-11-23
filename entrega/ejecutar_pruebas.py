#!/usr/bin/env python3
# Ejecuta, por cada prueba funcional (PF) de entrega/datos/pruebas.csv, sus archivos de pytest en el contenedor `api`
# y escribe el resultado obtenido y el estado. Uso (con `docker compose up` en marcha): python entrega/ejecutar_pruebas.py
import csv
import datetime
import os
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CSV = RAIZ / "entrega" / "datos" / "pruebas.csv"


def correr(archivos: list[str]) -> tuple[str, str]:
    rutas = [f"tests/{a}" for a in archivos]
    # Las pruebas suponen el modo de contexto por defecto (`completo`); el .env local usa `rag`, así que se fija como en la CI.
    cmd = ["docker", "compose", "exec", "-T", "-e", "ASSISTANT_CONTEXT_MODE=completo", "api", "pytest", "-q", "-p", "no:cacheprovider", *rutas]
    env = {**os.environ, "MSYS_NO_PATHCONV": "1"}
    p = subprocess.run(cmd, cwd=RAIZ, capture_output=True, text=True, env=env, timeout=900)
    resumen = [lin for lin in p.stdout.strip().splitlines() if re.search(r"\b(passed|failed|error|no tests ran)\b", lin)]
    ultima = resumen[-1] if resumen else (p.stdout.strip().splitlines() or ["sin salida"])[-1]
    ultima = re.sub(r"\s+in\s+[\d.]+s.*$", "", ultima).replace("=", "").strip()
    pasaron = re.search(r"(\d+) passed", ultima)
    falla = re.search(r"(\d+) (failed|error)", ultima)
    if p.returncode == 0 and pasaron and not falla:
        n = pasaron.group(1)
        omit = re.search(r"(\d+) skipped", ultima)
        texto = f"{n} pasaron" + (f", {omit.group(1)} omitidas" if omit else "")
        return texto, "Cumplido"
    return ultima, "Fallido"


def main() -> int:
    with CSV.open(encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f, delimiter=";"))
        campos = list(filas[0].keys())
    hoy = datetime.date.today().strftime("%d/%m/%Y")
    fallidas = 0
    for fila in filas:
        archivos = fila["pruebas"].split()
        if archivos and archivos[0].startswith("ai/"):
            # Las pruebas de ai/ corren con `cd ai && pytest` en un entorno aparte (ai/requirements.txt); su resultado se anota a mano.
            print("·", fila["pf"], "se conserva:", fila["obtenido"])
            continue
        faltan = [a for a in archivos if not (RAIZ / "backend" / "tests" / a).exists()]
        if faltan:
            print(f"✗ {fila['pf']}: no existen {faltan}")
            fila["obtenido"], fila["estado"] = f"faltan archivos: {' '.join(faltan)}", "Fallido"
            fallidas += 1
            continue
        obtenido, estado = correr(archivos)
        fila["obtenido"] = f"{obtenido} ({hoy})"
        fila["estado"] = estado
        print(("✓" if estado == "Cumplido" else "✗"), fila["pf"], fila["obtenido"])
        fallidas += estado != "Cumplido"
    with CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos, delimiter=";", lineterminator="\n")
        w.writeheader()
        w.writerows(filas)
    return 1 if fallidas else 0


if __name__ == "__main__":
    sys.exit(main())

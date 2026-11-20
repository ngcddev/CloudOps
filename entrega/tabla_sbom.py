# Genera la tabla del SBOM (componente, versión, licencia, origen y restricción) a partir de los JSON de Syft.
# Uso: python entrega/tabla_sbom.py entrega/evidencias/sbom-2026-11-18
# Escribe en esa carpeta: tabla-sbom.md (para el complementario 06) y tabla-sbom.csv (para el Apéndice D).
import collections
import csv
import json
import pathlib
import sys

IMAGENES = {
    "hub-api_v1.17": "hub-api:v1.17",
    "hub-api_v1.18": "hub-api:v1.18",
    "hub-voz_v1.2": "hub-voz:v1.2",
    "hub-web_v1.12": "hub-web:v1.12",
}


# Licencias que Syft no detecta en los metadatos y se toman de lo que declara el proyecto.
DECLARADAS = {"tokenizers": "Apache-2.0 (declarada por el proyecto; Syft no la detectó)"}


def restriccion(licencia: str) -> str:
    """Obligación principal según la familia de la licencia."""
    lic = licencia.upper()
    if "AGPL" in lic:
        return "Copyleft de red: publicar cambios si se ofrece como servicio"
    if "LGPL" in lic:
        return "Uso como biblioteca; permitir reemplazarla"
    if "GPL" in lic:
        return "Copyleft: distribuir la imagen con su código fuente"
    if "MPL" in lic:
        return "Copyleft por archivo: publicar cambios a esos archivos"
    if not licencia or licencia == "(sin dato)":
        return "Revisar: Syft no detectó la licencia"
    return "Conservar el aviso de licencia"


def licencias_de(art: dict) -> str:
    vals = sorted({x["value"] for x in art.get("licenses", [])})
    return " / ".join(vals) if vals else "(sin dato)"


def main(carpeta: pathlib.Path) -> None:
    filas = {}  # (nombre, versión) -> datos, para no repetir lo que está en dos imágenes
    resumen = []
    for f in sorted(carpeta.glob("*.syft.json")):
        clave = f.name.replace(".syft.json", "")
        imagen = IMAGENES.get(clave, clave)
        arts = json.loads(f.read_text(encoding="utf-8"))["artifacts"]
        tipos = collections.Counter(a["type"] for a in arts)
        copyleft = sum(1 for a in arts if any(k in licencias_de(a).upper() for k in ("GPL", "MPL")))
        resumen.append((imagen, len(arts), tipos, copyleft))
        for a in arts:
            if a["type"] not in ("python", "npm"):
                continue  # los paquetes del sistema (deb, apk) van resumidos, no uno por uno
            k = (a["name"].lower(), a["version"])
            lic = licencias_de(a)
            if lic == "(sin dato)" and a["name"].lower() in DECLARADAS:
                lic = DECLARADAS[a["name"].lower()]
            if k in filas:
                filas[k]["origen"].add(imagen)
            else:
                filas[k] = {"componente": a["name"], "version": a["version"], "licencia": lic,
                            "tipo": a["type"], "origen": {imagen}, "restriccion": restriccion(lic)}

    ordenadas = sorted(filas.values(), key=lambda r: r["componente"].lower())
    with open(carpeta / "tabla-sbom.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["componente", "version", "licencia", "tipo", "origen", "restriccion"])
        for r in ordenadas:
            w.writerow([r["componente"], r["version"], r["licencia"], r["tipo"], ", ".join(sorted(r["origen"])), r["restriccion"]])

    md = ["| Imagen | Paquetes | Por tipo | Con licencia copyleft (GPL, LGPL, MPL) |", "|---|---|---|---|"]
    for imagen, n, tipos, cop in resumen:
        md.append(f"| {imagen} | {n} | {', '.join(f'{t}: {c}' for t, c in sorted(tipos.items()))} | {cop} |")
    md += ["", "| Componente | Versión | Licencia | Origen | Restricción |", "|---|---|---|---|---|"]
    for r in ordenadas:
        md.append(f"| {r['componente']} | {r['version']} | {r['licencia']} | {', '.join(sorted(r['origen']))} | {r['restriccion']} |")
    (carpeta / "tabla-sbom.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"{len(ordenadas)} componentes de aplicación; tablas en {carpeta}")


if __name__ == "__main__":
    main(pathlib.Path(sys.argv[1]))

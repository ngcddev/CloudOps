#!/usr/bin/env python3
# Ensambla las secciones en el orden del informe y numera tablas y figuras según su posición (spec 023).
# En las secciones se escribe `**Tabla {T:clave}**` en la leyenda y `{T:clave}` en las referencias del texto
# (igual con `{F:clave}` para figuras): así agregar una tabla no obliga a renumerar a mano.
# Uso: python entrega/preprocesar.py salida.md        (sin argumento escribe en entrega/.combinado.md)
import os
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
# INFORME_DIR elige la carpeta de secciones (por defecto el borrador 00-informe; el informe final se escribe en entrega/informe)
SECCIONES = AQUI / os.environ.get("INFORME_DIR", "00-informe")


def orden() -> list[Path]:
    """Orden APA: la portada (02) antes que la ficha (01); el resto por número."""
    todas = sorted(SECCIONES.glob("[0-9][0-9]-*.md"))
    por = {int(a.name[:2]): a for a in todas}
    primeras = [por[n] for n in (2, 1) if n in por]
    return primeras + [a for n, a in sorted(por.items()) if n not in (1, 2)]


def celdas(linea: str) -> list[str]:
    """Celdas de una fila de tabla de pipes; respeta `\\|` como texto y no como separador."""
    partes = re.split(r"(?<!\\)\|", linea.strip())
    return [c.strip() for c in partes[1:-1]]


def ajustar_columnas(texto: str) -> str:
    """Pandoc reparte el ancho de la tabla según los guiones de la fila separadora. Aquí se garantiza que cada columna sea al menos tan ancha como su
    palabra más larga (un «RF-01» o un «Prio.» no se parten letra por letra) sin tocar el reparto que ya funciona."""
    lineas = texto.split("\n")
    i = 0
    while i < len(lineas) - 1:
        if lineas[i].startswith("|") and re.fullmatch(r"\|[-: |]+\|", lineas[i + 1].strip()):
            fin = i + 2
            while fin < len(lineas) and lineas[fin].startswith("|"):
                fin += 1
            filas = [celdas(lineas[k]) for k in [i] + list(range(i + 2, fin))]
            n = len(celdas(lineas[i + 1]))
            pesos = [len(c) for c in celdas(lineas[i + 1])]
            palabras = [1] * n
            for f in filas:
                for j, c in enumerate(f[:n]):
                    limpio = re.sub(r"[`*_\\]", "", c)
                    mayor = max((len(p) for p in limpio.split()), default=1)
                    palabras[j] = max(palabras[j], min(mayor, 24))
            for _ in range(6):
                total = sum(pesos)
                nuevos = [max(p, round((palabras[j] + 3) * total / 90)) for j, p in enumerate(pesos)]
                if nuevos == pesos:
                    break
                pesos = nuevos
            lineas[i + 1] = "|" + "|".join("-" * max(3, p) for p in pesos) + "|"
            i = fin
        else:
            i += 1
    return "\n".join(lineas)


def combinar() -> tuple[str, list[str]]:
    texto = "\n\n".join(a.read_text(encoding="utf-8") for a in orden())
    problemas: list[str] = []
    for letra, rotulo in (("T", "Tabla"), ("F", "Figura")):
        claves: list[str] = []
        for m in re.finditer(rf"\*\*{rotulo} \{{{letra}:([\w-]+)\}}\*\*", texto):
            if m.group(1) in claves:
                problemas.append(f"leyenda repetida: {rotulo} {{{letra}:{m.group(1)}}}")
            else:
                claves.append(m.group(1))
        numeros = {c: i + 1 for i, c in enumerate(claves)}
        for m in re.finditer(rf"\{{{letra}:([\w-]+)\}}", texto):
            if m.group(1) not in numeros:
                problemas.append(f"referencia sin leyenda: {{{letra}:{m.group(1)}}}")
        texto = re.sub(rf"\{{{letra}:([\w-]+)\}}", lambda m, numeros=numeros: str(numeros.get(m.group(1), "?")), texto)
    return ajustar_columnas(texto), problemas


if __name__ == "__main__":
    salida = Path(sys.argv[1]) if len(sys.argv) > 1 else AQUI / ".combinado.md"
    texto, problemas = combinar()
    for p in problemas:
        print("✗", p)
    salida.write_text(texto, encoding="utf-8")
    sys.exit(1 if problemas else 0)

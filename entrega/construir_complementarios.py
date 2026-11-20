# Construye los complementarios de la entrega final desde Entrega_Final_CloudForge/0*.md:
#   .docx (01, 03, 05, 06) con pandoc en Docker y la plantilla APA (entrega/plantilla.docx);
#   .xlsx (02, 04) con una hoja por sección y los anexos A (diccionario) y D (SBOM de Syft).
# Uso: python entrega/construir_complementarios.py   (requiere Docker y openpyxl)
import csv
import os
import pathlib
import re
import subprocess

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

RAIZ = pathlib.Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "Entrega_Final_CloudForge"
ANEXOS = SALIDA / "anexos"
DOCX = ["01_Ficha_Proyecto", "03_Plan_Pruebas_Validacion_IA", "05_Runbook_Operacion", "06_Analisis_Riesgos_y_Seguridad"]
XLSX = ["02_Matriz_Trazabilidad", "04_Bitacora_IA"]
HORIZONTAL = {"03_Plan_Pruebas_Validacion_IA", "06_Analisis_Riesgos_y_Seguridad"}  # tablas anchas
VERDE = PatternFill("solid", fgColor="E8F5E9")


def limpiar(celda: str) -> str:
    """Quita el formato Markdown de una celda (negritas, cursivas y código)."""
    celda = re.sub(r"\*\*(.+?)\*\*", r"\1", celda)
    celda = re.sub(r"(?<!\w)\*(.+?)\*(?!\w)", r"\1", celda)
    return celda.replace("`", "").strip()


def tablas_por_seccion(md: str):
    """Devuelve [(título de sección, encabezados, filas)] para cada tabla del Markdown."""
    seccion, salida, bloque = "Tabla", [], []
    for linea in md.splitlines() + [""]:
        if linea.startswith("#"):
            seccion = linea.lstrip("# ").strip()
        if linea.strip().startswith("|"):
            bloque.append(linea.strip())
            continue
        if bloque:
            filas = [[limpiar(c) for c in f.strip("|").split("|")] for f in bloque if not re.fullmatch(r"\|[-:| ]+\|", f)]
            salida.append((seccion, filas[0], filas[1:]))
            bloque = []
    return salida


def hoja(wb, nombre: str, encabezados, filas, fuente: str = ""):
    ws = wb.create_sheet(re.sub(r"[\\/*?:\[\]]", "", nombre)[:31])
    fila0 = 1
    if fuente:
        ws.cell(1, 1, fuente).font = Font(italic=True, size=9)
        fila0 = 3
    for j, h in enumerate(encabezados, 1):
        c = ws.cell(fila0, j, h)
        c.font = Font(bold=True)
        c.fill = VERDE
        c.alignment = Alignment(wrap_text=True, vertical="top")
    for i, f in enumerate(filas, fila0 + 1):
        for j, v in enumerate(f, 1):
            ws.cell(i, j, v).alignment = Alignment(wrap_text=True, vertical="top")
    for j, h in enumerate(encabezados, 1):
        largo = max([len(str(h))] + [len(str(f[j - 1])) for f in filas if j - 1 < len(f)])
        ws.column_dimensions[get_column_letter(j)].width = min(max(12, largo * 0.9), 60)
    ws.freeze_panes = ws.cell(fila0 + 1, 1)
    ws.auto_filter.ref = f"A{fila0}:{get_column_letter(len(encabezados))}{fila0 + len(filas)}"


def construir_xlsx(nombre: str):
    md = (SALIDA / f"{nombre}.md").read_text(encoding="utf-8")
    nota = next((ln.lstrip("> ").strip() for ln in md.splitlines() if ln.startswith(">")), "")
    wb = Workbook()
    wb.remove(wb.active)
    usados = {}
    for seccion, enc, filas in tablas_por_seccion(md):
        titulo = re.sub(r"^\d+(\.\d+)?\.?\s*", "", seccion) or "Tabla"
        usados[titulo] = usados.get(titulo, 0) + 1
        if usados[titulo] > 1:
            titulo = f"{titulo[:27]} ({usados[titulo]})"
        hoja(wb, titulo, enc, filas, limpiar(nota) if not wb.sheetnames else "")
    wb.save(SALIDA / f"{nombre}.xlsx")
    print(f"✓ {nombre}.xlsx ({len(wb.sheetnames)} hojas)")


def construir_anexo_csv(origen: pathlib.Path, destino: str, titulo: str, fuente: str):
    with open(origen, encoding="utf-8") as fh:
        filas = list(csv.reader(fh, delimiter=";"))
    wb = Workbook()
    wb.remove(wb.active)
    hoja(wb, titulo, filas[0], filas[1:], fuente)
    wb.save(ANEXOS / destino)
    print(f"✓ anexos/{destino} ({len(filas) - 1} filas)")


def construir_docx(nombre: str):
    montaje = str(RAIZ)
    cmd = ["docker", "run", "--rm", "-v", f"{montaje}:/w", "-w", "/w", "pandoc/core:3.6",
           "--from", "markdown+pipe_tables+lists_without_preceding_blankline", "--to", "docx", "--reference-doc=entrega/plantilla.docx",
           "--metadata", "lang=es-CO", "--metadata", f"pagetitle={nombre}",
           "-o", f"Entrega_Final_CloudForge/{nombre}.docx", f"Entrega_Final_CloudForge/{nombre}.md"]
    subprocess.run(cmd, check=True, env={**os.environ, "MSYS_NO_PATHCONV": "1"})
    if os.name == "nt":  # formato final con Word (solo en Windows, que es donde está Word)
        horizontal = "1" if nombre in HORIZONTAL else "0"
        subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                        str(RAIZ / "entrega" / "formato_docx.ps1"), "-Doc", str(SALIDA / f"{nombre}.docx"),
                        "-Horizontal", horizontal], check=True)
    print(f"✓ {nombre}.docx")


if __name__ == "__main__":
    ANEXOS.mkdir(exist_ok=True)
    for n in DOCX:
        construir_docx(n)
    for n in XLSX:
        construir_xlsx(n)
    construir_anexo_csv(RAIZ / "entrega/datos/diccionario.csv", "Apendice_A_Diccionario_de_datos.xlsx", "Diccionario de datos",
                        "Apéndice A. Generado desde backend/app/models/ con entrega/generar_diccionario.py (commit bb5a284).")
    construir_anexo_csv(RAIZ / "entrega/evidencias/sbom-2026-11-18/tabla-sbom.csv", "Apendice_D_Tabla_SBOM.xlsx", "SBOM Syft",
                        "Apéndice D. Syft v1.55.0 sobre hub-api:v1.17, hub-web:v1.12 y hub-voz:v1.2 (18 nov 2026); "
                        "SBOM completos en entrega/evidencias/sbom-2026-11-18/.")

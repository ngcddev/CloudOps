#!/usr/bin/env bash
# Construye el informe consolidador (.docx) a partir de entrega/00-informe/*.md con pandoc y la plantilla APA 7.
# Uso: bash entrega/construir.sh              genera Entrega_Final_CloudForge/00_Informe_Final_Proyecto_Integrador_CloudForge.docx
#      bash entrega/construir.sh --plantilla  regenera entrega/plantilla.docx antes de construir
# Requiere Docker. Solo escribe en entrega/ y en Entrega_Final_CloudForge/.
set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RAIZ"
# En Git Bash de Windows, Docker necesita la ruta de Windows y sin conversión automática de rutas.
if command -v cygpath >/dev/null 2>&1; then MONTAJE="$(cygpath -w "$RAIZ")"; else MONTAJE="$RAIZ"; fi
export MSYS_NO_PATHCONV=1

PANDOC_IMG="pandoc/core:3.6"
PY_IMG="python:3.12-slim"
SALIDA_DIR="Entrega_Final_CloudForge"
SALIDA="$SALIDA_DIR/00_Informe_Final_Proyecto_Integrador_CloudForge.docx"

if [ "${1:-}" = "--plantilla" ] || [ ! -f entrega/plantilla.docx ]; then
  echo "· generando entrega/plantilla.docx (estilos APA 7)"
  docker run --rm --entrypoint sh -v "$MONTAJE:/w" "$PANDOC_IMG" \
    -c "pandoc --print-default-data-file reference.docx > /w/entrega/.base.docx"
  docker run --rm -v "$MONTAJE:/w" -w /w "$PY_IMG" sh -c \
    "pip install -q python-docx==1.1.2 >/dev/null 2>&1 && python entrega/crear_plantilla.py entrega/.base.docx entrega/plantilla.docx"
  rm -f entrega/.base.docx
fi

mkdir -p "$SALIDA_DIR"
# Ensambla en orden APA (portada antes que ficha) y numera tablas y figuras por su posición.
export INFORME_DIR="${INFORME_DIR:-informe}"   # carpeta de secciones: entrega/informe (el informe final); INFORME_DIR=00-informe construye el borrador
python entrega/preprocesar.py entrega/.combinado.md 2>/dev/null || python3 entrega/preprocesar.py entrega/.combinado.md

echo "· construyendo con pandoc"
docker run --rm -v "$MONTAJE:/w" -w /w "$PANDOC_IMG"   --from markdown+pipe_tables+fenced_divs+raw_attribute   --to docx --reference-doc=entrega/plantilla.docx   --metadata lang=es-CO --metadata pagetitle="Informe final CloudForge"   -o "$SALIDA" entrega/.combinado.md

echo "✓ $SALIDA ($(du -h "$SALIDA" | cut -f1))"

#!/usr/bin/env bash
# Registro de hallazgos de las imágenes (spec 018, T02): construye las imágenes del Hub (API y frontend) y del sitio de ejemplo (colegio), las escanea con Trivy mostrando también lo que
# NO tiene arreglo, y cruza el resultado con pipelines/hallazgos.yaml (pipelines/hallazgos.py). Deja en evidencias/hallazgos/ la tabla del registro, el JSON y el VEX (OpenVEX).
# Frena si hay un hallazgo corregible, sin decisión o con la decisión vencida.
# Uso:  bash pipelines/pruebas/hallazgos.sh [imagen-ya-construida ...]      (sin argumentos construye las cuatro imágenes de arriba)
set -uo pipefail
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TRIVY_IMAGE="${TRIVY_IMAGE:-aquasec/trivy:0.76.1}"
export MSYS_NO_PATHCONV=1
ruta_docker() { (cd "$1" && (pwd -W 2>/dev/null || pwd)); }
SALIDA="$RAIZ/evidencias/hallazgos"
rm -rf "$SALIDA"; mkdir -p "$SALIDA"
SALIDA_D="$(ruta_docker "$SALIDA")"
RAIZ_D="$(ruta_docker "$RAIZ")"

imagenes=("$@")
if [ "${#imagenes[@]}" -eq 0 ]; then
  echo "→ Construyendo las imágenes"
  docker build -q --build-context seed="$RAIZ_D/seed" -t hub-api:hallazgos "$RAIZ_D/backend" >/dev/null || { echo "no se pudo construir hub-api" >&2; exit 1; }
  docker build -q --build-context seed="$RAIZ_D/seed" -t hub-web:hallazgos "$RAIZ_D/frontend" >/dev/null || { echo "no se pudo construir hub-web" >&2; exit 1; }
  docker build -q -f "$RAIZ_D/apps/colegio/Dockerfile.frontend" -t colegio-web:hallazgos "$RAIZ_D/apps/colegio" >/dev/null || { echo "no se pudo construir colegio-web" >&2; exit 1; }
  docker build -q -f "$RAIZ_D/apps/colegio/Dockerfile.backend" -t colegio-api:hallazgos "$RAIZ_D/apps/colegio" >/dev/null || { echo "no se pudo construir colegio-api" >&2; exit 1; }
  imagenes=(hub-api:hallazgos hub-web:hallazgos colegio-web:hallazgos colegio-api:hallazgos)
fi

echo "→ Escaneando con Trivy (altas y críticas, también sin arreglo)"
reportes=()
for imagen in "${imagenes[@]}"; do
  nombre="$(echo "$imagen" | tr '/:' '__')"
  docker save "$imagen" -o "$SALIDA_D/${nombre}.tar" || { echo "no se pudo guardar $imagen" >&2; exit 1; }
  docker run --rm -v "$SALIDA_D:/out" -v puerta-trivy-cache:/root/.cache "$TRIVY_IMAGE" image --input "/out/${nombre}.tar" --severity HIGH,CRITICAL --quiet \
    --format json --output "/out/${nombre}.json" >/dev/null 2>&1 || { echo "Trivy no pudo revisar $imagen" >&2; exit 1; }
  rm -f "$SALIDA/${nombre}.tar"
  reportes+=("/out/${nombre}.json")
done

echo "→ Cruzando con pipelines/hallazgos.yaml"
docker run --rm -v "$RAIZ_D:/repo:ro" -v "$SALIDA_D:/out" -w /repo python:3.12-slim sh -c \
  "pip install -q pyyaml >/dev/null 2>&1 && python pipelines/hallazgos.py --salida /out ${reportes[*]}"
codigo=$?
echo
[ "$codigo" -eq 0 ] && echo "Registro de hallazgos al día: todo lo corregible está corregido y lo demás tiene decisión vigente. Resultado en evidencias/hallazgos/." || echo "Hay hallazgos sin resolver."
exit "$codigo"

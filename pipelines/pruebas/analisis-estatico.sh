#!/usr/bin/env bash
# Análisis estático y de composición del código (spec 018, T01), todo en contenedores: no instala nada en el equipo.
#   1. SAST        bandit sobre el código de Python (Hub, sitios de los clientes, ai/ y voz/): frena con hallazgos de severidad media o alta
#   2. SCA         trivy fs sobre las dependencias declaradas (requirements.txt y package-lock.json): frena con vulnerabilidades altas o críticas
#   3. Imagen web  construye la imagen del frontend y la escanea con Trivy: frena con críticas que ya tienen arreglo (la imagen del Hub API se escanea aparte en el CI)
# Las excepciones van en el código (`# nosec Bxxx` con su razón en la línea de arriba) o en .trivyignore.yaml / vex/ con razón y vencimiento; nunca en este script.
# Uso:  bash pipelines/pruebas/analisis-estatico.sh [sast|sca|imagen|todo]      (por defecto, todo)
set -uo pipefail
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BANDIT_IMAGE="${BANDIT_IMAGE:-python:3.12-slim}"
TRIVY_IMAGE="${TRIVY_IMAGE:-aquasec/trivy:0.76.1}"
export MSYS_NO_PATHCONV=1
ruta_docker() { (cd "$1" && (pwd -W 2>/dev/null || pwd)); }
fallos=0
ok()    { echo "   OK   $1"; }
falla() { echo "   FALLA $1"; fallos=$((fallos+1)); }
RAIZ_D="$(ruta_docker "$RAIZ")"

sast() {
  echo "== SAST: bandit (severidad media o alta)"
  docker run --rm -v "${RAIZ_D}:/w:ro" -w /w "$BANDIT_IMAGE" sh -c \
    "pip install -q bandit >/dev/null 2>&1 && bandit -r -ll backend/app apps/consultorio/backend/app apps/colegio/backend/app ai voz -x '**/tests/**,**/eval/runs/**' 2>&1 | grep -E 'Issue:|Location:|Total issues|Medium:|High:|No issues'; bandit -q -r -ll backend/app apps/consultorio/backend/app apps/colegio/backend/app ai voz -x '**/tests/**,**/eval/runs/**' >/dev/null 2>&1" \
    && ok "bandit no encontró hallazgos de severidad media ni alta" || falla "bandit encontró hallazgos de severidad media o alta"
}

sca() {
  echo "== SCA: dependencias declaradas (trivy fs)"
  if docker run --rm -v "${RAIZ_D}:/src:ro" -v puerta-trivy-cache:/root/.cache "$TRIVY_IMAGE" fs --scanners vuln --severity HIGH,CRITICAL --exit-code 1 --quiet \
      --ignorefile /src/.trivyignore.yaml --skip-dirs '**/node_modules' /src; then
    ok "ninguna dependencia con vulnerabilidades altas o críticas"
  else
    falla "hay dependencias con vulnerabilidades altas o críticas"
  fi
}

imagen() {
  echo "== Imagen del frontend (trivy image)"
  # El tar va en una carpeta del repositorio (ignorada por Git): docker.exe de Windows no ve las rutas /tmp de Git Bash
  local tmp="$RAIZ/evidencias/analisis"; mkdir -p "$tmp"
  docker build -q --build-context seed="$(ruta_docker "$RAIZ/seed")" -t hub-web:analisis "$(ruta_docker "$RAIZ/frontend")" >/dev/null || { falla "no se pudo construir la imagen del frontend"; return; }
  docker save hub-web:analisis -o "$(ruta_docker "$tmp")/hub-web.tar"
  if docker run --rm -v "$(ruta_docker "$tmp"):/out" -v puerta-trivy-cache:/root/.cache "$TRIVY_IMAGE" image --input /out/hub-web.tar --severity CRITICAL --ignore-unfixed --exit-code 1 --quiet; then
    ok "la imagen del frontend no tiene vulnerabilidades críticas con arreglo"
  else
    falla "la imagen del frontend tiene vulnerabilidades críticas con arreglo"
  fi
  rm -rf "$tmp"
}

case "${1:-todo}" in
  sast) sast ;;
  sca) sca ;;
  imagen) imagen ;;
  todo) sast; sca; imagen ;;
  *) echo "Uso: $0 [sast|sca|imagen|todo]" >&2; exit 2 ;;
esac
echo
[ "$fallos" -eq 0 ] && echo "Análisis estático y de composición: sin hallazgos que frenen." || { echo "${fallos} control(es) fallaron."; exit 1; }

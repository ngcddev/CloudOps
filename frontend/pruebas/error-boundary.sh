#!/usr/bin/env bash
# Prueba del ErrorBoundary y de la carga por pantalla en un DOM real (spec 022, T11): compila prueba-error.tsx con esbuild y la corre contra jsdom.
# Todo pasa en un contenedor de Node sobre una copia temporal de frontend/ y seed/; jsdom se instala solo ahí (--no-save), no entra a package.json.
# Uso: bash frontend/pruebas/error-boundary.sh
set -euo pipefail
export MSYS_NO_PATHCONV=1   # Git Bash en Windows: no convertir las rutas de los -v de Docker

RAIZ="$(cd "$(dirname "$0")/../.." && (pwd -W 2>/dev/null || pwd))"
docker run --rm -v "${RAIZ}/frontend:/origen/frontend:ro" -v "${RAIZ}/seed:/origen/seed:ro" node:22-alpine sh -c '
  set -e
  mkdir -p /tmp/r && cp -r /origen/frontend /origen/seed /tmp/r/ && cd /tmp/r/frontend
  npm ci --no-audit --no-fund >/dev/null 2>&1
  npm i --no-save --no-audit --no-fund jsdom >/dev/null 2>&1
  npx esbuild pruebas/prueba-error.tsx --bundle --platform=node --format=cjs --jsx=automatic --outfile=out.cjs --log-level=error
  node -r ./pruebas/setup-dom.cjs out.cjs 2>&1 | grep -v "React Router Future Flag"
'

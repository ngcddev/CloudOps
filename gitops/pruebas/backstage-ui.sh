#!/usr/bin/env bash
# Prueba de Backstage en un navegador real (spec 017, T02): Chromium con Playwright en un contenedor (sin instalar nada en el equipo) abre https://backstage.hub.local,
# entra como invitado, comprueba que no hay errores de JavaScript, ejecuta la plantilla «Sitio de cliente» desde la interfaz y abre TechDocs. Deja capturas en SALIDA.
# Uso:  set -a; . ./.env.cluster; set +a; SALIDA=./capturas-backstage bash gitops/pruebas/backstage-ui.sh
# Requisitos: Docker (la imagen de Playwright pesa ~1,5 GB la primera vez), el clúster encendido y GITEA_ADMIN_USER/GITEA_ADMIN_PASSWORD en el entorno.
set -euo pipefail
AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
: "${GITEA_ADMIN_USER:?Falta GITEA_ADMIN_USER (.env.cluster)}"
: "${GITEA_ADMIN_PASSWORD:?Falta GITEA_ADMIN_PASSWORD (.env.cluster)}"
SALIDA="${SALIDA:-$AQUI/../../capturas-backstage}"
mkdir -p "$SALIDA"
cp "$AQUI/backstage-ui/navegador.py" "$SALIDA/navegador.py"
SALIDA="$(cd "$SALIDA" && (pwd -W 2>/dev/null || pwd))" GITEA_ADMIN_USER="$GITEA_ADMIN_USER" GITEA_ADMIN_PASSWORD="$GITEA_ADMIN_PASSWORD" \
  "$(command -v python3 >/dev/null 2>&1 && python3 -c 'import sys' 2>/dev/null && echo python3 || echo python)" "$AQUI/backstage-ui/e2e.py"
rm -f "$SALIDA/navegador.py"

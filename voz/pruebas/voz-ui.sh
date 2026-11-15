#!/usr/bin/env bash
# Prueba de la voz del asistente en un navegador real (spec 021): Chromium con Playwright en un contenedor y un micrófono falso que reproduce un audio de práctica
# (sintetizado con el propio servicio de voz). No hace falta hablar ni instalar nada en el equipo.
# Uso:  set -a; . ./.env; set +a; HUB_USUARIO=sofia@forjadigital.test HUB_PASSWORD="$SEED_USER_PASSWORD" bash voz/pruebas/voz-ui.sh
# Requisitos: Docker, `docker compose --profile voz up -d --build voz web api` y Ollama encendido (la imagen de Playwright pesa ~1,5 GB la primera vez).
set -euo pipefail
export MSYS_NO_PATHCONV=1
: "${HUB_USUARIO:?Falta HUB_USUARIO}"
: "${HUB_PASSWORD:?Falta HUB_PASSWORD}"
AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SALIDA="${SALIDA:-$AQUI/../../capturas-voz}"
HUB_WEB="${HUB_WEB:-http://hub.localhost:${WEB_PORT:-5173}}"
VOZ_PUERTO="${VOZ_PORT:-8100}"
mkdir -p "$SALIDA"
# curl.exe de Windows no entiende las rutas /c/… de Git Bash
SALIDA="$(cd "$SALIDA" && (pwd -W 2>/dev/null || pwd))"
cp "$AQUI/navegador.py" "$SALIDA/navegador.py"
# El audio de práctica: la voz del laboratorio dice una pregunta del Hub
printf '{"texto":"Para aprobar un cambio de versión, abre Cambios y pulsa Aprobar."}' > "$SALIDA/practica.json"
curl -fsS -m 60 -X POST "http://localhost:${VOZ_PUERTO}/tts" -H 'Content-Type: application/json' --data-binary "@$SALIDA/practica.json" -o "$SALIDA/audio-de-practica.wav"
RUTA="$SALIDA"
docker run --rm --add-host=host.docker.internal:host-gateway -e HUB_WEB="$HUB_WEB" -e HUB_USUARIO -e HUB_PASSWORD -v "$RUTA:/out" \
  mcr.microsoft.com/playwright/python:v1.49.1-noble sh -c "pip install -q playwright==1.49.1 >/dev/null 2>&1; python /out/navegador.py"
rm -f "$SALIDA/navegador.py" "$SALIDA/practica.json"

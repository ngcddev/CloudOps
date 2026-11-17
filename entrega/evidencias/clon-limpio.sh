#!/usr/bin/env bash
# Prueba de reproducibilidad (criterio del jurado: «clonar, seguir las instrucciones, desplegar y verificar»): clona la rama dev de GitHub en una carpeta temporal, levanta el entorno con
# docker compose en un proyecto aparte («limpio», con otros puertos para no chocar con el entorno de trabajo), mide los tiempos y ensaya los procedimientos básicos del runbook: arranque,
# comprobación, pruebas del backend, reinicio de un servicio, degradación sin IA ni voz y apagado. Usa solo lo que dice CLAUDE.md (el README del repositorio no trae instrucciones de arranque).
set -uo pipefail
# No exportar MSYS_NO_PATHCONV: git.exe tomaba /tmp/... como C:	mp\... y el clon quedaba fuera de la carpeta temporal (así se sobrescribió el .env del repositorio la primera vez)
RAIZ="$(git rev-parse --show-toplevel)"
RAMA="${RAMA:-dev}"
T="$(mktemp -d)"; T="$(cygpath -m "$T" 2>/dev/null || echo "$T")"; P=limpio
seg() { echo $(( $(date +%s) - $1 )); }
cleanup() { (cd "$T/clon" 2>/dev/null && docker compose -p $P down -v --remove-orphans >/dev/null 2>&1); rm -rf "$T"; }
trap cleanup EXIT

echo "== 1. Clonar https://github.com/ngcddev/CloudOps.git (rama $RAMA) =="
t0=$(date +%s); git clone -q --depth 1 --branch "$RAMA" https://github.com/ngcddev/CloudOps.git "$T/clon" || { echo "FALLO: no se pudo clonar"; exit 1; }
echo "   clonado en $(seg $t0) s · commit $(git -C "$T/clon" rev-parse --short HEAD)"
cd "$T/clon" || { echo "FALLO: no existe la carpeta del clon ($T/clon)"; exit 1; }
# Salvaguarda: nada de lo que sigue (cp .env.example .env, sed) puede ocurrir dentro del repositorio de trabajo
[ "$(git rev-parse --show-toplevel)" != "$RAIZ" ] || { echo "FALLO: el directorio actual es el repositorio de trabajo"; exit 1; }

echo "== 2. Configurar .env (cp .env.example .env y un JWT_SECRET propio) =="
cp .env.example .env
JWT="$(python -c 'import secrets;print(secrets.token_hex(32))')"
sed -i "s|^JWT_SECRET=.*|JWT_SECRET=$JWT|" .env
sed -i "s|^DB_PORT=.*|DB_PORT=25432|; s|^API_PORT=.*|API_PORT=28000|; s|^WEB_PORT=.*|WEB_PORT=25173|; s|^RESTAURANTE_PORT=.*|RESTAURANTE_PORT=28081|; s|^FERRETERIA_PORT=.*|FERRETERIA_PORT=28082|; s|^CONSULTORIO_PORT=.*|CONSULTORIO_PORT=28083|" .env
SEED="$(grep '^SEED_USER_PASSWORD=' .env | cut -d= -f2)"

echo "== 3. docker compose up --build (arranque en frío) =="
t0=$(date +%s); docker compose -p $P up -d --build --wait 2>&1 | tail -6
echo "   arranque en frío: $(seg $t0) s"
docker compose -p $P ps --format '{{.Service}} {{.Status}}' | sed 's/^/   /'

echo "== 4. Comprobar =="
curl -s -m 10 "http://localhost:28000/health" | sed 's/^/   api \/health: /'; echo
curl -s -m 10 -o /dev/null -w '   web /health: %{http_code}\n' "http://localhost:25173/health"
TOK="$(curl -s -m 10 -H 'Content-Type: application/json' -X POST http://localhost:28000/api/auth/login -d "{\"email\":\"sofia@forjadigital.test\",\"password\":\"$SEED\"}" | python -c "import sys,json;print(json.load(sys.stdin).get('access_token',''))")"
[ -n "$TOK" ] && echo "   inicio de sesión con el usuario sembrado: OK" || echo "   inicio de sesión: FALLO"
curl -s -m 10 -H "Authorization: Bearer $TOK" http://localhost:28000/api/clients | python -c "import sys,json; print('   clientes sembrados:', len(json.load(sys.stdin)))"

echo "== 5. Pruebas del backend dentro del contenedor =="
t0=$(date +%s); docker compose -p $P exec -T api pytest -q 2>&1 | tail -3; echo "   pytest: $(seg $t0) s"

echo "== 6. Runbook: reinicio de un servicio (api) =="
t0=$(date +%s); docker compose -p $P restart api >/dev/null 2>&1
until [ "$(curl -s -m 3 -o /dev/null -w '%{http_code}' http://localhost:28000/health)" = "200" ]; do sleep 1; [ "$(seg $t0)" -gt 120 ] && break; done
echo "   api de nuevo sana a los $(seg $t0) s"

echo "== 7. Runbook: degradación elegante (sin Ollama y sin voz) =="
curl -s -m 60 -o "$T/ask.json" -w "   HTTP %{http_code}
" -H "Authorization: Bearer $TOK" -H "Content-Type: application/json" -X POST http://localhost:28000/api/assistant/ask -d '{"question":"Como apruebo un cambio de version?"}'
python "$RAIZ/entrega/evidencias/asistente-sin-ia.py" "$T/ask.json"
curl -s -m 10 -H "Authorization: Bearer $TOK" http://localhost:28000/api/assistant/voice/status | sed 's/^/   voz: /'; echo

echo "== 8. Runbook: apagado =="
t0=$(date +%s); docker compose -p $P down -v --remove-orphans >/dev/null 2>&1; echo "   apagado limpio en $(seg $t0) s"
echo "FIN"

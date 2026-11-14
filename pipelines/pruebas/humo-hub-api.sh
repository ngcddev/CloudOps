#!/usr/bin/env bash
# Prueba de humo de la imagen de PRODUCCIÓN de la API del Hub: se construye sin --target, arranca contra un PostgreSQL
# desechable, aplica las migraciones y siembra los datos, responde /health, corre sin root y no lleva pytest ni las pruebas.
# La usa la CI del Hub (.github/workflows/ci.yml) y sirve a mano antes de publicar una versión.
# Uso: bash pipelines/pruebas/humo-hub-api.sh [imagen]     (sin argumento construye hub-api:humo)
set -uo pipefail
export MSYS_NO_PATHCONV=1
RAIZ="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$RAIZ"
IMAGEN="${1:-hub-api:humo}"
SUFIJO="$$"
RED="humo-red-$SUFIJO"; DB="humo-db-$SUFIJO"; API="humo-api-$SUFIJO"
fallos=0
ok() { echo "✓ $1"; }
mal() { echo "✗ $1"; fallos=$((fallos + 1)); }
limpiar() { docker rm -f "$API" "$DB" >/dev/null 2>&1; docker network rm "$RED" >/dev/null 2>&1; }
trap limpiar EXIT

if [ "$#" -eq 0 ]; then
  docker build -q --build-context seed=./seed -t "$IMAGEN" backend >/dev/null && ok "la imagen de producción se construye" || { mal "no se pudo construir la imagen"; exit 1; }
fi

[ "$(docker run --rm --entrypoint id "$IMAGEN" -u)" = "10001" ] && ok "corre como usuario 10001, no como root" || mal "corre como root"
if docker run --rm --entrypoint sh "$IMAGEN" -c 'test -e /app/tests || test -e /app/pytest.ini || python -c "import pytest" 2>/dev/null'; then
  mal "la imagen de producción lleva pytest o las pruebas"
else
  ok "no lleva pytest ni las pruebas"
fi

docker network create "$RED" >/dev/null
docker run -d --name "$DB" --network "$RED" -e POSTGRES_USER=hub -e POSTGRES_PASSWORD=humo -e POSTGRES_DB=hub postgres:16-alpine >/dev/null
for _ in $(seq 1 30); do docker exec "$DB" pg_isready -U hub -d hub >/dev/null 2>&1 && break; sleep 1; done
docker run -d --name "$API" --network "$RED" -p 0:8000 \
  -e DATABASE_URL="postgresql+psycopg://hub:humo@$DB:5432/hub" -e JWT_SECRET=humo-0123456789-0123456789-0123 -e SEED_USER_PASSWORD=humo \
  "$IMAGEN" >/dev/null
PUERTO="$(docker port "$API" 8000/tcp | head -1 | sed 's/.*://')"
sano=0
for _ in $(seq 1 45); do
  if curl -fs "http://localhost:${PUERTO}/health" >/dev/null 2>&1; then sano=1; break; fi
  sleep 1
done
[ "$sano" = 1 ] && ok "la API responde /health tras migrar" || { mal "la API no respondió /health"; docker logs "$API" 2>&1 | tail -5; }
usuarios="$(docker exec "$DB" psql -U hub -d hub -tAc 'select count(*) from users' 2>/dev/null | tr -d '[:space:]')"
[ "${usuarios:-0}" -gt 0 ] && ok "las migraciones corrieron y se sembraron $usuarios usuarios" || mal "no hay datos sembrados"

[ "$fallos" -eq 0 ] && echo "Todo en verde." || { echo "Falló en $fallos paso(s)."; exit 1; }

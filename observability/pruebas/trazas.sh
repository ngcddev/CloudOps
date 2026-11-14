#!/usr/bin/env bash
# Prueba de punta a punta de las trazas del Hub (OpenTelemetry → Tempo): levanta Tempo con la configuración del clúster, un PostgreSQL
# desechable y la imagen de PRODUCCIÓN de la API con OTEL_EXPORTER_OTLP_ENDPOINT, hace peticiones (incluida una pregunta al asistente) y le
# pregunta a Tempo por las trazas. Comprueba que lleguen los spans de la API y las etapas del asistente, que /health no genere trazas y que ningún
# dato de la pregunta salga en una traza (principio 2). No necesita Ollama: sin él el asistente responde igual y deja sus spans.
# Uso: bash observability/pruebas/trazas.sh [imagen-de-la-api]     (sin argumento construye hub-api:trazas)
set -uo pipefail
export MSYS_NO_PATHCONV=1
RAIZ="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$RAIZ"
OBS="$(cd observability && (pwd -W 2>/dev/null || pwd))"
IMAGEN="${1:-hub-api:trazas}"
S="$$"; RED="trazas-red-$S"; TEMPO="trazas-tempo-$S"; DB="trazas-db-$S"; API="trazas-api-$S"
fallos=0
ok() { echo "✓ $1"; }
mal() { echo "✗ $1"; fallos=$((fallos + 1)); }
limpiar() { docker rm -f "$API" "$DB" "$TEMPO" >/dev/null 2>&1; docker network rm "$RED" >/dev/null 2>&1; }
trap limpiar EXIT

[ "$#" -eq 0 ] && { docker build -q --build-context seed=./seed -t "$IMAGEN" backend >/dev/null && ok "imagen de producción construida" || { mal "no se pudo construir la imagen"; exit 1; }; }
docker network create "$RED" >/dev/null
docker run -d --name "$TEMPO" --network "$RED" -p 0:3200 --tmpfs /var/tempo:rw,uid=10001,gid=10001 \
  -v "$OBS/tempo/tempo.yaml:/etc/tempo/tempo.yaml:ro" grafana/tempo:2.8.2 -config.file=/etc/tempo/tempo.yaml >/dev/null
docker run -d --name "$DB" --network "$RED" -e POSTGRES_USER=hub -e POSTGRES_PASSWORD=trazas -e POSTGRES_DB=hub postgres:16-alpine >/dev/null
for _ in $(seq 1 30); do docker exec "$DB" pg_isready -U hub -d hub >/dev/null 2>&1 && break; sleep 1; done
PUERTO_TEMPO="$(docker port "$TEMPO" 3200/tcp | head -1 | sed 's/.*://')"
for _ in $(seq 1 60); do curl -fs "http://localhost:${PUERTO_TEMPO}/ready" >/dev/null 2>&1 && break; sleep 1; done
curl -fs "http://localhost:${PUERTO_TEMPO}/ready" >/dev/null && ok "Tempo listo con la configuración del clúster" || { mal "Tempo no arrancó"; docker logs "$TEMPO" 2>&1 | tail -5; exit 1; }

CLAVE="trazas-0123456789-0123456789"
docker run -d --name "$API" --network "$RED" -p 0:8000 \
  -e DATABASE_URL="postgresql+psycopg://hub:trazas@$DB:5432/hub" -e JWT_SECRET="$CLAVE" -e SEED_USER_PASSWORD=trazas \
  -e OTEL_EXPORTER_OTLP_ENDPOINT="http://$TEMPO:4318" "$IMAGEN" >/dev/null
PUERTO_API="$(docker port "$API" 8000/tcp | head -1 | sed 's/.*://')"
for _ in $(seq 1 45); do curl -fs "http://localhost:${PUERTO_API}/health" >/dev/null 2>&1 && break; sleep 1; done
curl -fs "http://localhost:${PUERTO_API}/health" >/dev/null && ok "la API arrancó con las trazas activas" || { mal "la API no arrancó"; docker logs "$API" 2>&1 | tail -5; exit 1; }

TOKEN="$(curl -s -H 'Content-Type: application/json' -X POST "http://localhost:${PUERTO_API}/api/auth/login" -d '{"email":"sofia@forjadigital.test","password":"trazas"}' | sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p')"
[ -n "$TOKEN" ] && ok "inicio de sesión de agencia" || mal "no se pudo iniciar sesión"
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:${PUERTO_API}/api/plans" >/dev/null
# Preguntas con datos que no deben salir en ninguna traza
# Sin tildes: Git Bash en Windows no manda UTF-8 en los argumentos y la API respondería 400
for pregunta in "Cual es el telefono confidencial de Dona Clarita?" "Como hago un rollback del sitio de Don Aurelio?"; do
  estado="$(curl -s -m 30 -o /dev/null -w '%{http_code}' -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -X POST "http://localhost:${PUERTO_API}/api/assistant/ask" -d "{\"question\":\"$pregunta\"}")"
  [ "$estado" = "200" ] && ok "el asistente respondió (HTTP 200)" || mal "el asistente respondió HTTP $estado"
done

# Tempo tarda unos segundos en cerrar el bloque y poder buscarlo
todas=""
for _ in $(seq 1 45); do
  ids="$(curl -s "http://localhost:${PUERTO_TEMPO}/api/search?tags=service.name%3Dhub-api&limit=50" | grep -o '"traceID":"[0-9a-f]*"' | cut -d'"' -f4 | sort -u)"
  todas=""
  for id in $ids; do todas="$todas$(curl -s -H 'Accept: application/json' "http://localhost:${PUERTO_TEMPO}/api/traces/$id")"; done
  echo "$todas" | grep -q 'assistant.compuerta' && echo "$todas" | grep -q 'assistant.contexto' && break
  sleep 2
done
echo "$todas" | grep -q 'assistant.compuerta' && ok "Tempo tiene el span assistant.compuerta del asistente" || { mal "no llegó assistant.compuerta a Tempo; spans recibidos: $(echo "$todas" | grep -o '"name":"[^"]*"' | sort -u | tr '
' ' ')"; }
echo "$todas" | grep -q 'assistant.contexto' && ok "Tempo tiene el span assistant.contexto" || mal "no llegó assistant.contexto"
echo "$todas" | grep -q '/api/plans' && ok "Tempo tiene la traza de la petición GET /api/plans" || mal "no llegó la traza de la API"
echo "$todas" | grep -q '"/health"\|GET /health' && mal "/health generó trazas (debía excluirse)" || ok "/health no genera trazas"
privados="$(echo "$todas" | grep -o -i -E 'clarita|confidencial|aurelio|rollback del sitio' | sort -u | tr '\n' ' ')"
[ -z "$privados" ] && ok "ninguna traza lleva el texto de las preguntas" || mal "las trazas filtraron texto de las preguntas: $privados"

[ "$fallos" -eq 0 ] && echo "Todo en verde." || { echo "Falló en $fallos paso(s)."; exit 1; }

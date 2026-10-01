#!/usr/bin/env bash
# Prueba de humo del sitio de Dental Popayán (spec 002, T09): construye las imágenes v1 y v2,
# las levanta y comprueba usuario no root, /health, el formulario de citas por /api y los 500 de v2.
# Uso (desde cualquier carpeta, con Docker corriendo): bash apps/consultorio/smoke-test.sh

set -euo pipefail
cd "$(dirname "$0")"

PREFIX="consultorio-smoke"
NETWORK="${PREFIX}-net"
FAILURES=0

# Borra contenedores y red al terminar, pase lo que pase.
cleanup() {
  docker rm -f "${PREFIX}-api-v1" "${PREFIX}-api-v2" "${PREFIX}-web-v1" "${PREFIX}-web-v2" >/dev/null 2>&1 || true
  docker network rm "$NETWORK" >/dev/null 2>&1 || true
}
trap cleanup EXIT

# Compara un valor obtenido con el esperado e informa con texto (✓ / ✕).
check() {
  local description="$1" expected="$2" actual="$3"
  if [[ "$actual" == "$expected" ]]; then
    echo "✓ $description"
  else
    echo "✕ $description (esperado: $expected · obtenido: $actual)"
    FAILURES=$((FAILURES + 1))
  fi
}

# Devuelve "código cuerpo" de una petición HTTP.
request() {
  curl -s -o /tmp/${PREFIX}-body -w '%{http_code}' "$@" && echo " $(cat /tmp/${PREFIX}-body)"
}

# Puerto del host asignado a un contenedor (se publican en puertos libres para no chocar con nada).
host_port() {
  docker port "$1" "$2" | head -1 | sed 's/.*://'
}

# Espera a que un endpoint responda (sin importar el código) hasta 30 s.
wait_for() {
  for _ in $(seq 1 30); do
    curl -s -o /dev/null "$1" && return 0
    sleep 1
  done
  echo "✕ $1 no respondió a tiempo"
  exit 1
}

echo "== Construyendo imágenes"
for version in v1 v2; do
  docker build -q -f Dockerfile.backend --build-arg APP_VERSION="$version" -t "hub/consultorio-api:$version" . >/dev/null
  docker build -q -f Dockerfile.frontend --build-arg APP_VERSION="$version" -t "hub/consultorio-web:$version" . >/dev/null
done

echo "== Levantando contenedores"
cleanup
docker network create "$NETWORK" >/dev/null
for version in v1 v2; do
  docker run -d --name "${PREFIX}-api-$version" --network "$NETWORK" -p 127.0.0.1::8000 \
    "hub/consultorio-api:$version" >/dev/null
  docker run -d --name "${PREFIX}-web-$version" --network "$NETWORK" -p 127.0.0.1::8080 \
    -e API_UPSTREAM="${PREFIX}-api-$version:8000" "hub/consultorio-web:$version" >/dev/null
done

API_V1="http://127.0.0.1:$(host_port "${PREFIX}-api-v1" 8000)"
API_V2="http://127.0.0.1:$(host_port "${PREFIX}-api-v2" 8000)"
WEB_V1="http://127.0.0.1:$(host_port "${PREFIX}-web-v1" 8080)"
WEB_V2="http://127.0.0.1:$(host_port "${PREFIX}-web-v2" 8080)"
for url in "$API_V1" "$API_V2" "$WEB_V1" "$WEB_V2"; do wait_for "$url/health"; done

echo "== Contenedores sin root"
check "backend corre con UID 10001" "10001" "$(docker exec "${PREFIX}-api-v1" id -u)"
check "frontend corre con UID 101" "101" "$(docker exec "${PREFIX}-web-v1" id -u)"

echo "== Versión v1 (sana)"
check "backend /health" '200 {"status":"ok","version":"v1"}' "$(request "$API_V1/health")"
check "frontend /health" '200 {"status":"ok","version":"v1"}' "$(request "$WEB_V1/health")"
check "frontend / sirve la página" "200" "$(curl -s -o /dev/null -w '%{http_code}' "$WEB_V1/")"
check "formulario de citas a través del proxy /api" '200 {"ok":true}' "$(request -X POST "$WEB_V1/api/contact" \
  -H 'Content-Type: application/json' -d '{"name":"Paciente de prueba","phone":"3000000000","reason":"Valoracion de prueba"}')"

echo "== Versión v2 (rota a propósito)"
check "backend /health responde 500" '500 {"status":"error","version":"v2"}' "$(request "$API_V2/health")"
check "frontend /health responde 500" '500 {"status":"error","version":"v2"}' "$(request "$WEB_V2/health")"
check "frontend / responde 500" "500" "$(curl -s -o /dev/null -w '%{http_code}' "$WEB_V2/")"

echo
if [[ "$FAILURES" -eq 0 ]]; then
  echo "✓ Prueba de humo superada"
else
  echo "✕ $FAILURES comprobación(es) fallaron"
  exit 1
fi

#!/usr/bin/env bash
# Reinicia la demo (spec 015): deja el Hub con los datos semilla de seed/ y los tres sitios de los clientes en su versión sana (v1),
# para ensayar siempre desde el mismo punto. En el entorno de docker compose:
#   1. detiene la API y la web, recrea la base `hub` vacía (se pierden tickets, incidentes, consultas del asistente y el índice del RAG)
#   2. levanta la API: aplica las migraciones y siembra los datos al encontrar la base vacía
#   3. recrea los sitios de los clientes en v1 (si alguno quedó en v2, el caso del restaurante)
#   4. comprueba que todo responde
# No toca MLflow, Ollama ni los modelos. Para el clúster k3s el reinicio es otro (GitOps): ver runbooks/.
# Uso: bash demo/reiniciar.sh [--sin-comprobar]      (ENV_FILE=otro.env para otro entorno; borra la base del entorno elegido)
set -uo pipefail
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
cd "$RAIZ"
# ENV_FILE permite apuntar a otro archivo de variables (otro nombre de proyecto y otros puertos, por ejemplo en la CI)
ENV_FILE="${ENV_FILE:-.env}"
[ -f "$ENV_FILE" ] || { echo "Falta $ENV_FILE: cp .env.example .env" >&2; exit 2; }
set -a; . "./$ENV_FILE"; set +a
# Los sitios vuelven a v1 aunque el entorno tenga otra versión exportada
unset RESTAURANTE_VERSION FERRETERIA_VERSION CONSULTORIO_VERSION

paso() { echo "→ $1"; }
fallo() { echo "✗ $1" >&2; exit 1; }
COMPROBAR=1
[ "${1:-}" = "--sin-comprobar" ] && COMPROBAR=0

paso "Deteniendo la API y la web"
docker compose stop api web >/dev/null 2>&1
docker compose up -d db >/dev/null 2>&1 || fallo "no se pudo levantar la base"
for _ in $(seq 1 30); do docker compose exec -T db pg_isready -U "$POSTGRES_USER" -d postgres >/dev/null 2>&1 && break; sleep 1; done

paso "Recreando la base ${POSTGRES_DB} vacía"
psql_db() { docker compose exec -T db psql -U "$POSTGRES_USER" -d postgres -v ON_ERROR_STOP=1 -q "$@" </dev/null; }
psql_db -c "DROP DATABASE IF EXISTS \"${POSTGRES_DB}\" WITH (FORCE)" || fallo "no se pudo borrar la base"
psql_db -c "CREATE DATABASE \"${POSTGRES_DB}\"" || fallo "no se pudo crear la base"

paso "Levantando la API (migra y siembra) y la web"
docker compose up -d api web >/dev/null 2>&1 || fallo "no se pudo levantar la API"

paso "Recreando los sitios de los clientes en v1"
docker compose up -d --build --force-recreate restaurante ferreteria consultorio-api consultorio-web >/dev/null 2>&1 || fallo "no se pudieron recrear los sitios"

if [ "$COMPROBAR" = 1 ]; then
  paso "Comprobando"
  for _ in $(seq 1 60); do curl -fs "http://localhost:${API_PORT:-8000}/health" >/dev/null 2>&1 && break; sleep 1; done
  curl -fs "http://localhost:${API_PORT:-8000}/health" >/dev/null || fallo "la API no responde"
  usuarios="$(docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc 'select count(*) from users' </dev/null | tr -d '[:space:]')"
  [ "${usuarios:-0}" -gt 0 ] || fallo "la base no quedó sembrada"
  for sitio in "restaurante ${RESTAURANTE_PORT:-8081}" "ferreteria ${FERRETERIA_PORT:-8082}" "consultorio ${CONSULTORIO_PORT:-8083}"; do
    set -- $sitio
    for _ in $(seq 1 30); do respuesta="$(curl -fs "http://localhost:$2/health" 2>/dev/null)" && break; sleep 1; done
    case "${respuesta:-}" in *'"version":"v1"'*) echo "   ✓ $1 en v1" ;; *) fallo "$1 no responde en v1: ${respuesta:-sin respuesta}" ;; esac
  done
  echo "   ✓ API sana y ${usuarios} usuarios sembrados"
fi
echo "Demo reiniciada: datos semilla y sitios en v1."

#!/usr/bin/env bash
# Valida la pila de observabilidad sin tocar el clúster (spec 008, T23):
#   1. promtool check config  sobre prometheus.yml (con las reglas montadas donde las busca)
#   2. promtool check rules   sobre las reglas de alerta
#   3. promtool test rules    con los casos de observability/pruebas/reglas_test.yml
#   4. amtool check-config    sobre alertmanager.yml (si ya existe)
#   5. kubectl kustomize      de observability/ (que todos los manifiestos armen)
# promtool y amtool corren en contenedor, con la misma versión de las imágenes de los manifiestos.
# Si no hay Docker pero promtool/amtool están en el PATH, se usan esos.
# Uso: bash observability/pruebas/validar.sh
set -uo pipefail
export MSYS_NO_PATHCONV=1   # Git Bash en Windows: no convertir las rutas de los -v de Docker

OBS="$(cd "$(dirname "$0")/.." && pwd)"
OBS_HOST="$(cd "$OBS" && (pwd -W 2>/dev/null || pwd))"
PROMETHEUS_IMAGE="${PROMETHEUS_IMAGE:-prom/prometheus:v3.5.0}"
ALERTMANAGER_IMAGE="${ALERTMANAGER_IMAGE:-prom/alertmanager:v0.28.1}"
fallos=0

paso() {  # paso <descripción> <comando...>
  local descripcion="$1"; shift
  if "$@"; then echo "✓ ${descripcion}"; else echo "✗ ${descripcion}"; fallos=$((fallos + 1)); fi
}

if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  # Se monta todo observability/ en /obs y las reglas además en la ruta que usa prometheus.yml
  promtool() {
    docker run --rm -v "${OBS_HOST}:/obs:ro" -v "${OBS_HOST}/prometheus/reglas:/etc/prometheus/reglas:ro" \
      -w /obs --entrypoint promtool "$PROMETHEUS_IMAGE" "$@"
  }
  amtool() {
    docker run --rm -v "${OBS_HOST}:/obs:ro" -w /obs --entrypoint amtool "$ALERTMANAGER_IMAGE" "$@"
  }
  RAIZ_OBS=/obs
elif command -v promtool >/dev/null 2>&1; then
  echo "(sin Docker: se usan promtool y amtool del PATH)"
  RAIZ_OBS="$OBS"
  if [ ! -d /etc/prometheus/reglas ]; then
    # prometheus.yml busca las reglas en /etc/prometheus/reglas: se valida una copia que apunta aquí
    TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
    sed "s#/etc/prometheus/reglas/#${OBS}/prometheus/reglas/#" "$OBS/prometheus/prometheus.yml" > "$TMP/prometheus.yml"
  fi
else
  echo "Hace falta Docker (o promtool y amtool en el PATH) para validar." >&2
  exit 2
fi

CONFIG="${TMP:+$TMP/prometheus.yml}"
CONFIG="${CONFIG:-${RAIZ_OBS}/prometheus/prometheus.yml}"
paso "prometheus.yml es válido" promtool check config "$CONFIG"
paso "las reglas de alerta son válidas" promtool check rules "${RAIZ_OBS}"/prometheus/reglas/*.yml
paso "SitioCaido pasa sus pruebas" promtool test rules "${RAIZ_OBS}/pruebas/reglas_test.yml"
if [ -f "$OBS/alertmanager/alertmanager.yml" ]; then
  paso "alertmanager.yml es válido" amtool check-config "${RAIZ_OBS}/alertmanager/alertmanager.yml"
fi
if command -v kubectl >/dev/null 2>&1; then
  paso "observability/ arma con kustomize" bash -c "kubectl kustomize '$OBS' >/dev/null"
else
  echo "(sin kubectl: no se revisó kustomize)"
fi

if [ "$fallos" -gt 0 ]; then
  echo "La validación falló en ${fallos} paso(s)."
  exit 1
fi
echo "Todo en verde."

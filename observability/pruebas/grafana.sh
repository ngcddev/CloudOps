#!/usr/bin/env bash
# Comprueba que Grafana carga el tablero «Servicio de los sitios» con los mismos archivos de aprovisionamiento que usa
# el clúster (spec 010): levanta la imagen fijada en deployment.yaml, espera su API y pregunta por el tablero.
# Las fuentes de datos apuntan a servicios que aquí no existen: solo se revisa que el tablero se cargue y quede completo.
# Uso: bash observability/pruebas/grafana.sh
set -uo pipefail
export MSYS_NO_PATHCONV=1
OBS="$(cd "$(dirname "$0")/.." && (pwd -W 2>/dev/null || pwd))"
IMAGEN="${GRAFANA_IMAGE:-grafana/grafana:12.1.1}"
PUERTO="${GRAFANA_PRUEBA_PUERTO:-13000}"
NOMBRE="grafana-prueba-$$"
trap 'docker rm -f "$NOMBRE" >/dev/null 2>&1' EXIT

docker run -d --name "$NOMBRE" -p "${PUERTO}:3000" \
  -e GF_SECURITY_ADMIN_USER=admin -e GF_SECURITY_ADMIN_PASSWORD=prueba \
  -e GF_ANALYTICS_REPORTING_ENABLED=false -e GF_ANALYTICS_CHECK_FOR_UPDATES=false \
  -v "${OBS}/grafana/datasources.yaml:/etc/grafana/provisioning/datasources/datasources.yaml:ro" \
  -v "${OBS}/grafana/dashboards-provider.yaml:/etc/grafana/provisioning/dashboards/dashboards-provider.yaml:ro" \
  -v "${OBS}/grafana/dashboards:/etc/grafana/dashboards-hub:ro" \
  "$IMAGEN" >/dev/null || { echo "✗ no se pudo iniciar Grafana"; exit 1; }

for _ in $(seq 1 60); do
  curl -fs "http://localhost:${PUERTO}/api/health" >/dev/null 2>&1 && break
  sleep 2
done
sleep 5  # el proveedor de tableros carga poco después de que la API responde

fallos=0
busqueda="$(curl -fs -u admin:prueba "http://localhost:${PUERTO}/api/search?query=Servicio")" || busqueda=""
if echo "$busqueda" | grep -q '"uid":"servicio-sitios"'; then echo "✓ Grafana cargó el tablero servicio-sitios"; else echo "✗ el tablero no aparece: $busqueda"; fallos=$((fallos + 1)); fi

tablero="$(curl -fs -u admin:prueba "http://localhost:${PUERTO}/api/dashboards/uid/servicio-sitios")" || tablero=""
paneles="$(echo "$tablero" | grep -o '"type":"\(stat\|timeseries\|logs\|text\)"' | wc -l | tr -d ' ')"
if [ "${paneles:-0}" -ge 13 ]; then echo "✓ el tablero tiene ${paneles} paneles"; else echo "✗ el tablero tiene ${paneles:-0} paneles (se esperaban 13)"; fallos=$((fallos + 1)); fi

fuentes="$(curl -fs -u admin:prueba "http://localhost:${PUERTO}/api/datasources")" || fuentes=""
for uid in prometheus loki tempo; do
  if echo "$fuentes" | grep -q "\"uid\":\"${uid}\""; then echo "✓ fuente de datos ${uid} provisionada"; else echo "✗ falta la fuente ${uid}"; fallos=$((fallos + 1)); fi
done
[ "$fallos" -eq 0 ] && echo "Todo en verde." || { echo "Falló en ${fallos} paso(s)."; exit 1; }

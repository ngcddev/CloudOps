#!/usr/bin/env bash
# Prueba de la salida de red de un cliente (spec 022, T14; auditoría K8-02): un Pod de cliente comprometido no debe poder llegar a lo demás del clúster.
# Lanza un Pod busybox en el namespace del cliente y comprueba (1) lo que SÍ necesita un sitio: resolver nombres (DNS) y hablar con los Pods de su propio
# namespace, y (2) lo que NO debe alcanzar: los servicios sin autenticación del monitoreo (Loki, Prometheus, Alertmanager), MLflow, Gitea, Argo CD, el Hub,
# otro cliente e internet. «Llegó» significa que hubo conexión (aunque el servicio responda con un error); «no llegó» es tiempo de espera o conexión rechazada.
# Uso: bash gitops/pruebas/salida-red.sh [cliente]   (por defecto ferreteria-staging; con --estado muestra el resultado sin fallar la salida)
set -uo pipefail
export MSYS_NO_PATHCONV=1   # Git Bash en Windows: no convertir rutas como /dev/null al pasárselas a kubectl

CLIENTE="${1:-ferreteria-staging}"
NS="cliente-${CLIENTE}"
IMAGEN="${IMAGEN:-gitea.hub.local/forja-digital/busybox:v1}"
POD="prueba-salida"
SOLO_MIDE=0; [ "${2:-}" = "--estado" ] && SOLO_MIDE=1
OTRO="restaurante"; [ "$CLIENTE" = "restaurante" ] && OTRO="ferreteria"   # otro cliente: nunca el mismo

kubectl -n "$NS" delete pod "$POD" --ignore-not-found --now >/dev/null 2>&1
# El Pod cumple el perfil `restricted` del namespace: sin root, sin privilegios.
kubectl -n "$NS" run "$POD" --image="$IMAGEN" --restart=Never \
  --overrides='{"spec":{"securityContext":{"runAsNonRoot":true,"runAsUser":1000,"seccompProfile":{"type":"RuntimeDefault"}},"containers":[{"name":"'"$POD"'","image":"'"$IMAGEN"'","command":["sleep","600"],"securityContext":{"allowPrivilegeEscalation":false,"capabilities":{"drop":["ALL"]}}}]}}' >/dev/null
kubectl -n "$NS" wait --for=condition=Ready "pod/$POD" --timeout=120s >/dev/null || { echo "El Pod de prueba no arrancó"; exit 2; }
trap 'kubectl -n "$NS" delete pod "$POD" --now >/dev/null 2>&1' EXIT

fallos=0
# llego <url>: 0 si hubo conexión con el servicio (aunque responda un error HTTP), 1 si no
llego() {
  local salida
  salida="$(kubectl -n "$NS" exec "$POD" -- wget -q -T 3 -O - "$1" 2>&1)" && return 0
  echo "$salida" | grep -q "server returned error" && return 0
  return 1
}
debe_llegar() {
  if llego "$2"; then echo "  ✓ $1 → llega"; else echo "  ✗ $1 → NO llega (debía llegar)"; fallos=$((fallos + 1)); fi
}
no_debe_llegar() {
  if llego "$2"; then echo "  ✗ $1 → LLEGA (debía estar bloqueado)"; fallos=$((fallos + 1)); else echo "  ✓ $1 → bloqueado"; fi
}

echo ">> Desde ${NS}, lo que un sitio necesita"
if kubectl -n "$NS" exec "$POD" -- nslookup "web.${NS}.svc.cluster.local" >/dev/null 2>&1; then echo "  ✓ resolver nombres (DNS) → funciona"; else echo "  ✗ resolver nombres (DNS) → NO funciona (debía funcionar)"; fallos=$((fallos + 1)); fi
debe_llegar "su propio sitio (web.${NS}.svc/health)" "http://web.${NS}.svc/health"

echo ">> Lo que NO debe alcanzar un Pod de cliente"
no_debe_llegar "Loki (logs de todos los clientes, sin autenticación)" "http://loki.monitoring.svc:3100/ready"
no_debe_llegar "Prometheus (métricas de todos, sin autenticación)" "http://prometheus.monitoring.svc:9090/-/ready"
no_debe_llegar "Alertmanager (podría mandar alertas falsas al Hub)" "http://alertmanager.monitoring.svc:9093/-/ready"
no_debe_llegar "Grafana" "http://grafana.monitoring.svc:3000/api/health"
no_debe_llegar "MLflow (registro de modelos, sin autenticación)" "http://mlflow.mlops.svc:5000/health"
no_debe_llegar "Gitea (repositorios y registro de imágenes)" "http://gitea.gitea.svc:3000/api/healthz"
no_debe_llegar "el API del Hub" "http://api.hub.svc:8000/livez"
no_debe_llegar "el sitio de otro cliente (cliente-${OTRO})" "http://web.cliente-${OTRO}.svc/health"
no_debe_llegar "internet (1.1.1.1)" "http://1.1.1.1/"

if [ "$fallos" -gt 0 ]; then echo; echo "${fallos} comprobación(es) no cumplen lo esperado."; [ "$SOLO_MIDE" = 1 ] && exit 0; exit 1; fi
echo; echo "Todo en verde."

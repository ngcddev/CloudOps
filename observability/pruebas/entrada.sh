#!/usr/bin/env bash
# Prueba en el clúster (spec 022, T17): al namespace monitoring solo entran sus propios Pods, Traefik (hacia Grafana) y el namespace hub (hacia Prometheus 9090,
# Loki 3100 y Tempo 4318). Otros namespaces no. Y la pila sigue viva: Prometheus ve sus blancos arriba, Loki recibe registros y el Hub sigue consultando.
# Uso: KUBECONFIG=... bash observability/pruebas/entrada.sh
set -uo pipefail
export MSYS_NO_PATHCONV=1
fallos=0
SEG='"securityContext":{"allowPrivilegeEscalation":false,"capabilities":{"drop":["ALL"]},"runAsNonRoot":true,"runAsUser":1000,"seccompProfile":{"type":"RuntimeDefault"}}'
RES='"resources":{"requests":{"cpu":"5m","memory":"8Mi"},"limits":{"cpu":"20m","memory":"16Mi"}}'

desde() {  # desde <namespace> <url>: OK si un Pod alcanza la URL (o, si empieza por "tcp:", el puerto host:puerto), NO si no
  local cmd="wget -q -T 3 -O - $2 >/dev/null 2>&1"
  case "$2" in tcp:*) cmd="nc -z -w 3 $(echo "${2#tcp:}" | tr ':' ' ')" ;; esac
  # Un Pod de prueba en `hub` lleva la etiqueta app=api para heredar la política de salida de la API (spec 022, T18): sin ella el namespace deniega toda salida
  local etiquetas=(); [ "$1" = "hub" ] && etiquetas=(--labels app=api)
  kubectl run "ent-$RANDOM" --rm -i --restart=Never -n "$1" --image=busybox:1.36 --quiet "${etiquetas[@]}" \
    --overrides="{\"spec\":{\"containers\":[{\"name\":\"t\",\"image\":\"busybox:1.36\",\"command\":[\"sh\",\"-c\",\"$cmd && echo OK || echo NO\"],$SEG,$RES}]}}" 2>/dev/null | tr -d '\r' | grep -E '^(OK|NO)$' | head -1
}
espera() {  # espera <namespace> <url> <OK|NO> <descripción>
  local r; r=$(desde "$1" "$2")
  if [ "$r" = "$3" ]; then echo "  ✓ $4"; else echo "  ✗ $4 (resultado: '$r')"; fallos=$((fallos+1)); fi
}

for ns in default mlops gitea argocd; do
  espera "$ns" "http://loki.monitoring.svc:3100/ready" NO "desde $ns no llega a Loki"
  espera "$ns" "http://prometheus.monitoring.svc:9090/-/ready" NO "desde $ns no llega a Prometheus"
done
espera default "http://alertmanager.monitoring.svc:9093/-/ready" NO "desde default no llega a Alertmanager"
espera default "http://grafana.monitoring.svc:3000/api/health" NO "desde default no llega a Grafana"
espera hub "http://prometheus.monitoring.svc:9090/-/ready" OK "desde hub sí llega a Prometheus"
espera hub "http://loki.monitoring.svc:3100/ready" OK "desde hub sí llega a Loki"
espera hub "tcp:tempo.monitoring.svc:4318" OK "desde hub sí llega al receptor OTLP de Tempo"
espera hub "http://alertmanager.monitoring.svc:9093/-/ready" NO "desde hub no llega a Alertmanager (no lo usa)"

codigo=$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 --resolve grafana.hub.local:80:127.0.0.1 http://grafana.hub.local/api/health || true)
if [ "$codigo" = "200" ]; then echo "  ✓ por Traefik (grafana.hub.local) responde 200"; else echo "  ✗ por Traefik responde '$codigo'"; fallos=$((fallos+1)); fi

# La pila sigue viva: consultas desde dentro del namespace (Prometheus y Alertmanager hablan entre sí, Grafana con sus fuentes)
prom() { kubectl exec -n monitoring deploy/prometheus -- wget -q -T 5 -O - "http://localhost:9090/api/v1/query?query=$1" 2>/dev/null; }
caidos=$(prom 'count(up==0)' | grep -o '"value":\[[^]]*\]' | grep -o '"[0-9]*"\]' | tr -dc '0-9')
if [ -z "$caidos" ]; then echo "  ✓ ningún blanco de Prometheus caído"; else echo "  ✗ blancos caídos: $caidos"; fallos=$((fallos+1)); fi
am=$(kubectl exec -n monitoring deploy/prometheus -- wget -q -T 5 -O - "http://localhost:9090/api/v1/alertmanagers" 2>/dev/null | grep -c '"activeAlertmanagers":\[{')
if [ "$am" = "1" ]; then echo "  ✓ Prometheus ve a Alertmanager"; else echo "  ✗ Prometheus no ve a Alertmanager"; fallos=$((fallos+1)); fi
ds=$(kubectl exec -n monitoring deploy/grafana -- wget -q -T 5 -O - "http://localhost:3000/api/health" 2>/dev/null | grep -c '"database": "ok"')
if [ "$ds" = "1" ]; then echo "  ✓ Grafana sana"; else echo "  ✗ Grafana no responde sana"; fallos=$((fallos+1)); fi

[ "$fallos" -eq 0 ] && echo "entrada (monitoring): todo en orden" || { echo "entrada (monitoring): $fallos fallo(s)"; exit 1; }

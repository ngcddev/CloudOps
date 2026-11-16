#!/usr/bin/env bash
# Prueba en el clúster (spec 022, T15): a MLflow solo se llega por Traefik (mlflow.hub.local). Un Pod de otro namespace (hub, default, un cliente) no debe alcanzarlo.
# Uso: KUBECONFIG=... bash gitops/pruebas/entrada-mlops.sh
set -uo pipefail
export MSYS_NO_PATHCONV=1
fallos=0
SEG='"securityContext":{"allowPrivilegeEscalation":false,"capabilities":{"drop":["ALL"]},"runAsNonRoot":true,"runAsUser":1000,"seccompProfile":{"type":"RuntimeDefault"}}'
RES='"resources":{"requests":{"cpu":"5m","memory":"8Mi"},"limits":{"cpu":"20m","memory":"16Mi"}}'

desde() {  # desde <namespace> <url>: imprime OK si el Pod alcanza la URL
  local ns=$1 url=$2
  kubectl run "ent-$RANDOM" --rm -i --restart=Never -n "$ns" --image=busybox:1.36 --quiet \
    --overrides="{\"spec\":{\"containers\":[{\"name\":\"t\",\"image\":\"busybox:1.36\",\"command\":[\"sh\",\"-c\",\"wget -q -T 3 -O - $url >/dev/null 2>&1 && echo OK || echo NO\"],$SEG,$RES}]}}" 2>/dev/null | tr -d '\r' | grep -E '^(OK|NO)$' | head -1
}

for ns in hub default; do
  r=$(desde "$ns" "http://mlflow.mlops.svc:5000/health")
  if [ "$r" = "NO" ]; then echo "  ✓ desde $ns no llega a MLflow"; else echo "  ✗ desde $ns llega a MLflow (resultado: '$r')"; fallos=$((fallos+1)); fi
done

codigo=$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 --resolve mlflow.hub.local:80:127.0.0.1 http://mlflow.hub.local/health || true)
if [ "$codigo" = "200" ]; then echo "  ✓ por Traefik (mlflow.hub.local) responde 200"; else echo "  ✗ por Traefik responde '$codigo'"; fallos=$((fallos+1)); fi

[ "$fallos" -eq 0 ] && echo "entrada-mlops: todo en orden" || { echo "entrada-mlops: $fallos fallo(s)"; exit 1; }

#!/usr/bin/env bash
# Prueba en el clúster (spec 022, T16): a Gitea solo llegan Traefik, Argo CD, el Hub (namespace hub) y su propio namespace. Un Pod de default o de un cliente no.
# Uso: KUBECONFIG=... bash gitops/pruebas/entrada-gitea.sh
set -uo pipefail
export MSYS_NO_PATHCONV=1
fallos=0
SEG='"securityContext":{"allowPrivilegeEscalation":false,"capabilities":{"drop":["ALL"]},"runAsNonRoot":true,"runAsUser":1000,"seccompProfile":{"type":"RuntimeDefault"}}'
RES='"resources":{"requests":{"cpu":"5m","memory":"8Mi"},"limits":{"cpu":"20m","memory":"16Mi"}}'

desde() {  # desde <namespace> <url>: imprime OK si un Pod alcanza la URL, NO si no
  kubectl run "ent-$RANDOM" --rm -i --restart=Never -n "$1" --image=busybox:1.36 --quiet \
    --overrides="{\"spec\":{\"containers\":[{\"name\":\"t\",\"image\":\"busybox:1.36\",\"command\":[\"sh\",\"-c\",\"wget -q -T 3 -O - $2 >/dev/null 2>&1 && echo OK || echo NO\"],$SEG,$RES}]}}" 2>/dev/null | tr -d '\r' | grep -E '^(OK|NO)$' | head -1
}
espera() {  # espera <namespace> <OK|NO> <descripción>
  local r; r=$(desde "$1" "http://gitea.gitea.svc:3000/api/healthz")
  if [ "$r" = "$2" ]; then echo "  ✓ $3"; else echo "  ✗ $3 (resultado: '$r')"; fallos=$((fallos+1)); fi
}

espera default NO "desde default no llega a Gitea"
espera mlops NO "desde mlops no llega a Gitea"
espera monitoring NO "desde monitoring no llega a Gitea"
espera hub OK "desde hub (Hub y Backstage) sí llega"

codigo=$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 --resolve gitea.hub.local:80:127.0.0.1 http://gitea.hub.local/api/healthz || true)
if [ "$codigo" = "200" ]; then echo "  ✓ por Traefik (gitea.hub.local) responde 200"; else echo "  ✗ por Traefik responde '$codigo'"; fallos=$((fallos+1)); fi

[ "$fallos" -eq 0 ] && echo "entrada-gitea: todo en orden" || { echo "entrada-gitea: $fallos fallo(s)"; exit 1; }

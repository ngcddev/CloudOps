#!/usr/bin/env bash
# Prueba en el clúster (spec 022, T18): lo que cada aplicación del namespace hub puede y no puede alcanzar. Los Pods de prueba llevan la etiqueta de la aplicación
# (app=api, app=backstage, app=voz) para heredar su política. Uso: KUBECONFIG=... bash gitops/pruebas/salida-hub.sh
set -uo pipefail
export MSYS_NO_PATHCONV=1
fallos=0
SEG='"securityContext":{"allowPrivilegeEscalation":false,"capabilities":{"drop":["ALL"]},"runAsNonRoot":true,"runAsUser":1000,"seccompProfile":{"type":"RuntimeDefault"}}'
RES='"resources":{"requests":{"cpu":"5m","memory":"8Mi"},"limits":{"cpu":"20m","memory":"16Mi"}}'

# «Alcanza» significa que hubo conexión TCP aunque el servicio conteste con un error o con otro protocolo (Postgres); «no alcanza» es tiempo de espera o conexión rechazada.
# Antes de medir el Pod espera 4 s: kube-router instala las reglas del Pod unos instantes después de arrancar y la primera conexión puede colarse (medido: 1.1.1.1 «llegaba» solo al inicio).
# Se usa wget y no `nc -z`: contra direcciones de internet nc daba «conectado» aunque la política rechazara la salida (medido), y wget coincide con lo que hace gitops/pruebas/salida-red.sh.
alcanza() {  # alcanza <app> <host> <puerto>: OK si el Pod con esa etiqueta conecta al puerto, NO si no
  kubectl run "sal-$RANDOM" --rm -i --restart=Never -n hub --image=busybox:1.36 --quiet --labels "app=$1" \
    --overrides="{\"spec\":{\"containers\":[{\"name\":\"t\",\"image\":\"busybox:1.36\",\"command\":[\"sh\",\"-c\",\"sleep 4; o=\$(wget -q -T 3 -O - http://$2:$3/ 2>&1); case \$o in *onnect*|*imed*|*ddress*|*nreachable*) echo NO;; *) echo OK;; esac\"],$SEG,$RES}]}}" 2>/dev/null | tr -d '
' | grep -E '^(OK|NO)$' | head -1
}
espera() {  # espera <app> <host> <puerto> <OK|NO> <descripción>
  local r; r=$(alcanza "$1" "$2" "$3")
  if [ "$r" = "$4" ]; then echo "  ✓ $1: $5"; else echo "  ✗ $1: $5 (resultado: '$r')"; fallos=$((fallos+1)); fi
}

API=api
espera $API postgres.hub.svc 5432 OK "llega a su base de datos"
espera $API voz.hub.svc 8100 OK "llega al servicio de voz"
espera $API gitea.gitea.svc 3000 OK "llega a Gitea"
espera $API argocd-server.argocd.svc 80 OK "llega a Argo CD"
espera $API prometheus.monitoring.svc 9090 OK "llega a Prometheus"
espera $API loki.monitoring.svc 3100 OK "llega a Loki"
espera $API tempo.monitoring.svc 4318 OK "llega al receptor OTLP de Tempo"
espera $API host.docker.internal 11434 OK "llega a Ollama en el host"
espera $API mlflow.mlops.svc 5000 NO "no llega a MLflow"
espera $API alertmanager.monitoring.svc 9093 NO "no llega a Alertmanager"
espera $API grafana.monitoring.svc 3000 NO "no llega a Grafana"
espera $API kubernetes.default.svc 443 NO "no llega a la API de Kubernetes"
espera $API web.cliente-restaurante.svc 80 NO "no llega al sitio de un cliente"
espera $API 1.1.1.1 443 NO "no llega a internet"
espera backstage gitea.gitea.svc 3000 OK "llega a Gitea"
espera backstage postgres.hub.svc 5432 OK "llega a Postgres del Hub (mismo namespace)"
espera backstage prometheus.monitoring.svc 9090 NO "no llega a Prometheus"
espera backstage 1.1.1.1 443 NO "no llega a internet"
espera voz gitea.gitea.svc 3000 NO "no llega a Gitea"
espera voz host.docker.internal 11434 NO "no llega a Ollama"
espera voz 1.1.1.1 443 NO "no llega a internet"

[ "$fallos" -eq 0 ] && echo "salida-hub: todo en orden" || { echo "salida-hub: $fallos fallo(s)"; exit 1; }

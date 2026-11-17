#!/usr/bin/env bash
# Lanza el recorrido de la interfaz (recorrido-ui.py) en el contenedor de Playwright. Las contraseñas salen de los Secret del clúster y viajan solo por el entorno del contenedor.
# Uso: KUBECONFIG=... SALIDA=<carpeta> bash entrega/evidencias/recorrido-ui.sh
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"
SALIDA="${SALIDA:?Falta SALIDA}"; mkdir -p "$SALIDA"
SALIDA_WIN="$(cd "$SALIDA" && (pwd -W 2>/dev/null || pwd))"
cp entrega/evidencias/recorrido-ui.py "$SALIDA/recorrido-ui.py"
HUB_PW="$(kubectl -n hub get secret hub-auth -o jsonpath='{.data.SEED_USER_PASSWORD}' | base64 -d)"
GRAFANA_PW="$(kubectl -n monitoring get secret grafana-admin -o jsonpath='{.data.admin-password}' | base64 -d)"
ARGO_PW="$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d)"
export PASO_SECRETOS_EXTRA="$HUB_PW"$'\n'"$GRAFANA_PW"$'\n'"$ARGO_PW"
MSYS_NO_PATHCONV=1 docker run --rm \
  --add-host hub.local:172.30.0.1 --add-host argocd.hub.local:172.30.0.1 --add-host grafana.hub.local:172.30.0.1 --add-host mlflow.hub.local:172.30.0.1 --add-host gitea.hub.local:172.30.0.1 \
  -e HUB_USER=sofia@forjadigital.test -e HUB_PW="$HUB_PW" -e CLIENTE_USER=contacto@lasazon.test -e CLIENTE_PW="$HUB_PW" -e GRAFANA_PW="$GRAFANA_PW" -e ARGO_PW="$ARGO_PW" \
  -v "$SALIDA_WIN:/out" mcr.microsoft.com/playwright/python:v1.49.1-noble \
  sh -c "pip install -q playwright==1.49.1 >/dev/null 2>&1; python /out/recorrido-ui.py"
rc=$?
rm -f "$SALIDA/recorrido-ui.py"
exit $rc

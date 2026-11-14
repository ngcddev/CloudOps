#!/usr/bin/env bash
# Reinicia la demo del colegio en el clúster k3s (spec 016): deja el Hub con los datos semilla y quita el sitio del colegio,
# para volver a dar de alta el cliente en vivo. Todo por los caminos normales: el sitio sale de hub-gitops (Argo CD lo borra
# solo) y la base del Hub se recrea (la API migra y siembra al encontrarla vacía). No toca el repositorio de código.
#   1. borra clients/colegio de hub-gitops con la API de Gitea (el ApplicationSet retira la Application y su namespace)
#   2. detiene la API, recrea la base `hub` vacía y vuelve a levantar la API
#   3. comprueba que el Hub responde y que el namespace del colegio ya no existe
# Uso:  GITEA_USER=forja-admin GITEA_PASSWORD='...' [KUBECONFIG=...] bash demo/reiniciar-cluster.sh
#   (con las variables de .env.cluster:  set -a; . ./.env.cluster; set +a; GITEA_USER=$GITEA_ADMIN_USER GITEA_PASSWORD=$GITEA_ADMIN_PASSWORD ...)
set -uo pipefail

: "${GITEA_USER:?Falta GITEA_USER}"
: "${GITEA_PASSWORD:?Falta GITEA_PASSWORD}"
GITEA_URL="${GITEA_URL:-http://127.0.0.1}"          # el Ingress del clúster; el nombre va en el encabezado Host
GITEA_HOST="${GITEA_HOST:-gitea.hub.local}"
REPO="${REPO:-forja-digital/hub-gitops}"
SITIO="${SITIO:-colegio}"
NS="cliente-${SITIO}"

paso() { echo "→ $1"; }
fallo() { echo "✗ $1" >&2; exit 1; }
gitea() { curl -s -m 20 -u "${GITEA_USER}:${GITEA_PASSWORD}" -H "Host: ${GITEA_HOST}" -H 'Content-Type: application/json' "$@"; }

paso "Quitando clients/${SITIO} de hub-gitops"
archivos="$(gitea "${GITEA_URL}/api/v1/repos/${REPO}/contents/clients/${SITIO}?ref=main" | grep -o '"path": *"[^"]*"' | sed 's/.*: *"//; s/"$//')"
if [ -z "$archivos" ]; then
  echo "   (no había nada: el sitio ya estaba fuera de GitOps)"
else
  for ruta in $archivos; do
    sha="$(gitea "${GITEA_URL}/api/v1/repos/${REPO}/contents/${ruta}?ref=main" | grep -o '"sha": *"[^"]*"' | head -1 | sed 's/.*: *"//; s/"$//')"
    codigo="$(gitea -o /dev/null -w '%{http_code}' -X DELETE "${GITEA_URL}/api/v1/repos/${REPO}/contents/${ruta}" \
      -d "{\"sha\":\"${sha}\",\"message\":\"chore(${SITIO}): reinicio de la demo\",\"branch\":\"main\"}")"
    [ "$codigo" = "200" ] && echo "   ✓ ${ruta}" || fallo "no se pudo borrar ${ruta} (HTTP ${codigo})"
  done
fi

paso "Recreando la base del Hub vacía"
kubectl -n hub scale deploy/api --replicas=0 >/dev/null || fallo "no se pudo detener la API"
kubectl -n hub wait --for=delete pod -l app=api --timeout=90s >/dev/null 2>&1
db_user="$(kubectl -n hub get secret hub-db -o jsonpath='{.data.POSTGRES_USER}' | base64 -d)"
db_name="$(kubectl -n hub get secret hub-db -o jsonpath='{.data.POSTGRES_DB}' | base64 -d)"
sql() { kubectl -n hub exec statefulset/postgres -- psql -U "$db_user" -d postgres -v ON_ERROR_STOP=1 -q -c "$1" </dev/null; }
sql "DROP DATABASE IF EXISTS \"${db_name}\" WITH (FORCE)" || fallo "no se pudo borrar la base"
sql "CREATE DATABASE \"${db_name}\"" || fallo "no se pudo crear la base"

paso "Levantando la API (migra y siembra)"
kubectl -n hub scale deploy/api --replicas=1 >/dev/null || fallo "no se pudo levantar la API"
kubectl -n hub rollout status deploy/api --timeout=240s >/dev/null || fallo "la API no quedó lista"

paso "Comprobando"
usuarios="$(kubectl -n hub exec statefulset/postgres -- psql -U "$db_user" -d "$db_name" -tAc 'select count(*) from users' </dev/null | tr -d '[:space:]')"
[ "${usuarios:-0}" -gt 0 ] && echo "   ✓ ${usuarios} usuarios sembrados" || fallo "la base no quedó sembrada"
for _ in $(seq 1 30); do kubectl get ns "$NS" >/dev/null 2>&1 || break; sleep 5; done
kubectl get ns "$NS" >/dev/null 2>&1 && echo "   … el namespace ${NS} sigue terminando (Argo CD lo está borrando)" || echo "   ✓ ${NS} ya no existe"
echo "Demo del clúster reiniciada: datos semilla y sin ${SITIO}."

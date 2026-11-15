#!/usr/bin/env bash
# Publica una versión en el ambiente de pruebas de un cliente (spec 017, T03): cambia `newTag` en clients/<cliente>-staging/kustomization.yaml de
# hub-gitops con un commit y espera a que Argo CD la despliegue. No pasa por el Hub ni por la puerta: staging es donde se prueba antes de pedir el cambio.
# Uso:  GITEA_USER=... GITEA_PASSWORD=... KUBECONFIG=... bash gitops/staging/publicar.sh <cliente> <versión>     (por ejemplo: ferreteria v1.1)
set -euo pipefail
CLIENTE="${1:?Uso: publicar.sh <cliente> <versión>}"
VERSION="${2:?Uso: publicar.sh <cliente> <versión>}"
: "${GITEA_USER:?Falta GITEA_USER}"
: "${GITEA_PASSWORD:?Falta GITEA_PASSWORD}"
GITEA_URL="${GITEA_URL:-http://gitea.hub.local}"
REPO="${REPO:-forja-digital/hub-gitops}"
RUTA="clients/${CLIENTE}-staging/kustomization.yaml"
NS="cliente-${CLIENTE}-staging"
case "$VERSION" in *[!A-Za-z0-9._-]*|"") echo "Versión inválida: $VERSION" >&2; exit 2 ;; esac
api() { curl -fsS -m 30 -u "${GITEA_USER}:${GITEA_PASSWORD}" -H 'Content-Type: application/json' "$@"; }

archivo="$(api "${GITEA_URL}/api/v1/repos/${REPO}/contents/${RUTA}?ref=main")" || { echo "No existe ${RUTA} en ${REPO}: el cliente no tiene staging." >&2; exit 1; }
sha="$(echo "$archivo" | sed -n 's/.*"sha": *"\([^"]*\)".*/\1/p' | head -1)"
texto="$(echo "$archivo" | sed -n 's/.*"content": *"\([^"]*\)".*/\1/p' | head -1 | base64 -d)"
actual="$(echo "$texto" | sed -n 's/^ *newTag: *\(.*\)$/\1/p' | tr -d '"')"
[ "$actual" != "$VERSION" ] || { echo "staging de ${CLIENTE} ya está en ${VERSION}."; exit 0; }
nuevo="$(echo "$texto" | sed "s/^\( *newTag: *\).*/\1${VERSION}/")"
contenido="$(printf '%s\n' "$nuevo" | base64 -w0)"
api -X PUT "${GITEA_URL}/api/v1/repos/${REPO}/contents/${RUTA}" \
  -d "{\"content\":\"${contenido}\",\"sha\":\"${sha}\",\"branch\":\"main\",\"message\":\"chore(${CLIENTE}-staging): versión ${VERSION} a prueba\"}" >/dev/null
echo "→ staging de ${CLIENTE}: ${actual} → ${VERSION} (commit en ${REPO})"

echo "→ Esperando a Argo CD"
imagen=""
for _ in $(seq 1 45); do
  imagen="$(kubectl -n "$NS" get deploy web -o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null || true)"
  [ "${imagen##*:}" = "$VERSION" ] && break
  sleep 2
done
[ "${imagen##*:}" = "$VERSION" ] || { echo "   Argo CD no desplegó ${VERSION} a tiempo (imagen actual: ${imagen:-ninguna})" >&2; exit 1; }
# Una versión rota no llega a Ready: no es un error de este script, es justo lo que staging debe mostrar
for _ in $(seq 1 30); do
  listas="$(kubectl -n "$NS" get deploy web -o jsonpath='{.status.readyReplicas}' 2>/dev/null || true)"
  actualizadas="$(kubectl -n "$NS" get deploy web -o jsonpath='{.status.updatedReplicas}' 2>/dev/null || true)"
  [ "${listas:-0}" -ge 1 ] && [ "${actualizadas:-0}" -ge 1 ] && break
  sleep 2
done
listas="$(kubectl -n "$NS" get deploy web -o jsonpath='{.status.readyReplicas}' 2>/dev/null || true)"
if [ "${listas:-0}" -ge 1 ]; then
  echo "   ${VERSION} desplegada y lista en ${NS}"
else
  echo "   ${VERSION} desplegada en ${NS} pero NO queda lista (el Pod nuevo no pasa su readiness): no debe promoverse"
fi

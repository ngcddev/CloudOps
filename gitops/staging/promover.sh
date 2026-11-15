#!/usr/bin/env bash
# Promueve a producción la versión que está en staging (spec 017, T03), solo si ahí está sana:
#   1. lee de hub-gitops la versión de staging y la de producción de un cliente
#   2. comprueba que staging corre esa versión y que su /health responde 200 con esa versión
#   3. si falla, NO promueve: producción sigue como estaba
#   4. si está sana, pide el cambio por el camino normal del Hub (ticket → solicitud de cambio → puerta de seguridad → aprobación): el Hub escribe el commit de
#      producción y Argo CD lo despliega. Staging prueba la versión; el Hub sigue siendo quien gobierna producción.
# Uso:  GITEA_USER=... GITEA_PASSWORD=... HUB_PASSWORD=... KUBECONFIG=... bash gitops/staging/promover.sh <cliente>
#       (HUB_USUARIO=sofia@forjadigital.test por defecto; HUB=http://hub.local; GITEA_URL=http://gitea.hub.local)
set -uo pipefail
CLIENTE="${1:?Uso: promover.sh <cliente>}"
: "${GITEA_USER:?Falta GITEA_USER}"
: "${GITEA_PASSWORD:?Falta GITEA_PASSWORD}"
: "${HUB_PASSWORD:?Falta HUB_PASSWORD (kubectl -n hub get secret hub-auth -o jsonpath='{.data.SEED_USER_PASSWORD}' | base64 -d)}"
GITEA_URL="${GITEA_URL:-http://gitea.hub.local}"
HUB="${HUB:-http://hub.local}"
HUB_USUARIO="${HUB_USUARIO:-sofia@forjadigital.test}"
REPO="${REPO:-forja-digital/hub-gitops}"
NS_STAGING="cliente-${CLIENTE}-staging"
NS_PROD="cliente-${CLIENTE}"

paso() { echo "→ $1"; }
fallo() { echo "✗ $1" >&2; exit 1; }
api() { curl -fsS -m 30 -u "${GITEA_USER}:${GITEA_PASSWORD}" "$@"; }
etiqueta_de() { # ruta en hub-gitops → newTag
  api "${GITEA_URL}/api/v1/repos/${REPO}/contents/$1?ref=main" | sed -n 's/.*"content": *"\([^"]*\)".*/\1/p' | head -1 | base64 -d | sed -n 's/^ *newTag: *\(.*\)$/\1/p' | tr -d '"\r'
}
campo() { grep -o "\"$1\": *\"\{0,1\}[^\",}]*" | head -1 | sed "s/^\"$1\": *\"\{0,1\}//"; }

paso "Versiones en hub-gitops"
STAGING="$(etiqueta_de "clients/${CLIENTE}-staging/kustomization.yaml")" || fallo "no existe el staging de ${CLIENTE}"
PROD="$(etiqueta_de "clients/${CLIENTE}/kustomization.yaml")" || fallo "no existe el cliente ${CLIENTE}"
echo "   staging: ${STAGING} · producción: ${PROD}"
[ "$STAGING" != "$PROD" ] || { echo "Nada que promover: staging y producción ya están en ${PROD}."; exit 0; }

paso "Comprobando staging (${NS_STAGING})"
imagen="$(kubectl -n "$NS_STAGING" get deploy web -o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null)" || fallo "staging no está desplegado"
[ "${imagen##*:}" = "$STAGING" ] || fallo "staging corre ${imagen##*:} y Git dice ${STAGING}: espere a Argo CD o corra publicar.sh"
deseadas="$(kubectl -n "$NS_STAGING" get deploy web -o jsonpath='{.spec.replicas}')"
listas="$(kubectl -n "$NS_STAGING" get deploy web -o jsonpath='{.status.readyReplicas}')"
actualizadas="$(kubectl -n "$NS_STAGING" get deploy web -o jsonpath='{.status.updatedReplicas}')"
# Con una versión rota el Pod nuevo nunca queda Ready y el anterior sigue sirviendo: eso no es «sana»
if [ "${listas:-0}" != "$deseadas" ] || [ "${actualizadas:-0}" != "$deseadas" ]; then
  fallo "la versión ${STAGING} no queda lista en staging (listas ${listas:-0}/${deseadas}, actualizadas ${actualizadas:-0}): no se promueve; producción sigue en ${PROD}"
fi
salud="$(kubectl -n "$NS_STAGING" exec deploy/web -- wget -qO- http://127.0.0.1:8080/health 2>&1)" || salud="${salud:-sin respuesta}"
if [ "$(echo "$salud" | campo status)" = "ok" ] && [ "$(echo "$salud" | campo version)" = "$STAGING" ]; then
  echo "   /health: ${salud}"
else
  echo "   /health: ${salud}"
  fallo "la versión ${STAGING} NO está sana en staging: no se promueve; producción sigue en ${PROD}"
fi

paso "Pidiendo el cambio ${PROD} → ${STAGING} por el Hub"
TOKEN="$(curl -fsS -m 15 -H 'Content-Type: application/json' -X POST "${HUB}/api/auth/login" -d "{\"email\":\"${HUB_USUARIO}\",\"password\":\"${HUB_PASSWORD}\"}" | campo access_token)"
[ -n "$TOKEN" ] || fallo "no se pudo entrar al Hub como ${HUB_USUARIO}"
# Segregación de funciones (spec 018): quien pide el cambio no lo aprueba; lo aprueba otra cuenta de la agencia
HUB_USUARIO_APROBADOR="${HUB_USUARIO_APROBADOR:-camilo@forjadigital.test}"
TOKEN_APROBADOR="$(curl -fsS -m 15 -H 'Content-Type: application/json' -X POST "${HUB}/api/auth/login" -d "{\"email\":\"${HUB_USUARIO_APROBADOR}\",\"password\":\"${HUB_PASSWORD}\"}" | campo access_token)"
[ -n "$TOKEN_APROBADOR" ] || fallo "no se pudo entrar al Hub como ${HUB_USUARIO_APROBADOR}"
hub() { curl -sS -m 30 -H "Authorization: Bearer ${TOKEN}" -H 'Content-Type: application/json' "$@"; }
# El cuerpo va por archivo: con tildes en la línea de comandos, curl de Windows lo manda en otra codificación y el Hub responde «error parsing the body»
CUERPO="$(mktemp)"; trap 'rm -f "$CUERPO"' EXIT
ruta_curl() { if command -v cygpath >/dev/null 2>&1; then cygpath -m "$1"; else echo "$1"; fi; }
enviar() { printf '%s' "$2" > "$CUERPO"; hub -X POST "$1" --data-binary "@$(ruta_curl "$CUERPO")"; }
SERVICIO="$(hub "${HUB}/api/services/status" | tr '{' '\n' | grep "\"${NS_PROD}\"" | campo service_id)"
[ -n "$SERVICIO" ] || fallo "el Hub no conoce el servicio ${NS_PROD}"
ticket="$(enviar "${HUB}/api/tickets" "{\"service_id\":${SERVICIO},\"title\":\"Promover ${STAGING} de staging a producción\",\"description\":\"Probada en ${NS_STAGING} (spec 017, T03).\",\"kind\":\"cambio\"}")"
CAMBIO="$(enviar "${HUB}/api/change-requests" "{\"ticket_id\":$(echo "$ticket" | campo id),\"to_version\":\"${STAGING}\"}" | campo id)"
[ -n "$CAMBIO" ] || fallo "no se pudo registrar el cambio a ${STAGING}: ticket=${ticket}"
aprobado="$(TOKEN="$TOKEN_APROBADOR" enviar "${HUB}/api/change-requests/${CAMBIO}/approve" '{}')"
sha="$(echo "$aprobado" | campo gitops_commit_sha)"
[ -n "$sha" ] || fallo "el Hub no aprobó el cambio (¿la puerta de seguridad de ${STAGING} no está en ok?): ${aprobado}"
echo "   cambio #${CAMBIO} aprobado: commit ${sha:0:7} en hub-gitops"

paso "Esperando a Argo CD en producción"
for _ in $(seq 1 90); do
  imagen="$(kubectl -n "$NS_PROD" get deploy web -o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null)"
  listos="$(kubectl -n "$NS_PROD" get deploy web -o jsonpath='{.status.readyReplicas}' 2>/dev/null)"
  [ "${imagen##*:}" = "$STAGING" ] && [ "${listos:-0}" -ge 1 ] && break
  sleep 2
done
[ "${imagen##*:}" = "$STAGING" ] || fallo "producción no llegó a ${STAGING} (imagen: ${imagen})"
echo "✓ ${CLIENTE} en producción: ${PROD} → ${STAGING}, promovida desde staging"

#!/usr/bin/env bash
# Crea los tokens con los que el Hub habla con Gitea y Argo CD y los guarda en el Secret
# `hub-gitops-tokens` del namespace hub (spec 005, T04). Nada se escribe en el repo ni en pantalla.
#
#   · Gitea: el usuario `hub-bot` solo es colaborador con escritura de forja-digital/hub-gitops, y su
#     token tiene el alcance write:repository. Así el token no puede tocar ningún otro repo.
#   · Argo CD: la cuenta local `hub-readonly` con el rol readonly y un token de solo lectura.
#
# Uso:  GITEA_ADMIN_USER=forja-admin GITEA_ADMIN_PASSWORD='...' bash gitops/hub/crear-tokens.sh
# Necesita kubectl con acceso al clúster y las entradas de hosts de gitops/README.md.
# Si el Secret ya existe no se toca; para rotarlo, bórralo y vuelve a correr el script.
set -euo pipefail

NS="${NS:-hub}"
GITEA_URL="${GITEA_URL:-http://gitea.hub.local}"
ARGOCD_URL="${ARGOCD_URL:-http://argocd.hub.local}"
ORG="${ORG:-forja-digital}"
REPO="${REPO:-hub-gitops}"
BOT=hub-bot
CUENTA_ARGOCD=hub-readonly
: "${GITEA_ADMIN_USER:?Falta GITEA_ADMIN_USER}"
: "${GITEA_ADMIN_PASSWORD:?Falta GITEA_ADMIN_PASSWORD}"

if kubectl -n "$NS" get secret hub-gitops-tokens >/dev/null 2>&1; then
  echo "El Secret hub-gitops-tokens ya existe en $NS: no se cambia."
  exit 0
fi

# Sin Python (en Windows suele ser solo un alias): clave con /dev/urandom y campos JSON con sed
aleatoria() { head -c 48 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 24; }
campo() { sed -n "s/.*\"$1\" *: *\"\([^\"]*\)\".*/\1/p" | head -1; }

# ---------- Gitea: usuario hub-bot con escritura solo en hub-gitops ----------
CLAVE_BOT="$(aleatoria)"   # solo sirve para pedir el token; no se guarda
if ! curl -sf -u "${GITEA_ADMIN_USER}:${GITEA_ADMIN_PASSWORD}" "${GITEA_URL}/api/v1/users/${BOT}" >/dev/null; then
  echo ">> Creando el usuario ${BOT} en Gitea"
  curl -sf -u "${GITEA_ADMIN_USER}:${GITEA_ADMIN_PASSWORD}" -H 'Content-Type: application/json' \
    -X POST "${GITEA_URL}/api/v1/admin/users" \
    -d "{\"username\":\"${BOT}\",\"email\":\"hub-bot@forja.test\",\"password\":\"${CLAVE_BOT}\",\"must_change_password\":false}" >/dev/null
else
  # El usuario ya existía: se le fija una clave nueva para poder emitir el token
  curl -sf -u "${GITEA_ADMIN_USER}:${GITEA_ADMIN_PASSWORD}" -H 'Content-Type: application/json' \
    -X PATCH "${GITEA_URL}/api/v1/admin/users/${BOT}" \
    -d "{\"login_name\":\"${BOT}\",\"source_id\":0,\"password\":\"${CLAVE_BOT}\",\"must_change_password\":false}" >/dev/null
fi
curl -sf -u "${GITEA_ADMIN_USER}:${GITEA_ADMIN_PASSWORD}" -H 'Content-Type: application/json' \
  -X PUT "${GITEA_URL}/api/v1/repos/${ORG}/${REPO}/collaborators/${BOT}" -d '{"permission":"write"}' >/dev/null
GITEA_TOKEN="$(curl -sf -u "${BOT}:${CLAVE_BOT}" -H 'Content-Type: application/json' \
  -X POST "${GITEA_URL}/api/v1/users/${BOT}/tokens" \
  -d "{\"name\":\"hub-$(date +%Y%m%d%H%M%S)\",\"scopes\":[\"write:repository\"]}" | campo sha1)"

# ---------- Argo CD: cuenta hub-readonly con token de solo lectura ----------
kubectl -n argocd patch configmap argocd-cm --type merge \
  -p "{\"data\":{\"accounts.${CUENTA_ARGOCD}\":\"apiKey\"}}" >/dev/null
# policy.csv es una sola cadena: se le agrega la regla sin pisar las que ya tenga
REGLA="g, ${CUENTA_ARGOCD}, role:readonly"
POLITICAS="$(kubectl -n argocd get configmap argocd-rbac-cm -o jsonpath='{.data.policy\.csv}')"
if ! printf '%s\n' "$POLITICAS" | grep -qxF "$REGLA"; then
  NUEVAS="${POLITICAS:+${POLITICAS}$'\n'}${REGLA}"
  NUEVAS_JSON="$(printf '%s' "$NUEVAS" | sed -e ':a' -e 'N' -e '$!ba' -e 's/\\/\\\\/g' -e 's/"/\\"/g' -e 's/\n/\\n/g')"
  kubectl -n argocd patch configmap argocd-rbac-cm --type merge \
    -p "{\"data\":{\"policy.csv\":\"${NUEVAS_JSON}\"}}" >/dev/null
fi
CLAVE_ADMIN="$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d)"
SESION="$(curl -sf -H 'Content-Type: application/json' -X POST "${ARGOCD_URL}/api/v1/session" \
  -d "{\"username\":\"admin\",\"password\":\"${CLAVE_ADMIN}\"}" | campo token)"
ARGOCD_TOKEN="$(curl -sf -H "Authorization: Bearer ${SESION}" -H 'Content-Type: application/json' \
  -X POST "${ARGOCD_URL}/api/v1/account/${CUENTA_ARGOCD}/token" -d '{}' | campo token)"

# Un campo que no vino en la respuesta daría un token vacío y un Secret "creado" que no sirve
[ -n "$GITEA_TOKEN" ] || { echo "Gitea no devolvió el token de ${BOT}: no se crea el Secret." >&2; exit 1; }
[ -n "$ARGOCD_TOKEN" ] || { echo "Argo CD no devolvió el token de ${CUENTA_ARGOCD}: no se crea el Secret." >&2; exit 1; }

kubectl -n "$NS" create secret generic hub-gitops-tokens \
  --from-literal=GITEA_TOKEN="$GITEA_TOKEN" \
  --from-literal=ARGOCD_TOKEN="$ARGOCD_TOKEN"
echo "Secret hub-gitops-tokens creado en $NS."

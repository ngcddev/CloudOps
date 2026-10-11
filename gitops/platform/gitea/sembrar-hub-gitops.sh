#!/usr/bin/env bash
# Crea el repo forja-digital/hub-gitops en Gitea y lo siembra con platform/, hub/ y clients/ de gitops/
# (spec 005, T02). Es el repo que Argo CD vigila y donde el Hub escribe los cambios de versión.
# Uso:  GITEA_USER=forja-admin GITEA_PASSWORD='...' bash gitops/platform/gitea/sembrar-hub-gitops.sh
# Si el repo ya tiene commits no se toca: a partir de aquí el contenido cambia solo por PR del Hub o
# a mano en Gitea. La contraseña va en el entorno: nunca en el repo ni en la URL del remoto.
set -euo pipefail

GITEA_URL="${GITEA_URL:-http://gitea.hub.local}"
ORG="${ORG:-forja-digital}"
REPO="${REPO:-hub-gitops}"
: "${GITEA_USER:?Falta GITEA_USER}"
: "${GITEA_PASSWORD:?Falta GITEA_PASSWORD}"

RAIZ="$(cd "$(dirname "$0")/../../.." && pwd)"
API="${GITEA_URL}/api/v1"
curl_api() { curl -sS -u "${GITEA_USER}:${GITEA_PASSWORD}" -H 'Content-Type: application/json' "$@"; }

codigo="$(curl_api -o /dev/null -w '%{http_code}' "${API}/repos/${ORG}/${REPO}")"
if [ "$codigo" = "404" ]; then
  echo ">> Creando ${ORG}/${REPO}"
  curl_api -f -X POST "${API}/orgs/${ORG}/repos" \
    -d "{\"name\":\"${REPO}\",\"private\":false,\"default_branch\":\"main\",\"description\":\"Configuración que Argo CD reconcilia (CloudOps Client Hub)\"}" >/dev/null
elif [ "$codigo" != "200" ]; then
  echo "Gitea respondió ${codigo} al consultar el repo: ¿está arriba y existe la organización ${ORG}?" >&2
  exit 1
fi

if [ "$(curl_api "${API}/repos/${ORG}/${REPO}/commits?limit=1" | head -c 2)" != "[]" ]; then
  echo "${ORG}/${REPO} ya tiene commits: no se vuelve a sembrar."
  exit 0
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
cp -r "${RAIZ}/gitops/platform" "${RAIZ}/gitops/hub" "${RAIZ}/gitops/clients" "$TMP/"
cd "$TMP"
git init -q -b main
git add .
git -c user.name="Forja Digital" -c user.email="hub@forja.test" \
  commit -q -m "chore: sembrar hub-gitops desde gitops/ del monorepo (spec 005)"
# La credencial va en un encabezado, no en la URL, para que no quede en la configuración del repo
AUTH="$(printf '%s:%s' "$GITEA_USER" "$GITEA_PASSWORD" | base64 | tr -d '\n')"
git -c "http.extraHeader=Authorization: Basic ${AUTH}" push -q "${GITEA_URL}/${ORG}/${REPO}.git" main
echo "Listo: ${GITEA_URL}/${ORG}/${REPO}"

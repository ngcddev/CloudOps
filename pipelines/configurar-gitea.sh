#!/usr/bin/env bash
# Deja Gitea listo para la puerta de seguridad (spec 006, T03 y T04): organización, par de claves de Cosign,
# secretos y variables de Gitea Actions. Se puede repetir sin romper nada.
#
# Uso:
#   GITEA_ADMIN_USER=forja-admin GITEA_ADMIN_PASSWORD='<contraseña>' bash pipelines/configurar-gitea.sh
#
# Qué hace:
#   1. Crea la organización forja-digital si no existe.
#   2. Si falta pipelines/cosign.pub, genera el par de claves de Cosign: la pública queda en el repositorio y
#      la privada y su contraseña van directo a los secretos de Gitea (nunca a un archivo). Con --rotar-claves
#      se generan unas nuevas (las versiones firmadas antes dejan de verificarse).
#   3. Carga los secretos de la organización: HUB_URL, HUB_PIPELINE_TOKEN, REGISTRY_USER, REGISTRY_PASSWORD,
#      COSIGN_PRIVATE_KEY y COSIGN_PASSWORD; y las variables REGISTRY, REGISTRY_IP y DOCKER_NETWORK.
#
# Variables opcionales:
#   GITEA_URL            dirección de Gitea (por defecto http://gitea.hub.local)
#   ORG                  organización (forja-digital)
#   HUB_URL              dirección del Hub vista desde el runner (http://hub.local)
#   HUB_PIPELINE_TOKEN   token de la puerta; si falta se lee del Secret hub-pipeline del clúster
#   REGISTRY_USER / REGISTRY_PASSWORD   quien sube las imágenes al registro (por defecto, el administrador)
#   REGISTRY / REGISTRY_IP / DOCKER_NETWORK   cómo el runner llega al registro (gitea.hub.local, 172.30.0.1, k3d-hub)
set -euo pipefail

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GITEA_URL="${GITEA_URL:-http://gitea.hub.local}"
ORG="${ORG:-forja-digital}"
HUB_URL="${HUB_URL:-http://hub.local}"
: "${GITEA_ADMIN_USER:?Falta GITEA_ADMIN_USER}"
: "${GITEA_ADMIN_PASSWORD:?Falta GITEA_ADMIN_PASSWORD}"
REGISTRY_USER="${REGISTRY_USER:-$GITEA_ADMIN_USER}"
REGISTRY_PASSWORD="${REGISTRY_PASSWORD:-$GITEA_ADMIN_PASSWORD}"
REGISTRY="${REGISTRY:-gitea.hub.local}"
REGISTRY_IP="${REGISTRY_IP-172.30.0.1}"      # vacío = no hace falta traducir el nombre del registro
DOCKER_NETWORK="${DOCKER_NETWORK-k3d-hub}"     # vacío = la red por defecto de Docker
ROTAR=0
[ "${1:-}" = "--rotar-claves" ] && ROTAR=1

# shellcheck source=lib.sh
source "$AQUI/lib.sh"
API="${GITEA_URL%/}/api/v1"
curl_api() { curl -sS -m 30 -u "${GITEA_ADMIN_USER}:${GITEA_ADMIN_PASSWORD}" -H 'Content-Type: application/json' "$@"; }
# Código HTTP de una llamada (el cuerpo se descarta); no usa -o /dev/null, que falla con el curl de Windows
codigo() { local salida; salida="$(curl_api -w $'
%{http_code}' "$@")" || true; printf '%s' "${salida##*$'
'}"; }

# 1. Organización
if [ "$(codigo "${API}/orgs/${ORG}")" = "404" ]; then
  [ "$(codigo -X POST "${API}/orgs" -d "{\"username\":\"${ORG}\",\"visibility\":\"public\"}")" = "201" ] \
    && echo "Organización ${ORG} creada." || { echo "No se pudo crear la organización ${ORG}." >&2; exit 1; }
else
  echo "La organización ${ORG} ya existe."
fi

# Un secreto de la organización; el valor viaja por stdin para que no quede en la lista de procesos
poner_secreto() {  # poner_secreto <nombre> <valor>
  local nombre="$1" cuerpo resultado
  cuerpo="$(printf '%s' "$2" | jq_run -Rs '{data: .}')"
  resultado="$(printf '%s' "$cuerpo" | codigo -X PUT "${API}/orgs/${ORG}/actions/secrets/${nombre}" --data-binary @-)"
  case "$resultado" in
    201|204) echo "Secreto ${nombre} guardado." ;;
    *) echo "No se pudo guardar el secreto ${nombre} (HTTP ${resultado})." >&2; exit 1 ;;
  esac
}

# Una variable de la organización: se crea o, si ya existe, se actualiza
poner_variable() {  # poner_variable <nombre> <valor>
  local nombre="$1" cuerpo resultado
  cuerpo="$(printf '%s' "$2" | jq_run -Rs '{value: .}')"
  resultado="$(printf '%s' "$cuerpo" | codigo -X POST "${API}/orgs/${ORG}/actions/variables/${nombre}" --data-binary @-)"
  if [ "$resultado" = "409" ]; then
    resultado="$(printf '%s' "$cuerpo" | codigo -X PUT "${API}/orgs/${ORG}/actions/variables/${nombre}" --data-binary @-)"
  fi
  case "$resultado" in
    200|201|204) echo "Variable ${nombre} = $2" ;;
    *) echo "No se pudo guardar la variable ${nombre} (HTTP ${resultado})." >&2; exit 1 ;;
  esac
}

# 2. Claves de Cosign: la pública al repositorio, la privada directo a Gitea
if [ ! -f "$AQUI/cosign.pub" ] || [ "$ROTAR" = "1" ]; then
  temporal="$(mktemp -d)"
  trap 'rm -rf "$temporal"' EXIT
  temporal_host="$(cd "$temporal" && (pwd -W 2>/dev/null || pwd))"
  clave="$(head -c 48 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 24)"
  docker run --rm -e COSIGN_PASSWORD="$clave" -v "${temporal_host}:/k" -w /k "$COSIGN_IMAGE" generate-key-pair >/dev/null
  cp "$temporal/cosign.pub" "$AQUI/cosign.pub"
  poner_secreto COSIGN_PRIVATE_KEY "$(cat "$temporal/cosign.key")"
  poner_secreto COSIGN_PASSWORD "$clave"
  echo "Clave pública nueva en pipelines/cosign.pub: súbela al repositorio (git add pipelines/cosign.pub)."
else
  echo "Ya existe pipelines/cosign.pub: se conservan las claves (usa --rotar-claves para cambiarlas)."
fi

# 3. Resto de secretos y variables
if [ -z "${HUB_PIPELINE_TOKEN:-}" ]; then
  HUB_PIPELINE_TOKEN="$(kubectl -n hub get secret hub-pipeline -o jsonpath='{.data.PIPELINE_TOKEN}' 2>/dev/null | base64 -d || true)"
  [ -n "$HUB_PIPELINE_TOKEN" ] || { echo "Falta HUB_PIPELINE_TOKEN y no se pudo leer del Secret hub-pipeline." >&2; exit 1; }
fi
poner_secreto HUB_URL "$HUB_URL"
poner_secreto HUB_PIPELINE_TOKEN "$HUB_PIPELINE_TOKEN"
poner_secreto REGISTRY_USER "$REGISTRY_USER"
poner_secreto REGISTRY_PASSWORD "$REGISTRY_PASSWORD"
poner_variable REGISTRY "$REGISTRY"
[ -z "$REGISTRY_IP" ] || poner_variable REGISTRY_IP "$REGISTRY_IP"
[ -z "$DOCKER_NETWORK" ] || poner_variable DOCKER_NETWORK "$DOCKER_NETWORK"
echo "Listo: Gitea configurado para la puerta de seguridad."

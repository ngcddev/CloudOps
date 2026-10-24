#!/usr/bin/env bash
# Funciones comunes de la puerta de seguridad (spec 006): se cargan con `source` desde puerta.sh y reportar.sh.
# El runner solo necesita Docker, git, curl y bash: todas las herramientas corren en contenedores con versión fija.

# Versiones fijas de las herramientas (se pueden cambiar por variable de entorno)
GITLEAKS_IMAGE="${GITLEAKS_IMAGE:-zricethezav/gitleaks:v8.30.1}"
TRIVY_IMAGE="${TRIVY_IMAGE:-aquasec/trivy:0.76.1}"
SYFT_IMAGE="${SYFT_IMAGE:-anchore/syft:v1.55.0}"
COSIGN_IMAGE="${COSIGN_IMAGE:-ghcr.io/sigstore/cosign/cosign:v3.1.4}"
SKOPEO_IMAGE="${SKOPEO_IMAGE:-quay.io/skopeo/stable:v1.22.3}"
JQ_IMAGE="${JQ_IMAGE:-ghcr.io/jqlang/jq:1.8.1}"

# En Git Bash (Windows) Docker necesita la ruta de Windows y que no se reescriban las rutas de los contenedores
export MSYS_NO_PATHCONV=1
HOST_PWD="$(pwd -W 2>/dev/null || pwd)"

# jq local si existe; si no, el de un contenedor. Todo entra por stdin.
jq_run() {
  if command -v jq >/dev/null 2>&1; then
    jq "$@"
  else
    docker run --rm -i "$JQ_IMAGE" "$@"
  fi
}

# docker run con la red y el nombre del registro del laboratorio, si se indicaron
# (DOCKER_NETWORK=k3d-hub y REGISTRY_IP=172.30.0.1 hacen que gitea.hub.local se resuelva dentro del contenedor)
docker_run() {
  local args=(--rm)
  [ -n "${DOCKER_NETWORK:-}" ] && args+=(--network "$DOCKER_NETWORK")
  [ -n "${REGISTRY_IP:-}" ] && args+=(--add-host "${REGISTRY}:${REGISTRY_IP}")
  docker run "${args[@]}" "$@"
}

#!/usr/bin/env bash
# Construye y publica en el registro de Gitea las imágenes de los sitios de clientes (spec 003, T06):
# restaurante, ferreteria, consultorio-web y consultorio-api, cada una en v1 (sana) y v2 (rota, 500).
# También las del Hub (T17): hub-api y hub-web, solo en v1. Se piden por nombre; no se publican por defecto.
# Uso:  REGISTRY_USER=forja-admin REGISTRY_PASSWORD='...' bash apps/publicar-imagenes.sh [app ...]
# Sin argumentos publica las cuatro de los sitios. La contraseña va en el entorno: nunca en el repo.
#
# Se sube con skopeo en un contenedor (Docker no confía en un registro HTTP que no sea localhost) y
# `--network k3d-hub`, la red del clúster de desarrollo, donde gitea.hub.local apunta al host.
set -euo pipefail
cd "$(dirname "$0")"

REGISTRY="${REGISTRY:-gitea.hub.local}"
ORG="${ORG:-forja-digital}"
REGISTRY_IP="${REGISTRY_IP:-172.30.0.1}"
NETWORK="${NETWORK:-k3d-hub}"
: "${REGISTRY_USER:?Falta REGISTRY_USER}"
: "${REGISTRY_PASSWORD:?Falta REGISTRY_PASSWORD}"

# app -> carpeta de contexto y Dockerfile
declare -A CONTEXT=( [restaurante]=restaurante [ferreteria]=ferreteria [consultorio-web]=consultorio [consultorio-api]=consultorio [hub-api]=../backend [hub-web]=../frontend )
declare -A DOCKERFILE=( [restaurante]=Dockerfile [ferreteria]=Dockerfile [consultorio-web]=Dockerfile.frontend [consultorio-api]=Dockerfile.backend [hub-api]=Dockerfile [hub-web]=Dockerfile )
# Versiones por app y opciones extra de build (el Hub necesita seed/ como contexto adicional)
declare -A VERSIONS=( [hub-api]=v1 [hub-web]=v1 )
declare -A EXTRA=( [hub-api]="--build-context seed=../seed" [hub-web]="--build-context seed=../seed" )

APPS=("$@")
[ ${#APPS[@]} -eq 0 ] && APPS=(restaurante ferreteria consultorio-web consultorio-api)

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
# Ruta que Docker pueda montar: en Git Bash (Windows) hace falta la ruta de Windows
MOUNT="$(cd "$TMP" && (pwd -W 2>/dev/null || pwd))"

for app in "${APPS[@]}"; do
  for version in ${VERSIONS[$app]:-v1 v2}; do
    local_tag="hub/${app}:${version}"
    echo ">> ${app}:${version}"
    docker build -q ${EXTRA[$app]:-} --build-arg "APP_VERSION=${version}" \
      -f "${CONTEXT[$app]}/${DOCKERFILE[$app]}" -t "$local_tag" "${CONTEXT[$app]}" >/dev/null
    docker save "$local_tag" -o "$TMP/${app}-${version}.tar"
    MSYS_NO_PATHCONV=1 docker run --rm --network "$NETWORK" --add-host "${REGISTRY}:${REGISTRY_IP}" \
      -v "${MOUNT}:/w" quay.io/skopeo/stable copy --dest-tls-verify=false \
      --dest-creds "${REGISTRY_USER}:${REGISTRY_PASSWORD}" \
      "docker-archive:/w/${app}-${version}.tar" "docker://${REGISTRY}/${ORG}/${app}:${version}"
    rm -f "$TMP/${app}-${version}.tar"
  done
done
echo "Listo: imágenes publicadas en ${REGISTRY}/${ORG}/"

#!/usr/bin/env bash
# Ejecuta OpenTofu o Terraform en contenedores con versiones fijadas (spec 011, T02).
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
NETWORK="${NETWORK:-k3d-hub}"

usage() {
  echo "Uso: infra/tofu.sh <tofu|terraform> <comando> [argumentos…]" >&2
  exit 2
}

[[ $# -ge 2 ]] || usage
TOOL="$1"
shift

case "$TOOL" in
  tofu)
    IMAGE="ghcr.io/opentofu/opentofu:1.13.2"
    ;;
  terraform)
    IMAGE="hashicorp/terraform:1.17.0"
    ;;
  *)
    echo "Herramienta inválida: $TOOL (usa tofu o terraform)." >&2
    usage
    ;;
esac

command -v docker >/dev/null 2>&1 || {
  echo "No se encontró Docker en PATH." >&2
  exit 1
}

# Consultar la versión no requiere que el clúster esté iniciado.
case "${1:-}" in
  version|-version|--version|help|-help|--help)
    exec docker run --rm "$IMAGE" "$@"
    ;;
esac

K3D_BIN="${K3D_BIN:-}"
if [[ -z "$K3D_BIN" ]]; then
  if command -v k3d >/dev/null 2>&1; then
    K3D_BIN="k3d"
  elif command -v k3d.exe >/dev/null 2>&1; then
    K3D_BIN="k3d.exe"
  elif command -v cmd.exe >/dev/null 2>&1; then
    WINDOWS_K3D="$(cmd.exe /c where k3d.exe 2>/dev/null | tr -d '\r' | head -n 1 || true)"
    if [[ -n "$WINDOWS_K3D" ]] && command -v wslpath >/dev/null 2>&1; then
      K3D_BIN="$(wslpath -u "$WINDOWS_K3D")"
    elif [[ -n "$WINDOWS_K3D" ]] && command -v cygpath >/dev/null 2>&1; then
      K3D_BIN="$(cygpath -u "$WINDOWS_K3D")"
    fi
  fi
fi
[[ -n "$K3D_BIN" ]] || {
  echo "No se encontró k3d en PATH; inicia el clúster hub antes de ejecutar $TOOL." >&2
  exit 1
}

docker network inspect "$NETWORK" >/dev/null 2>&1 || {
  echo "No existe la red Docker '$NETWORK'; inicia el clúster k3d hub." >&2
  exit 1
}

SERVERLB_IP="$(docker inspect --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' k3d-hub-serverlb 2>/dev/null || true)"
if [[ -z "$SERVERLB_IP" ]]; then
  echo "No se encontró la IP de k3d-hub-serverlb en la red Docker." >&2
  exit 1
fi

KUBECONFIG_PATH="$SCRIPT_DIR/.kubeconfig"
KUBECONFIG_TMP="${KUBECONFIG_PATH}.tmp.$$"
trap 'rm -f "$KUBECONFIG_TMP"' EXIT
if ! "$K3D_BIN" kubeconfig get hub > "$KUBECONFIG_TMP"; then
  echo "No se pudo generar el kubeconfig del clúster k3d hub." >&2
  exit 1
fi
if ! grep -q '^[[:space:]]*server:' "$KUBECONFIG_TMP"; then
  echo "El kubeconfig generado no contiene un endpoint de API." >&2
  exit 1
fi
sed -E 's#^([[:space:]]*server: ).*#\1https://k3d-hub-serverlb:6443#' \
  "$KUBECONFIG_TMP" > "$KUBECONFIG_PATH"
rm -f "$KUBECONFIG_TMP"
trap - EXIT

# pwd -W conserva una ruta montable por Docker Desktop cuando se ejecuta desde Git Bash.
MOUNT_DIR="$(cd "$SCRIPT_DIR" && (pwd -W 2>/dev/null || pwd))"
SEED_MOUNT_DIR="$(cd "$SCRIPT_DIR/../seed" && (pwd -W 2>/dev/null || pwd))"
DOCKER_ARGS=(
  run --rm
  --network "$NETWORK"
  --add-host "gitea.hub.local:${SERVERLB_IP}"
  -e KUBECONFIG=/infra/.kubeconfig
  -e KUBE_CONFIG_PATH=/infra/.kubeconfig
  -v "${MOUNT_DIR}:/infra"
  -v "${MOUNT_DIR}/state:/state"
  -v "${SEED_MOUNT_DIR}:/seed:ro"
  -w /infra/tofu
)

if [[ -n "${GITEA_TOKEN:-}" ]]; then
  export TF_VAR_gitea_token="$GITEA_TOKEN"
  DOCKER_ARGS+=(--env TF_VAR_gitea_token)
fi

MSYS_NO_PATHCONV=1 docker "${DOCKER_ARGS[@]}" "$IMAGE" "$@"

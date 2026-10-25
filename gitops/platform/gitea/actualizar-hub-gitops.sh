#!/usr/bin/env bash
# Copia carpetas elegidas del monorepo a forja-digital/hub-gitops en un commit nuevo (spec 008, T20).
# sembrar-hub-gitops.sh solo siembra un repo vacío; cuando un manifiesto cambia en el monorepo (por
# ejemplo gitops/clients/_base u observability/), este script lo lleva al repo que Argo CD vigila.
#
# Uso:
#   GITEA_USER=forja-admin GITEA_PASSWORD='...' \
#     bash gitops/platform/gitea/actualizar-hub-gitops.sh gitops/clients/_base observability
#
# Cada ruta es relativa a la raíz del monorepo. En hub-gitops queda en la misma ruta sin el prefijo
# `gitops/` (así se sembró): gitops/clients/_base → clients/_base, observability → observability.
# La carpeta destino se reemplaza completa: lo que se borró en el monorepo también sale de hub-gitops.
# Si no hay diferencias no se hace commit. La contraseña va en el entorno, nunca en la URL del remoto.
set -euo pipefail

GITEA_URL="${GITEA_URL:-http://gitea.hub.local}"
ORG="${ORG:-forja-digital}"
REPO="${REPO:-hub-gitops}"
# REMOTO permite apuntar a otro repo (por ejemplo uno local para probar el script)
REMOTO="${REMOTO:-${GITEA_URL}/${ORG}/${REPO}.git}"

[ "$#" -gt 0 ] || { echo "Uso: $0 <ruta del monorepo> [<ruta> ...]" >&2; exit 2; }

RAIZ="$(cd "$(dirname "$0")/../../.." && pwd)"
GIT_AUTH=()
case "$REMOTO" in
  http://*|https://*)
    : "${GITEA_USER:?Falta GITEA_USER}"
    : "${GITEA_PASSWORD:?Falta GITEA_PASSWORD}"
    # La credencial va en un encabezado, no en la URL, para que no quede en la configuración del repo
    AUTH="$(printf '%s:%s' "$GITEA_USER" "$GITEA_PASSWORD" | base64 | tr -d '\n')"
    GIT_AUTH=(-c "http.extraHeader=Authorization: Basic ${AUTH}")
    ;;
esac

# Valida todas las rutas antes de tocar nada
for ruta in "$@"; do
  ruta="${ruta%/}"
  [ -d "${RAIZ}/${ruta}" ] || { echo "No existe la carpeta ${ruta} en el monorepo." >&2; exit 2; }
  case "$ruta" in
    /*|*..*) echo "La ruta ${ruta} debe ser relativa a la raíz del monorepo y sin '..'." >&2; exit 2 ;;
  esac
done

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
git "${GIT_AUTH[@]}" clone -q --depth 1 --branch main "$REMOTO" "$TMP/hub-gitops"

destinos=()
for ruta in "$@"; do
  ruta="${ruta%/}"
  destino="${ruta#gitops/}"
  rm -rf "${TMP}/hub-gitops/${destino}"
  mkdir -p "$(dirname "${TMP}/hub-gitops/${destino}")"
  cp -r "${RAIZ}/${ruta}" "${TMP}/hub-gitops/${destino}"
  destinos+=("$destino")
done

cd "$TMP/hub-gitops"
git add -A
if git diff --cached --quiet; then
  echo "hub-gitops ya tiene lo mismo que el monorepo en: ${destinos[*]}. No hay nada que subir."
  exit 0
fi
git diff --cached --stat
ORIGEN="$(git -C "$RAIZ" rev-parse --short HEAD 2>/dev/null || echo 'sin git')"
git -c user.name="Forja Digital" -c user.email="hub@forja.test" \
  commit -q -m "chore: actualizar ${destinos[*]} desde el monorepo (${ORIGEN})"
git "${GIT_AUTH[@]}" push -q origin main
echo "Listo: ${destinos[*]} actualizado en ${REMOTO%.git} ($(git rev-parse --short HEAD))."

#!/usr/bin/env bash
# Promueve a forja-digital/hub-gitops (el repo que vigila Argo CD) lo que escribe el equipo en el repositorio principal (spec 022). Un solo comando, un solo sentido, y con dueños:
#
#   del equipo (se promueve, la carpeta destino se reemplaza completa)
#       gitops/clients/_base  → clients/_base          los manifiestos base de todos los sitios
#       observability/        → observability/         Prometheus, Loki, Tempo, Grafana, Alloy…
#       gitops/hub/           → hub/                   el Hub (API, web, voz, base de datos)
#       gitops/platform/backstage → platform/backstage la plantilla y las docs que Backstage lee
#   por cliente que YA existe en hub-gitops: se copia todo MENOS kustomization.yaml y catalog-info.yaml
#       porque la versión (images.newTag) y el catálogo los escribe el Hub al aprobar un cambio, al hacer un rollback o al dar de alta el sitio: promover no los pisa nunca.
#       Un cliente que no existe en hub-gitops se omite: lo crea el Hub.
#   de nadie (se aplica una vez con kubectl): platform/argocd, platform/gitea, platform/k3s, platform/namespaces.yaml; con --limpiar se retiran las copias viejas de hub-gitops.
#
# Solo promueve lo revisado: sin cambios sin guardar en lo que sube y con el commit ya contenido en origin/dev u origin/main (lo que se despliega es lo que se mezcló por PR).
# Uso:  GITEA_USER=... GITEA_PASSWORD=... bash gitops/sincronizar-hub-gitops.sh [--simular | --comprobar] [--limpiar] [--forzar]
#   --simular     muestra qué cambiaría en hub-gitops y no sube nada
#   --comprobar   como --simular pero sin exigir árbol limpio, y sale con 1 si hay diferencias (gitops/pruebas/sincronia.sh lo usa); el usuario y la clave son opcionales (el repo es público)
#   --limpiar     además retira de hub-gitops las copias sin uso de platform/ (argocd, gitea, k3s, namespaces.yaml)
#   --forzar      se salta las precondiciones (árbol limpio y commit mezclado) y lo avisa
# Variables: GITEA_URL (http://gitea.hub.local), ORG (forja-digital), REPO (hub-gitops), REMOTO (otro repo, p. ej. uno local para probar), RAIZ (otra raíz del repositorio principal), RAMAS_MEZCLADAS (origin/dev origin/main).
# Códigos de salida: 0 bien (o sin diferencias) · 1 hay diferencias (--comprobar) · 2 uso · 3 precondición sin cumplir.
set -euo pipefail

GITEA_URL="${GITEA_URL:-http://gitea.hub.local}"
ORG="${ORG:-forja-digital}"
REPO="${REPO:-hub-gitops}"
REMOTO="${REMOTO:-${GITEA_URL}/${ORG}/${REPO}.git}"
RAIZ="${RAIZ:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
RAMAS_MEZCLADAS="${RAMAS_MEZCLADAS:-origin/dev origin/main}"

# origen (en el repositorio principal) : destino (en hub-gitops)
COMPLETOS=("gitops/clients/_base:clients/_base" "observability:observability" "gitops/hub:hub" "gitops/platform/backstage:platform/backstage")
# Lo que escribe el Hub dentro de cada carpeta de cliente
DEL_HUB=("kustomization.yaml" "catalog-info.yaml")
OBSOLETOS=("platform/argocd" "platform/gitea" "platform/k3s" "platform/namespaces.yaml")

SIMULAR=0 COMPROBAR=0 LIMPIAR=0 FORZAR=0
for arg in "$@"; do
  case "$arg" in
    --simular) SIMULAR=1 ;;
    --comprobar) COMPROBAR=1 ;;
    --limpiar) LIMPIAR=1 ;;
    --forzar) FORZAR=1 ;;
    -h|--help) sed -n 2,23p "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Opción desconocida: $arg (ver --help)" >&2; exit 2 ;;
  esac
done

falla() { echo "ERROR: $1" >&2; exit "${2:-3}"; }

# ---------- Precondiciones: solo se promueve lo revisado ----------
ORIGEN_COMMIT="$(git -C "$RAIZ" rev-parse --short HEAD 2>/dev/null || echo 'sin-git')"
ORIGEN_RAMA="$(git -C "$RAIZ" rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')"
if [ "$COMPROBAR" = 0 ]; then
  rutas_origen=(); for par in "${COMPLETOS[@]}"; do rutas_origen+=("${par%%:*}"); done; rutas_origen+=("gitops/clients")
  sucio="$(git -C "$RAIZ" status --porcelain -- "${rutas_origen[@]}" 2>/dev/null || true)"
  mezclado=0
  git -C "$RAIZ" fetch -q origin 2>/dev/null || true
  for rama in $RAMAS_MEZCLADAS; do
    if git -C "$RAIZ" rev-parse -q --verify "refs/remotes/${rama}" >/dev/null 2>&1 && git -C "$RAIZ" merge-base --is-ancestor HEAD "refs/remotes/${rama}" 2>/dev/null; then mezclado=1; fi
  done
  if [ "$FORZAR" = 1 ]; then
    [ -z "$sucio" ] && [ "$mezclado" = 1 ] || echo "AVISO: --forzar: se promueve sin cumplir las precondiciones (árbol sin guardar o commit ${ORIGEN_COMMIT} sin mezclar)." >&2
  else
    [ -z "$sucio" ] || falla $'hay cambios sin guardar en lo que se promueve:\n'"$sucio"$'\nGuárdalos (commit) o usa --forzar.'
    [ "$mezclado" = 1 ] || falla "el commit ${ORIGEN_COMMIT} (${ORIGEN_RAMA}) no está en ${RAMAS_MEZCLADAS// / ni en }: mézclalo por PR primero (lo que se despliega es lo revisado) o usa --forzar."
  fi
fi

# ---------- Clonar hub-gitops ----------
GIT_AUTH=()
case "$REMOTO" in
  http://*|https://*)
    if [ -n "${GITEA_USER:-}" ] && [ -n "${GITEA_PASSWORD:-}" ]; then
      # La credencial va en un encabezado, no en la URL, para que no quede en la configuración del repo
      GIT_AUTH=(-c "http.extraHeader=Authorization: Basic $(printf '%s:%s' "$GITEA_USER" "$GITEA_PASSWORD" | base64 | tr -d '\n')")
    elif [ "$COMPROBAR" = 0 ] && [ "$SIMULAR" = 0 ]; then
      falla "faltan GITEA_USER y GITEA_PASSWORD (hacen falta para subir)." 2
    fi ;;
esac
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
git "${GIT_AUTH[@]}" clone -q --depth 1 --branch main "$REMOTO" "$TMP/hub-gitops"
DEST="$TMP/hub-gitops"

# ---------- Aplicar el mapa de dueños sobre la copia ----------
for par in "${COMPLETOS[@]}"; do
  origen="${par%%:*}"; destino="${par#*:}"
  [ -d "${RAIZ}/${origen}" ] || falla "no existe ${origen} en el repositorio principal." 2
  rm -rf "${DEST:?}/${destino}"
  mkdir -p "$(dirname "${DEST}/${destino}")"
  cp -r "${RAIZ}/${origen}" "${DEST}/${destino}"
done
for dir in "${RAIZ}"/gitops/clients/*/; do
  nombre="$(basename "$dir")"
  [ "$nombre" = "_base" ] && continue
  if [ ! -d "${DEST}/clients/${nombre}" ]; then
    echo "(omitido) clients/${nombre}: no existe en hub-gitops; lo crea el Hub al dar de alta el sitio."
    continue
  fi
  while IFS= read -r archivo; do
    archivo="${archivo#./}"
    propio=0; for h in "${DEL_HUB[@]}"; do [ "$archivo" = "$h" ] && propio=1; done
    [ "$propio" = 1 ] && continue
    mkdir -p "${DEST}/clients/${nombre}/$(dirname "$archivo")"
    cp "${dir}${archivo}" "${DEST}/clients/${nombre}/${archivo}"
  done < <(cd "$dir" && find . -type f)
done
if [ "$LIMPIAR" = 1 ]; then
  for o in "${OBSOLETOS[@]}"; do rm -rf "${DEST:?}/${o}"; done
fi

# ---------- Qué cambió ----------
cd "$DEST"
git add -A
if git diff --cached --quiet; then
  echo "hub-gitops está en sincronía con el repositorio principal (${ORIGEN_COMMIT}). No hay nada que subir."
  exit 0
fi
git diff --cached --stat | tail -25
if [ "$COMPROBAR" = 1 ]; then
  echo "DIFERENCIAS: hub-gitops no está en sincronía con el repositorio principal (${ORIGEN_COMMIT}); se corrige con: bash gitops/sincronizar-hub-gitops.sh" >&2
  exit 1
fi
if [ "$SIMULAR" = 1 ]; then
  echo "Simulación: esto cambiaría en hub-gitops; no se subió nada."
  exit 0
fi
git -c user.name="Forja Digital" -c user.email="hub@forja.test" commit -q -m "chore: sincronizar desde el repositorio principal (${ORIGEN_COMMIT} · ${ORIGEN_RAMA})"
git "${GIT_AUTH[@]}" push -q origin main
echo "Listo: hub-gitops actualizado (${DEST##*/} $(git rev-parse --short HEAD)) desde ${ORIGEN_COMMIT} (${ORIGEN_RAMA})."

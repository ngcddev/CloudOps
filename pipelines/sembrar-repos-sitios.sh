#!/usr/bin/env bash
# Crea en Gitea el repositorio de cada sitio de cliente desde apps/<sitio> (spec 006, T06), con el workflow de la
# puerta de seguridad y sus scripts, y sube las etiquetas de las versiones que ya existen. Cada etiqueta que se
# sube dispara la puerta (así quedan revisadas y firmadas v1, v1.1 y v2 en T22). No repite lo que ya está hecho.
#
# Uso:
#   GITEA_ADMIN_USER=forja-admin GITEA_ADMIN_PASSWORD='<contraseña>' bash pipelines/sembrar-repos-sitios.sh [--sin-etiquetas] [sitio...]
#
#   --sin-etiquetas   crea los repositorios pero no sube las versiones (la puerta no corre)
#   sitio...          solo esos sitios (restaurante, ferreteria, consultorio); por defecto los tres
#
# Variables opcionales: GITEA_URL (http://gitea.hub.local), ORG (forja-digital).
# Las versiones de la semilla apuntan todas al mismo commit: la imagen se construye con APP_VERSION=<etiqueta>.
set -euo pipefail

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RAIZ="$(cd "$AQUI/.." && pwd)"
GITEA_URL="${GITEA_URL:-http://gitea.hub.local}"
ORG="${ORG:-forja-digital}"
: "${GITEA_ADMIN_USER:?Falta GITEA_ADMIN_USER}"
: "${GITEA_ADMIN_PASSWORD:?Falta GITEA_ADMIN_PASSWORD}"
[ -f "$AQUI/cosign.pub" ] || { echo "Falta pipelines/cosign.pub: corre antes pipelines/configurar-gitea.sh." >&2; exit 1; }

ETIQUETAS=1
SITIOS=()
for argumento in "$@"; do
  case "$argumento" in
    --sin-etiquetas) ETIQUETAS=0 ;;
    *) SITIOS+=("$argumento") ;;
  esac
done
[ ${#SITIOS[@]} -gt 0 ] || SITIOS=(restaurante ferreteria consultorio)

# Versiones que ya existen de cada sitio (la v1.1 es la nueva portada de El Tornillo, spec 005)
etiquetas_de() {
  case "$1" in
    ferreteria) echo "v1 v1.1 v2" ;;
    *) echo "v1 v2" ;;
  esac
}

API="${GITEA_URL%/}/api/v1"
curl_api() { curl -sS -m 30 -u "${GITEA_ADMIN_USER}:${GITEA_ADMIN_PASSWORD}" -H 'Content-Type: application/json' "$@"; }
autorizacion="Authorization: Basic $(printf '%s:%s' "$GITEA_ADMIN_USER" "$GITEA_ADMIN_PASSWORD" | base64 | tr -d '\n')"
# Las credenciales viajan en la cabecera, no en la dirección del repositorio
git_gitea() { git -c "http.extraheader=${autorizacion}" -c user.name="Forja Digital" -c user.email="hub@forjadigital.test" "$@"; }

for sitio in "${SITIOS[@]}"; do
  [ -d "$RAIZ/apps/$sitio" ] || { echo "No existe apps/${sitio}." >&2; exit 1; }
  echo "== ${sitio} =="
  repo="${GITEA_URL%/}/${ORG}/${sitio}.git"

  codigo="$(curl_api -o /dev/null -w '%{http_code}' "${API}/repos/${ORG}/${sitio}")"
  if [ "$codigo" = "404" ]; then
    curl_api -f -X POST "${API}/orgs/${ORG}/repos" \
      -d "{\"name\":\"${sitio}\",\"private\":false,\"default_branch\":\"main\",\"description\":\"Sitio de ${sitio} (CloudOps Client Hub)\"}" >/dev/null
    echo "   repositorio creado"
  elif [ "$codigo" != "200" ]; then
    echo "Gitea respondió ${codigo} al consultar ${ORG}/${sitio}." >&2
    exit 1
  fi

  if [ -n "$(git_gitea ls-remote "$repo" 'refs/heads/main' 2>/dev/null)" ]; then
    echo "   ya tiene contenido: no se vuelve a sembrar (las etiquetas nuevas se suben a mano o con git push)"
    continue
  fi

  trabajo="$(mktemp -d)"
  cp -r "$RAIZ/apps/$sitio/." "$trabajo/"
  mkdir -p "$trabajo/.gitea/workflows" "$trabajo/.gitea/puerta"
  cp "$AQUI/puerta.yaml" "$trabajo/.gitea/workflows/puerta.yaml"
  cp "$AQUI/puerta.sh" "$AQUI/reportar.sh" "$AQUI/lib.sh" "$AQUI/cosign.pub" "$trabajo/.gitea/puerta/"
  # Lo que genera la puerta no es del repositorio ni del contexto de construcción
  printf '.puerta/\n' >> "$trabajo/.gitignore"
  printf '.puerta\n.gitea\n' >> "$trabajo/.dockerignore"

  (
    cd "$trabajo"
    git init -q -b main .
    git add -A
    # Windows no guarda el bit de ejecución: se marca para que los scripts corran en cualquier runner
    git update-index --chmod=+x .gitea/puerta/puerta.sh .gitea/puerta/reportar.sh
    git_gitea commit -q -m "feat: sitio de ${sitio} y puerta de seguridad"
    git_gitea push -q "$repo" main
    echo "   contenido subido (main)"
    if [ "$ETIQUETAS" = "1" ]; then
      for etiqueta in $(etiquetas_de "$sitio"); do
        git_gitea tag "$etiqueta"
        git_gitea push -q "$repo" "$etiqueta"
        echo "   versión ${etiqueta} subida: la puerta corre sola"
      done
    fi
  )
  rm -rf "$trabajo"
done
echo "Listo."

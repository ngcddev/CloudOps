#!/usr/bin/env bash
# Vuelve a correr la puerta de seguridad de las versiones de los sitios (v1, v1.1 y v2) para que el Hub las vuelva a conocer como «ok». Hace falta después de reiniciar la demo del
# clúster (demo/reiniciar-cluster.sh recrea la base del Hub vacía y con ella se pierden las corridas de la puerta). sembrar-repos-sitios.sh no repite lo que ya está hecho, así que aquí
# se borra cada etiqueta del repositorio del sitio en Gitea y se vuelve a subir: eso dispara el workflow de la puerta, que reporta al Hub. Uso: bash entrega/evidencias/resembrar-puerta.sh
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"
set -a; . ./.env.cluster; set +a
AUTH="$(printf '%s:%s' "$GITEA_ADMIN_USER" "$GITEA_ADMIN_PASSWORD" | base64 | tr -d '\n')"
git_gitea() { git -c "http.extraheader=Authorization: Basic ${AUTH}" -c user.name="Forja Digital" -c user.email="hub@forjadigital.test" "$@"; }
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
for par in "ferreteria:v1 v1.1 v2" "restaurante:v1 v2" "consultorio:v1 v2"; do
  sitio="${par%%:*}"; etiquetas="${par#*:}"
  repo="http://gitea.hub.local/forja-digital/${sitio}.git"
  echo "== ${sitio} =="
  git_gitea clone -q "$repo" "$T/$sitio" 2>/dev/null || { echo "   no se pudo clonar ${sitio}"; continue; }
  for e in $etiquetas; do
    git_gitea -C "$T/$sitio" push -q origin ":refs/tags/$e" 2>/dev/null
    git_gitea -C "$T/$sitio" tag -f "$e" HEAD >/dev/null
    git_gitea -C "$T/$sitio" push -q origin "refs/tags/$e" && echo "   $e subida: la puerta corre sola" || echo "   no se pudo subir $e"
    sleep 2
  done
done
echo "Esperando a que el runner termine las corridas (hasta 15 min)..."
for _ in $(seq 1 90); do
  pendientes="$(curl -s -m 10 -u "${GITEA_ADMIN_USER}:${GITEA_ADMIN_PASSWORD}" "http://gitea.hub.local/api/v1/repos/forja-digital/ferreteria/actions/runs?limit=10" 2>/dev/null | grep -o '"status":"\(queued\|in_progress\|waiting\|running\)"' | wc -l)"
  [ "${pendientes:-0}" -eq 0 ] && { sleep 20; echo "sin corridas pendientes en ferreteria"; break; }
  sleep 10
done

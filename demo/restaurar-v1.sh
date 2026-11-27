#!/usr/bin/env bash
# Devuelve un cliente a su versión base v1 en hub-gitops (como lo haría un git revert del cambio) y espera a que su sitio lo reporte. Sirve para dejar el estado que piden las demos
# antes de repetirlas: ferreteria:v1 para demo-005, ciclo-gitops y publicacion-sana. Uso: bash demo/restaurar-v1.sh [cliente]   (por defecto ferreteria; credenciales de .env.cluster)
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"
CLIENTE="${1:-ferreteria}"
set -a; . ./.env.cluster; set +a
AUTH="$(printf '%s:%s' "$GITEA_ADMIN_USER" "$GITEA_ADMIN_PASSWORD" | base64 | tr -d '\n')"
git_gitea() { git -c "http.extraHeader=Authorization: Basic ${AUTH}" -c user.name="Restaurar v1" -c user.email="prueba@forja.test" "$@"; }
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
git_gitea clone -q "http://gitea.hub.local/forja-digital/hub-gitops.git" "$T/r" || { echo "No se pudo clonar hub-gitops"; exit 1; }
cd "$T/r"
ARCHIVO="clients/$CLIENTE/kustomization.yaml"
actual="$(sed -n 's/^ *newTag: *\([^ \r]*\).*/\1/p' "$ARCHIVO" | head -1)"
echo "versión en hub-gitops: ${actual:-?}"
if [ "$actual" != "v1" ]; then
  sed -i 's/^\( *newTag: \)[^ \r]*\(\r\?\)$/\1v1\2/' "$ARCHIVO"
  git add "$ARCHIVO"
  git_gitea commit -q -m "revert($CLIENTE): volver a v1 (estado base de la verificación)"
  git_gitea push -q origin HEAD:main || { echo "No se pudo empujar"; exit 1; }
  echo "empujado: $(git rev-parse --short HEAD)"
fi
for _ in $(seq 1 60); do
  v="$(curl -s -m 5 "http://$CLIENTE.hub.local/health" | sed -n 's/.*"version":"\([^"]*\)".*/\1/p')"
  [ "$v" = "v1" ] && { echo "el sitio de $CLIENTE reporta v1"; exit 0; }
  sleep 5
done
echo "el sitio de $CLIENTE no volvió a v1 (reporta '$v')"; exit 1

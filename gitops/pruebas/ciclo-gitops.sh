#!/usr/bin/env bash
# Prueba a mano el ciclo GitOps de la spec 005 (T06; CA-3 y CA-5), sin pasar por el Hub:
#   1. cambia images.newTag de El Tornillo a v1.1 en hub-gitops y empuja el commit;
#   2. espera a que Argo CD sincronice y el sitio reporte v1.1 en /health (máximo 3 minutos);
#   3. revierte ese commit (git revert) y espera a que el sitio vuelva a v1.
# Uso:  GITEA_USER=forja-admin GITEA_PASSWORD='...' bash gitops/pruebas/ciclo-gitops.sh
# Necesita la imagen ferreteria:v1.1 publicada (apps/publicar-imagenes.sh ferreteria:v1.1) y las
# entradas de hosts. Deja el repo como estaba: el commit del cambio y su revert quedan en la historia.
set -uo pipefail

GITEA_URL="${GITEA_URL:-http://gitea.hub.local}"
REPO_URL="${GITEA_URL}/${ORG:-forja-digital}/${REPO:-hub-gitops}.git"
SITIO="${SITIO:-http://ferreteria.hub.local}"
ARCHIVO="clients/ferreteria/kustomization.yaml"
LIMITE="${LIMITE:-180}"
: "${GITEA_USER:?Falta GITEA_USER}"
: "${GITEA_PASSWORD:?Falta GITEA_PASSWORD}"

fallos=0
ok()    { echo "   OK   $1"; }
falla() { echo "   FALLA $1"; fallos=$((fallos+1)); }
version_del_sitio() { curl -s -m 5 "${SITIO}/health" | sed -n 's/.*"version":"\([^"]*\)".*/\1/p'; }
# Espera hasta LIMITE segundos a que /health reporte la versión pedida; imprime los segundos que tardó
esperar_version() {
  local esperada="$1" t=0
  while [ "$t" -lt "$LIMITE" ]; do
    [ "$(version_del_sitio)" = "$esperada" ] && { echo "$t"; return 0; }
    sleep 5; t=$((t+5))
  done
  return 1
}

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
AUTH="$(printf '%s:%s' "$GITEA_USER" "$GITEA_PASSWORD" | base64 | tr -d '\n')"
git_gitea() { git -c "http.extraHeader=Authorization: Basic ${AUTH}" -c user.name="Prueba GitOps" -c user.email="prueba@forja.test" "$@"; }

echo "== 0. Punto de partida =="
[ "$(version_del_sitio)" = "v1" ] && ok "el sitio reporta v1" || { falla "el sitio no reporta v1 (reporta '$(version_del_sitio)')"; exit 1; }
git_gitea clone -q "$REPO_URL" "$TMP/repo" || { echo "No se pudo clonar $REPO_URL"; exit 1; }
cd "$TMP/repo"

echo "== 1. Cambiar newTag a v1.1 y empujar =="
sed -i 's/^\(    newTag: \)v1\(\r\?\)$/\1v1.1\2/' "$ARCHIVO"   # tolera fin de línea CRLF
git diff --quiet && { echo "No cambió nada: ¿newTag ya no es v1?"; exit 1; }
git add "$ARCHIVO"
git_gitea commit -q -m "chore(ferreteria): versión v1.1 (prueba manual del ciclo)"
git_gitea push -q origin HEAD:main && ok "commit empujado: $(git rev-parse --short HEAD)" || { falla "no se pudo empujar"; exit 1; }

echo "== 2. Argo CD sincroniza y el sitio muestra v1.1 (CA-3, máximo ${LIMITE} s) =="
if t="$(esperar_version v1.1)"; then ok "v1.1 en /health a los ${t} s"; else falla "el sitio no llegó a v1.1 en ${LIMITE} s"; fi
curl -s -m 5 "${SITIO}/" | grep -q "Versi" && ok "el sitio responde" || falla "el sitio no responde en /"

echo "== 3. Revertir el commit y volver a v1 (CA-5) =="
git_gitea revert --no-edit HEAD >/dev/null
git_gitea push -q origin HEAD:main && ok "revert empujado: $(git rev-parse --short HEAD)" || { falla "no se pudo empujar el revert"; exit 1; }
if t="$(esperar_version v1)"; then ok "v1 de vuelta en /health a los ${t} s"; else falla "el sitio no volvió a v1 en ${LIMITE} s"; fi

echo
[ "$fallos" -eq 0 ] && echo "CICLO OK" || echo "CICLO CON ${fallos} FALLA(S)"
exit "$fallos"

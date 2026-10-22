#!/usr/bin/env bash
# Demo de cierre de la spec 005 (T23): recorre la demo y comprueba los criterios CA-1 a CA-6.
#   1. El Tornillo pide publicar la nueva portada (v1 -> v1.1).
#   2. El técnico aprueba en el Hub.
#   3. Se ve el commit en Gitea, Argo CD sincroniza y el sitio muestra v1.1.
#   4. La consola muestra v1.1, "Sincronizado" y el nombre del técnico.
# Uso:  bash gitops/pruebas/demo-005.sh      (clúster con todo aplicado, imagen ferreteria:v1.1
#       publicada, hub-gitops sembrado y las entradas de hosts; el sitio de El Tornillo debe estar en v1)
# Para volver a empezar: `git revert` del commit del cambio en hub-gitops (ver gitops/pruebas/ciclo-gitops.sh)
# y base nueva del Hub (docker compose down -v / reiniciar el Pod de la API con la base vacía).
set -uo pipefail

HUB="${HUB:-http://hub.local}"
GITEA="${GITEA:-http://gitea.hub.local}"
SITIO="${SITIO:-http://ferreteria.hub.local}"
BACKSTAGE="${BACKSTAGE:-http://backstage.hub.local}"
TECNICO_ID="${TECNICO_ID:-1}"        # Sofía Ramírez, la técnica de la semilla
VERSION_DESTINO="${VERSION_DESTINO:-v1.1}"
LIMITE="${LIMITE:-180}"

fallos=0
ok()    { echo "   OK   $1"; }
falla() { echo "   FALLA $1"; fallos=$((fallos+1)); }
# Primer valor de un campo JSON simple (cadena o número)
campo() { sed -n "s/.*\"$1\": *\"\{0,1\}\([^\",}]*\)\"\{0,1\}.*/\1/p" | head -1; }
post()  { curl -s -m 20 -H 'Content-Type: application/json' -X POST "$1" -d "$2"; }

echo "== 0. Punto de partida =="
estado="$(curl -s -m 10 "${HUB}/api/services/status")"
SERVICIO="$(echo "$estado" | tr '{' '\n' | grep '"cliente-ferreteria"' | campo service_id)"
[ -n "$SERVICIO" ] && ok "servicio de El Tornillo: #${SERVICIO}" || { falla "no se encontró el servicio de El Tornillo en ${HUB}"; exit 1; }
inicial="$(curl -s -m 5 "${SITIO}/health" | campo version)"
[ "$inicial" = "v1" ] && ok "el sitio reporta v1" || falla "el sitio reporta '${inicial}', se esperaba v1"

echo "== 1. El Tornillo pide publicar la nueva portada =="
ticket="$(post "${HUB}/api/tickets" "{\"service_id\":${SERVICIO},\"title\":\"Publicar la nueva portada\",\"description\":\"Queremos la portada de temporada de ${VERSION_DESTINO}.\",\"kind\":\"cambio\"}")"
TICKET_ID="$(echo "$ticket" | campo id)"
[ -n "$TICKET_ID" ] && ok "solicitud #${TICKET_ID} de tipo cambio" || { falla "no se creó la solicitud: ${ticket}"; exit 1; }
cambio="$(post "${HUB}/api/change-requests" "{\"ticket_id\":${TICKET_ID},\"to_version\":\"${VERSION_DESTINO}\",\"requested_by_id\":${TECNICO_ID}}")"
CAMBIO_ID="$(echo "$cambio" | campo id)"
[ "$(echo "$cambio" | campo status)" = "pendiente" ] && ok "cambio #${CAMBIO_ID} en pendiente" || { falla "el cambio no quedó pendiente: ${cambio}"; exit 1; }

echo "== 2. El técnico aprueba (CA-1, CA-2) =="
inicio=$(date +%s)
aprobado="$(post "${HUB}/api/change-requests/${CAMBIO_ID}/approve" "{\"actor_id\":${TECNICO_ID}}")"
SHA="$(echo "$aprobado" | campo gitops_commit_sha)"
[ "$(echo "$aprobado" | campo status)" = "en_validacion" ] && ok "aprobado: en_validacion, commit ${SHA:0:7}" || { falla "no quedó en validación: ${aprobado}"; exit 1; }

echo "== 3. El commit en Gitea cambia solo el tag (CA-2) =="
commit="$(curl -s -m 10 "${GITEA}/api/v1/repos/forja-digital/hub-gitops/git/commits/${SHA}")"
echo "$commit" | grep -q "chore(ferreteria): versi.*${VERSION_DESTINO} (cambio #${CAMBIO_ID})" \
  && ok "mensaje: chore(ferreteria): versión ${VERSION_DESTINO} (cambio #${CAMBIO_ID})" || falla "el mensaje del commit no es el esperado"
archivos="$(echo "$commit" | grep -o '"filename": *"[^"]*"' | sed 's/": *"/":"/' | sort -u)"
[ "$archivos" = '"filename":"clients/ferreteria/kustomization.yaml"' ] \
  && ok "solo cambió clients/ferreteria/kustomization.yaml" || falla "el commit cambió otros archivos: ${archivos}"

echo "== 4. Argo CD sincroniza y el sitio muestra ${VERSION_DESTINO} (CA-3, máximo ${LIMITE} s) =="
version=""
while [ $(( $(date +%s) - inicio )) -lt "$LIMITE" ]; do
  version="$(curl -s -m 5 "${SITIO}/health" | campo version)"
  [ "$version" = "$VERSION_DESTINO" ] && break
  sleep 5
done
segundos=$(( $(date +%s) - inicio ))
[ "$version" = "$VERSION_DESTINO" ] && ok "/health reporta ${VERSION_DESTINO} a los ${segundos} s" || falla "/health reporta '${version}' tras ${LIMITE} s"
curl -s -m 5 "${SITIO}/" | grep -q 'id="version"' && ok "el sitio responde con su pie de versión" || falla "el sitio no responde en /"

echo "== 5. La solicitud pasa a desplegada, con hora y usuario en cada paso (CA-1) =="
final=""
for _ in $(seq 1 12); do
  final="$(curl -s -m 5 "${HUB}/api/change-requests?service_id=${SERVICIO}" | tr '{' '\n' | grep "\"id\":${CAMBIO_ID}," | campo status)"
  [ "$final" = "desplegada" ] && break
  sleep 5
done
[ "$final" = "desplegada" ] && ok "cambio #${CAMBIO_ID}: desplegada" || falla "el cambio sigue en '${final}'"
eventos="$(curl -s -m 5 "${HUB}/api/tickets/${TICKET_ID}" | grep -o '"type":"cambio"' | wc -l | tr -d ' ')"
[ "$eventos" -ge 4 ] && ok "historial con ${eventos} pasos del cambio" || falla "el historial tiene ${eventos} pasos (se esperaban 4: pendiente, aprobada, en_validacion, desplegada)"

echo "== 6. La consola muestra la versión, el estado y el técnico (CA-4) =="
fila="$(curl -s -m 10 "${HUB}/api/services/status" | tr '{' '\n' | grep '"cliente-ferreteria"')"
[ "$(echo "$fila" | campo current_version)" = "$VERSION_DESTINO" ] && ok "versión activa ${VERSION_DESTINO}" || falla "versión activa: $(echo "$fila" | campo current_version)"
[ "$(echo "$fila" | campo sync_status)" = "Synced" ] && ok "sincronización: Synced" || falla "sincronización: $(echo "$fila" | campo sync_status)"
[ "$(echo "$fila" | campo health_status)" = "Healthy" ] && ok "salud: Healthy" || falla "salud: $(echo "$fila" | campo health_status)"
autor="$(echo "$fila" | campo last_author)"
[ -n "$autor" ] && ok "último cambio por ${autor}" || falla "no hay último autor"

echo "== 7. Catálogo con los 3 clientes (CA-6, opcional si Backstage está apagado) =="
# Solo cuenta como "responde" un 200: si Backstage no está, Traefik contesta 404 y curl igual sale con éxito
if [ "$(curl -s -m 10 -o /dev/null -w '%{http_code}' "${BACKSTAGE}/api/catalog/entities?filter=kind=component")" = "200" ]; then
  n="$(curl -s -m 10 "${BACKSTAGE}/api/catalog/entities?filter=kind=component" | grep -o '"kind":"Component"' | wc -l | tr -d ' ')"
  [ "$n" -ge 3 ] && ok "el catálogo lista ${n} componentes" || falla "el catálogo lista ${n} componentes (se esperaban 3)"
else
  echo "   --   Backstage no responde (apagado): /agencia/servicios cumple el rol"
fi

echo
echo "Falta comprobar a mano (CA-5): revertir el commit en Gitea y ver que el sitio vuelve a v1"
echo "(bash gitops/pruebas/ciclo-gitops.sh lo hace con medición de tiempos)."
[ "$fallos" -eq 0 ] && echo "DEMO OK" || echo "DEMO CON ${fallos} FALLA(S)"
exit "$fallos"

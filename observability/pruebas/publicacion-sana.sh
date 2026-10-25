#!/usr/bin/env bash
# Publicación sana (spec 008, T31 · CA-9): publica por el Hub una versión que funciona y vigila 2 minutos.
# Con strategy Recreate el sitio no responde unos segundos mientras arranca la versión nueva; la alerta
# espera 30 s, así que ese reinicio NO debe abrir un incidente ni dejar el servicio «caido».
# Uso:
#   HUB_PASSWORD='...' bash observability/pruebas/publicacion-sana.sh
#   (por defecto El Tornillo a v1.1; VERSION y NS cambian el sitio y la versión)
# Requisitos: la 008 publicada en el clúster, la versión con su puerta de seguridad en «ok» y el sitio en
# otra versión (si ya está en v1.1, volverlo a v1 con git revert en hub-gitops, ver gitops/pruebas/ciclo-gitops.sh).
set -uo pipefail

HUB="${HUB:-http://hub.local}"
NS="${NS:-cliente-ferreteria}"
SITIO="${SITIO:-http://ferreteria.hub.local}"
VERSION="${VERSION:-v1.1}"
VIGILAR="${VIGILAR:-120}"
HUB_USUARIO="${HUB_USUARIO:-sofia@forjadigital.test}"
: "${HUB_PASSWORD:?Falta HUB_PASSWORD (kubectl -n hub get secret hub-auth -o jsonpath='{.data.SEED_USER_PASSWORD}' | base64 -d)}"

fallos=0
ok()    { echo "   OK   $1"; }
falla() { echo "   FALLA $1"; fallos=$((fallos+1)); }
# Primer valor de un campo JSON simple (la primera aparición)
campo() { grep -o "\"$1\": *\"\{0,1\}[^\",}]*" | head -1 | sed "s/^\"$1\": *\"\{0,1\}//"; }
TOKEN="$(curl -s -m 10 -H 'Content-Type: application/json' -X POST "${HUB}/api/auth/login" \
  -d "{\"email\":\"${HUB_USUARIO}\",\"password\":\"${HUB_PASSWORD}\"}" | campo access_token)"
[ -n "$TOKEN" ] || { echo "No se pudo entrar al Hub como ${HUB_USUARIO} (¿HUB_PASSWORD correcta?)"; exit 1; }
hub_get() { curl -s -m 10 -H "Authorization: Bearer ${TOKEN}" "$1"; }
post()    { curl -s -m 20 -H "Authorization: Bearer ${TOKEN}" -H 'Content-Type: application/json' -X POST "$1" -d "$2"; }
fila()    { hub_get "${HUB}/api/services/status" | tr '{' '\n' | grep "\"${NS}\""; }

SERVICIO="$(fila | campo service_id)"
CLIENTE="$(fila | campo client_id)"
[ -n "$SERVICIO" ] || { echo "No se encontró el servicio ${NS} en ${HUB}"; exit 1; }
# Cuántos incidentes tiene el cliente (cualquier estado): no debe crecer
contar() { hub_get "${HUB}/api/incidents?client_id=${CLIENTE}" | grep -o '"id":' | wc -l | tr -d ' '; }
antes="$(contar)"

echo "== Publicar ${VERSION} en ${NS} por el Hub =="
ticket="$(post "${HUB}/api/tickets" "{\"service_id\":${SERVICIO},\"title\":\"Publicación sana ${VERSION}\",\"description\":\"Prueba CA-9 (spec 008, T31).\",\"kind\":\"cambio\"}")"
cambio="$(post "${HUB}/api/change-requests" "{\"ticket_id\":$(echo "$ticket" | campo id),\"to_version\":\"${VERSION}\"}")"
CAMBIO_ID="$(echo "$cambio" | campo id)"
aprobado="$(post "${HUB}/api/change-requests/${CAMBIO_ID:-0}/approve" "{}")"
[ "$(echo "$aprobado" | campo status)" = "en_validacion" ] && ok "cambio #${CAMBIO_ID} aprobado" || { falla "no se aprobó: ${aprobado}${cambio}"; exit 1; }

echo "== Vigilar ${VIGILAR} s: el sitio puede reiniciarse, pero no debe abrirse ningún incidente =="
inicio=$(date +%s); sin_respuesta=0; caido=no
while [ $(( $(date +%s) - inicio )) -lt "$VIGILAR" ]; do
  [ "$(curl -s -o /dev/null -m 3 -w '%{http_code}' "${SITIO}/health")" = "200" ] || sin_respuesta=$((sin_respuesta + 1))
  [ "$(fila | campo service_status)" = "caido" ] && caido=si
  sleep 1
done
echo "   (el sitio no respondió en ${sin_respuesta} sondeos de 1 s durante el reinicio)"
despues="$(contar)"
[ "$despues" = "$antes" ] && ok "ningún incidente nuevo (CA-9)" || falla "se abrieron $((despues - antes)) incidente(s)"
[ "$caido" = "no" ] && ok "el servicio nunca apareció «caido»" || falla "el servicio apareció «caido»"
[ "$(curl -s -m 5 "${SITIO}/health" | campo version)" = "$VERSION" ] && ok "el sitio responde ${VERSION}" || falla "el sitio no reporta ${VERSION}"

echo
if [ "$fallos" -eq 0 ]; then echo "La publicación sana no abrió incidentes (CA-9)."; else echo "${fallos} comprobación(es) fallaron."; exit 1; fi

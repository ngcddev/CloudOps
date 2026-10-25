#!/usr/bin/env bash
# Cronómetro del caso del restaurante (spec 008, T30 · CA-2, CA-5, CA-6). En cada corrida:
#   1. aprueba en el Hub el cambio de La Sazón a la v2 rota (por la API, como lo haría el técnico);
#   2. mide desde que el sitio deja de responder hasta que el Hub abre el incidente P1 (debe ser ≤ 60 s)
#      y comprueba que el servicio queda «caido»;
#   3. vuelve a v1 con `git revert` del commit del cambio en hub-gitops y espera a que el incidente pase
#      solo a «mitigado» y el servicio a «operativo».
# Uso:
#   HUB_PASSWORD='...' GITEA_USER=forja-admin GITEA_PASSWORD='...' bash observability/pruebas/cronometro.sh
# Requisitos: la 008 publicada en el clúster (Hub con ALERTMANAGER_TOKEN, pila de observability/ en
# Synced/Healthy), restaurante:v2 con su puerta de seguridad en «ok», La Sazón en v1 y las entradas de hosts.
# Entre corridas espera a que el cambio a v2 deje de estar en curso: hasta la spec 009 el Hub lo marca
# «fallida» cuando vence VALIDATION_TIMEOUT_MINUTES (10 min por defecto).
# Los incidentes quedan mitigados; se cierran desde la consola con su causa raíz.
set -uo pipefail

HUB="${HUB:-http://hub.local}"
GITEA="${GITEA:-http://gitea.hub.local}"
SITIO="${SITIO:-http://restaurante.hub.local}"
NS="cliente-restaurante"
HUB_USUARIO="${HUB_USUARIO:-sofia@forjadigital.test}"
: "${HUB_PASSWORD:?Falta HUB_PASSWORD (kubectl -n hub get secret hub-auth -o jsonpath='{.data.SEED_USER_PASSWORD}' | base64 -d)}"
: "${GITEA_USER:?Falta GITEA_USER}"
: "${GITEA_PASSWORD:?Falta GITEA_PASSWORD}"
VERSION_ROTA="${VERSION_ROTA:-v2}"
CORRIDAS="${CORRIDAS:-3}"
LIMITE="${LIMITE:-60}"                         # segundos máximos de la caída al incidente (CA-2)
LIMITE_RECUPERACION="${LIMITE_RECUPERACION:-240}"
ESPERA_CAMBIO="${ESPERA_CAMBIO:-900}"          # cuánto esperar a que no haya un cambio en curso

fallos=0
ok()    { echo "   OK   $1"; }
falla() { echo "   FALLA $1"; fallos=$((fallos+1)); }
# Primer valor de un campo JSON simple (la primera aparición: el detalle del incidente repite claves
# como «source» dentro del último cambio)
campo() { grep -o "\"$1\": *\"\{0,1\}[^\",}]*" | head -1 | sed "s/^\"$1\": *\"\{0,1\}//"; }
TOKEN="$(curl -s -m 10 -H 'Content-Type: application/json' -X POST "${HUB}/api/auth/login" \
  -d "{\"email\":\"${HUB_USUARIO}\",\"password\":\"${HUB_PASSWORD}\"}" | campo access_token)"
[ -n "$TOKEN" ] || { echo "No se pudo entrar al Hub como ${HUB_USUARIO} (¿HUB_PASSWORD correcta?)"; exit 1; }
hub_get() { curl -s -m 10 -H "Authorization: Bearer ${TOKEN}" "$1"; }
post()    { curl -s -m 20 -H "Authorization: Bearer ${TOKEN}" -H 'Content-Type: application/json' -X POST "$1" -d "$2"; }
# Fila de La Sazón en el estado de los servicios
fila()    { hub_get "${HUB}/api/services/status" | tr '{' '\n' | grep "\"${NS}\""; }
AUTH="$(printf '%s:%s' "$GITEA_USER" "$GITEA_PASSWORD" | base64 | tr -d '\n')"
git_gitea() { git -c "http.extraHeader=Authorization: Basic ${AUTH}" -c user.name="Cronómetro 008" -c user.email="prueba@forja.test" "$@"; }

SERVICIO="$(fila | campo service_id)"
CLIENTE="$(fila | campo client_id)"
[ -n "$SERVICIO" ] || { echo "No se encontró el servicio de La Sazón en ${HUB}"; exit 1; }
# Incidente abierto de La Sazón (id), vacío si no hay
incidente_abierto() { hub_get "${HUB}/api/incidents?status=abierto&client_id=${CLIENTE}" | campo id; }

for corrida in $(seq 1 "$CORRIDAS"); do
  echo "== Corrida ${corrida} de ${CORRIDAS} =="
  [ -z "$(incidente_abierto)" ] || { falla "La Sazón ya tiene un incidente abierto: ciérrelo o mitíguelo antes"; break; }

  espera=0
  while [ "$(fila | campo open_change_id)" != "null" ] && [ -n "$(fila | campo open_change_id)" ]; do
    [ "$espera" -ge "$ESPERA_CAMBIO" ] && break
    [ "$espera" -eq 0 ] && echo "   ...La Sazón tiene un cambio en curso; esperando a que termine (máx. ${ESPERA_CAMBIO} s)"
    sleep 15; espera=$((espera + 15))
  done

  ticket="$(post "${HUB}/api/tickets" "{\"service_id\":${SERVICIO},\"title\":\"Cronómetro 008: publicar ${VERSION_ROTA}\",\"description\":\"Prueba de detección (spec 008, T30).\",\"kind\":\"cambio\"}")"
  TICKET_ID="$(echo "$ticket" | campo id)"
  cambio="$(post "${HUB}/api/change-requests" "{\"ticket_id\":${TICKET_ID:-0},\"to_version\":\"${VERSION_ROTA}\"}")"
  CAMBIO_ID="$(echo "$cambio" | campo id)"
  [ -n "$CAMBIO_ID" ] || { falla "no se pudo registrar el cambio: ${cambio}"; break; }
  aprobado="$(post "${HUB}/api/change-requests/${CAMBIO_ID}/approve" "{}")"
  SHA="$(echo "$aprobado" | campo gitops_commit_sha)"
  [ -n "$SHA" ] && ok "cambio #${CAMBIO_ID} a ${VERSION_ROTA} aprobado (commit ${SHA:0:7})" || { falla "no se aprobó: ${aprobado}"; break; }

  # Una sola vuelta por segundo: primero se ve caer el sitio, luego aparece el incidente
  inicio=$(date +%s); caida=""; INCIDENTE=""
  while [ $(( $(date +%s) - inicio )) -lt $((LIMITE + 240)) ]; do
    if [ -z "$caida" ]; then
      codigo="$(curl -s -o /dev/null -m 3 -w '%{http_code}' "${SITIO}/health")"
      [ "$codigo" = "200" ] || caida=$(date +%s)
    fi
    INCIDENTE="$(incidente_abierto)"
    [ -n "$INCIDENTE" ] && break
    sleep 1
  done
  ahora=$(date +%s)
  if [ -z "$INCIDENTE" ]; then
    falla "no apareció el incidente (el sitio ${caida:+cayó}${caida:-nunca dejó de responder})"
  else
    desde_caida=$(( ahora - ${caida:-$ahora} ))
    detalle="$(hub_get "${HUB}/api/incidents/${INCIDENTE}")"
    [ "$(echo "$detalle" | campo priority)" = "P1" ] && [ "$(echo "$detalle" | campo source)" = "alerta" ] \
      && ok "incidente P1 #${INCIDENTE} abierto por el monitoreo" || falla "el incidente no es P1 de alerta"
    [ "$desde_caida" -le "$LIMITE" ] \
      && ok "de la caída al incidente: ${desde_caida} s (≤ ${LIMITE} s) · desde la aprobación: $(( ahora - inicio )) s" \
      || falla "de la caída al incidente: ${desde_caida} s (más de ${LIMITE} s)"
    [ "$(fila | campo service_status)" = "caido" ] && ok "el servicio aparece «caido»" || falla "el servicio no aparece «caido»"
  fi

  TMP="$(mktemp -d)"
  if git_gitea clone -q "${GITEA}/forja-digital/hub-gitops.git" "$TMP/repo" \
    && git_gitea -C "$TMP/repo" revert --no-edit "$SHA" >/dev/null \
    && git_gitea -C "$TMP/repo" push -q origin HEAD:main; then
    ok "git revert del cambio empujado: $(git -C "$TMP/repo" rev-parse --short HEAD)"
  else
    falla "no se pudo revertir ${SHA:0:7} en hub-gitops"
  fi
  rm -rf "$TMP"

  if [ -n "$INCIDENTE" ]; then
    inicio=$(date +%s); estado=""
    while [ $(( $(date +%s) - inicio )) -lt "$LIMITE_RECUPERACION" ]; do
      estado="$(hub_get "${HUB}/api/incidents/${INCIDENTE}" | campo status)"
      [ "$estado" = "mitigado" ] && break
      sleep 2
    done
    [ "$estado" = "mitigado" ] && ok "el incidente pasó solo a «mitigado» en $(( $(date +%s) - inicio )) s" \
      || falla "el incidente sigue «${estado}» tras ${LIMITE_RECUPERACION} s"
    [ "$(fila | campo service_status)" = "operativo" ] && ok "el servicio volvió a «operativo»" || falla "el servicio no volvió a «operativo»"
  fi
done

echo
if [ "$fallos" -eq 0 ]; then echo "Las ${CORRIDAS} corridas cumplen (CA-2, CA-5, CA-6)."; else echo "${fallos} comprobación(es) fallaron."; exit 1; fi

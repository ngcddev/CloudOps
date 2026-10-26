#!/usr/bin/env bash
# Caso completo del restaurante, sin IA (spec 009, T14 · CA-2 a CA-5 y CA-7). En cada corrida:
#   1. aprueba en el Hub el cambio de La Sazón a la v2 rota (por la API, como lo haría el técnico);
#   2. espera el incidente P1 que abre el monitoreo y comprueba que el plan dice «v2 → v1»;
#   3. pide el rollback por la API (el Hub escribe el commit `revert` en hub-gitops; nadie toca el clúster);
#   4. mide hasta que el incidente queda «mitigado» y muestra su MTTR medido de verdad;
#   5. comprueba que el sitio responde 200, que el servicio vuelve a «operativo», que el rollback quedó en
#      la línea de tiempo, el historial de versiones y la bitácora, y que un segundo rollback se rechaza;
#   6. pide el mensaje para el cliente (nunca se envía solo) y lo imprime.
# Uso:
#   HUB_PASSWORD='...' bash gitops/pruebas/demo-caso-restaurante.sh
#   La contraseña es la de los usuarios sembrados (Secret hub-auth en k3s):
#   kubectl -n hub get secret hub-auth -o jsonpath='{.data.SEED_USER_PASSWORD}' | base64 -d
# Requisitos: la 009 publicada en el clúster (Hub con la migración 0009), la pila de monitoreo de la 008 en
# Synced/Healthy, restaurante:v2 con su puerta de seguridad en «ok», La Sazón en v1 y las entradas de hosts.
# Entre corridas espera a que el cambio a v2 deje de estar en curso. Los incidentes quedan mitigados; se
# cierran desde la consola con su causa raíz.
set -uo pipefail

HUB="${HUB:-http://hub.local}"
SITIO="${SITIO:-http://restaurante.hub.local}"
NS="cliente-restaurante"
HUB_USUARIO="${HUB_USUARIO:-sofia@forjadigital.test}"
: "${HUB_PASSWORD:?Falta HUB_PASSWORD (kubectl -n hub get secret hub-auth -o jsonpath='{.data.SEED_USER_PASSWORD}' | base64 -d)}"
VERSION_ROTA="${VERSION_ROTA:-v2}"
VERSION_ESTABLE="${VERSION_ESTABLE:-v1}"
CORRIDAS="${CORRIDAS:-3}"
LIMITE_INCIDENTE="${LIMITE_INCIDENTE:-300}"      # segundos máximos de la aprobación al incidente
LIMITE_RECUPERACION="${LIMITE_RECUPERACION:-240}" # segundos máximos del rollback a «mitigado»
ESPERA_CAMBIO="${ESPERA_CAMBIO:-900}"            # cuánto esperar a que no haya un cambio en curso

fallos=0
ok()    { echo "   OK   $1"; }
falla() { echo "   FALLA $1"; fallos=$((fallos+1)); }
# Primer valor de un campo JSON simple (la primera aparición)
campo() { grep -o "\"$1\": *\"\{0,1\}[^\",}]*" | head -1 | sed "s/^\"$1\": *\"\{0,1\}//"; }
# Solo el bloque «rollback» del detalle del incidente: ahí «status» no es el del incidente
bloque_rollback() { sed -n 's/.*"rollback": *{\([^}]*\)}.*/\1/p'; }
TOKEN="$(curl -s -m 10 -H 'Content-Type: application/json' -X POST "${HUB}/api/auth/login" \
  -d "{\"email\":\"${HUB_USUARIO}\",\"password\":\"${HUB_PASSWORD}\"}" | campo access_token)"
[ -n "$TOKEN" ] || { echo "No se pudo entrar al Hub como ${HUB_USUARIO} (¿HUB_PASSWORD correcta?)"; exit 1; }
hub_get() { curl -s -m 10 -H "Authorization: Bearer ${TOKEN}" "$1"; }
post()    { curl -s -m 30 -H "Authorization: Bearer ${TOKEN}" -H 'Content-Type: application/json' -X POST "$1" -d "${2:-}"; }
codigo_post() { curl -s -m 30 -o /dev/null -w '%{http_code}' -H "Authorization: Bearer ${TOKEN}" -X POST "$1"; }
fila()    { hub_get "${HUB}/api/services/status" | tr '{' '\n' | grep "\"${NS}\""; }

SERVICIO="$(fila | campo service_id)"
CLIENTE="$(fila | campo client_id)"
[ -n "$SERVICIO" ] || { echo "No se encontró el servicio de La Sazón en ${HUB}"; exit 1; }
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

  # 1. La v2 rota entra por la puerta de siempre: ticket, solicitud de cambio y aprobación
  ticket="$(post "${HUB}/api/tickets" "{\"service_id\":${SERVICIO},\"title\":\"Caso restaurante 009: publicar ${VERSION_ROTA}\",\"description\":\"Demo del rollback (spec 009, T14).\",\"kind\":\"cambio\"}")"
  CAMBIO="$(post "${HUB}/api/change-requests" "{\"ticket_id\":$(echo "$ticket" | campo id),\"to_version\":\"${VERSION_ROTA}\"}" | campo id)"
  [ -n "$CAMBIO" ] || { falla "no se pudo registrar el cambio a ${VERSION_ROTA}"; break; }
  aprobado="$(post "${HUB}/api/change-requests/${CAMBIO}/approve" "{}")"
  SHA_CAMBIO="$(echo "$aprobado" | campo gitops_commit_sha)"
  [ -n "$SHA_CAMBIO" ] && ok "cambio #${CAMBIO} a ${VERSION_ROTA} aprobado (commit ${SHA_CAMBIO:0:7})" || { falla "no se aprobó: ${aprobado}"; break; }

  # 2. El monitoreo ve el sitio caído y abre el incidente P1
  inicio=$(date +%s); INCIDENTE=""
  while [ $(( $(date +%s) - inicio )) -lt "$LIMITE_INCIDENTE" ]; do
    INCIDENTE="$(incidente_abierto)"; [ -n "$INCIDENTE" ] && break; sleep 2
  done
  [ -n "$INCIDENTE" ] && ok "incidente P1 #${INCIDENTE} abierto por el monitoreo" || { falla "no apareció el incidente"; break; }

  plan="$(hub_get "${HUB}/api/incidents/${INCIDENTE}/rollback-plan")"
  [ "$(echo "$plan" | campo current_version)" = "$VERSION_ROTA" ] && [ "$(echo "$plan" | campo target_version)" = "$VERSION_ESTABLE" ] \
    && [ "$(echo "$plan" | campo can_rollback)" = "true" ] \
    && ok "el plan dice ${VERSION_ROTA} → ${VERSION_ESTABLE} y el botón está activo" || falla "el plan no es ${VERSION_ROTA} → ${VERSION_ESTABLE}: ${plan}"

  # 3. Rollback: el Hub escribe el commit; Argo CD hace el resto
  inicio_rollback=$(date +%s)
  respuesta="$(post "${HUB}/api/incidents/${INCIDENTE}/rollback")"
  SHA_ROLLBACK="$(echo "$respuesta" | bloque_rollback | campo commit_sha)"
  [ -n "$SHA_ROLLBACK" ] && ok "rollback pedido: commit ${SHA_ROLLBACK:0:7} en hub-gitops" || { falla "no se pudo pedir el rollback: ${respuesta}"; break; }
  [ "$(codigo_post "${HUB}/api/incidents/${INCIDENTE}/rollback")" = "409" ] \
    && ok "un segundo rollback se rechaza (409)" || falla "el segundo rollback no dio 409"

  # 4. MTTR medido de verdad: de la caída a la primera vez que la sonda ve el sitio sano
  estado=""
  while [ $(( $(date +%s) - inicio_rollback )) -lt "$LIMITE_RECUPERACION" ]; do
    detalle="$(hub_get "${HUB}/api/incidents/${INCIDENTE}")"
    estado="$(echo "$detalle" | campo status)"
    [ "$estado" = "mitigado" ] && break
    sleep 2
  done
  if [ "$estado" = "mitigado" ]; then
    ok "incidente «mitigado» a los $(( $(date +%s) - inicio_rollback )) s del rollback · MTTR: $(echo "$detalle" | campo mttr_minutes) min"
  else
    falla "el incidente sigue «${estado}» tras ${LIMITE_RECUPERACION} s"
  fi
  [ "$(curl -s -o /dev/null -m 5 -w '%{http_code}' "${SITIO}/health")" = "200" ] && ok "el sitio responde 200" || falla "el sitio no responde 200"
  [ "$(fila | campo service_status)" = "operativo" ] && ok "el servicio volvió a «operativo»" || falla "el servicio no volvió a «operativo»"

  # Argo CD confirma un poco después de la sonda: el avance llega a «recuperado» y deja su rastro
  for _ in $(seq 1 30); do
    detalle="$(hub_get "${HUB}/api/incidents/${INCIDENTE}")"
    [ "$(echo "$detalle" | bloque_rollback | campo status)" = "recuperado" ] && break; sleep 2
  done
  [ "$(echo "$detalle" | bloque_rollback | campo status)" = "recuperado" ] \
    && ok "el avance llegó a «recuperado»" || falla "el rollback no llegó a «recuperado»"

  # 5. El rastro: línea de tiempo, historial de versiones y bitácora (CA-5)
  echo "$detalle" | grep -q '"type": *"rollback_enviado"' && echo "$detalle" | grep -q '"type": *"rollback_confirmado"' \
    && ok "la línea de tiempo tiene el rollback enviado y confirmado" || falla "falta el rollback en la línea de tiempo"
  hub_get "${HUB}/api/services/${SERVICIO}/deployments" | grep -q '"source": *"rollback"' \
    && ok "el historial de versiones tiene la restauración" || falla "el historial no tiene la restauración"
  bitacora="$(hub_get "${HUB}/api/audit-logs?entity=incident&action=rollback")"
  echo "$bitacora" | grep -q "\"entity_id\": *${INCIDENTE}" \
    && ok "la bitácora registra quién pidió el rollback" || falla "la bitácora no registra el rollback"

  # 6. El mensaje al cliente se genera con las horas reales y se copia; el Hub no lo envía
  mensaje="$(hub_get "${HUB}/api/incidents/${INCIDENTE}/client-message" | sed -n 's/.*"message": *"\(.*\)".*/\1/p')"
  [ -n "$mensaje" ] && { ok "mensaje para el cliente:"; echo "        ${mensaje}"; } || falla "no se generó el mensaje para el cliente"
done

echo
if [ "$fallos" -eq 0 ]; then echo "Las ${CORRIDAS} corridas cumplen (CA-2 a CA-5 y CA-7)."; else echo "${fallos} comprobación(es) fallaron."; exit 1; fi

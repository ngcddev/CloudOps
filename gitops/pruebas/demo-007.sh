#!/usr/bin/env bash
# Demo de cierre de la spec 007 (T21): recorre la demo y comprueba los criterios de acceso y bitácora.
#   1. Entrar como cliente de La Sazón: solo aparecen sus datos y sus solicitudes.
#   2. Pedir los datos de El Tornillo: "no encontrado".
#   3. Un cliente no puede ejecutar acciones de agencia; sin sesión no se responde nada.
#   4. Entrar como agencia, cambiar la prioridad de una solicitud y verla en la bitácora con usuario y hora.
# Uso:  HUB=http://hub.local HUB_PASSWORD='<contraseña>' bash gitops/pruebas/demo-007.sh
#   La contraseña es la de los usuarios sembrados (Secret hub-auth en k3s, SEED_USER_PASSWORD en .env):
#   kubectl -n hub get secret hub-auth -o jsonpath='{.data.SEED_USER_PASSWORD}' | base64 -d
# En desarrollo con docker compose:  HUB=http://localhost:8000 HUB_PASSWORD=hub-desarrollo bash gitops/pruebas/demo-007.sh
# No deja datos nuevos: clasifica una solicitud con la misma prioridad que ya tiene.
set -uo pipefail

HUB="${HUB:-http://hub.local}"
: "${HUB_PASSWORD:?Falta HUB_PASSWORD (la contraseña de los usuarios sembrados; ver el encabezado)}"
CLIENTE_USUARIO="${CLIENTE_USUARIO:-contacto@lasazon.test}"
AGENCIA_USUARIO="${AGENCIA_USUARIO:-sofia@forjadigital.test}"

fallos=0
ok()    { echo "   OK   $1"; }
falla() { echo "   FALLA $1"; fallos=$((fallos+1)); }
# Primer valor de un campo JSON simple (cadena o número)
campo() { sed -n "s/.*\"$1\": *\"\{0,1\}\([^\",}]*\)\"\{0,1\}.*/\1/p" | head -1; }
codigo() { curl -s -m 10 -o /dev/null -w '%{http_code}' "$@"; }   # código HTTP de una llamada

entrar() {   # entrar <correo> → imprime el token
  curl -s -m 10 -H 'Content-Type: application/json' -X POST "${HUB}/api/auth/login" \
    -d "{\"email\":\"$1\",\"password\":\"${HUB_PASSWORD}\"}" | campo access_token
}

echo "== 0. Sin sesión no se responde nada (CA-2) =="
[ "$(codigo "${HUB}/api/clients")" = "401" ] && ok "GET /api/clients sin sesión: 401" || falla "GET /api/clients sin sesión no dio 401"
[ "$(codigo "${HUB}/api/tickets")" = "401" ] && ok "GET /api/tickets sin sesión: 401" || falla "GET /api/tickets sin sesión no dio 401"

echo "== 1. El cliente de La Sazón ve solo lo suyo (CA-3) =="
TOKEN_CLIENTE="$(entrar "$CLIENTE_USUARIO")"
[ -n "$TOKEN_CLIENTE" ] && ok "entró como ${CLIENTE_USUARIO}" || { falla "no se pudo entrar como ${CLIENTE_USUARIO} (¿HUB_PASSWORD correcta?)"; exit 1; }
cliente_get() { curl -s -m 10 -H "Authorization: Bearer ${TOKEN_CLIENTE}" "$@"; }
clientes="$(cliente_get "${HUB}/api/clients")"
total="$(echo "$clientes" | grep -o '"contact_name"' | wc -l | tr -d ' ')"
[ "$total" = "1" ] && ok "la lista de clientes trae solo 1" || falla "la lista de clientes trae ${total}"
echo "$clientes" | grep -q "La Sazón" && ok "es Restaurante La Sazón" || falla "no aparece La Sazón"
solicitudes="$(cliente_get "${HUB}/api/tickets")"
otras="$(echo "$solicitudes" | grep -c 'productos destacados\|Solicito agregar credencial')"
[ "$otras" = "0" ] && ok "ninguna solicitud de otros clientes" || falla "aparecen solicitudes de otros clientes"

echo "== 2. Pedir los datos de El Tornillo da 'no encontrado' (CA-3) =="
TOKEN_AGENCIA="$(entrar "$AGENCIA_USUARIO")"
[ -n "$TOKEN_AGENCIA" ] && ok "entró como ${AGENCIA_USUARIO}" || { falla "no se pudo entrar como ${AGENCIA_USUARIO}"; exit 1; }
agencia_get() { curl -s -m 10 -H "Authorization: Bearer ${TOKEN_AGENCIA}" "$@"; }
# El id de El Tornillo, leído de la lista completa de la agencia
ID_TORNILLO="$(agencia_get "${HUB}/api/clients" | tr '{' '\n' | grep 'El Tornillo' | campo id)"
[ -n "$ID_TORNILLO" ] && ok "El Tornillo es el cliente #${ID_TORNILLO}" || { falla "no se encontró a El Tornillo"; exit 1; }
[ "$(codigo -H "Authorization: Bearer ${TOKEN_CLIENTE}" "${HUB}/api/clients/${ID_TORNILLO}")" = "404" ] \
  && ok "su detalle como cliente de La Sazón: 404" || falla "el cliente de La Sazón pudo pedir a El Tornillo"
TICKET_TORNILLO="$(agencia_get "${HUB}/api/tickets" | tr '{' '\n' | grep 'productos destacados' | campo id)"
[ "$(codigo -H "Authorization: Bearer ${TOKEN_CLIENTE}" "${HUB}/api/tickets/${TICKET_TORNILLO}")" = "404" ] \
  && ok "su solicitud #${TICKET_TORNILLO}: 404" || falla "el cliente de La Sazón pudo ver una solicitud de El Tornillo"

echo "== 3. Un cliente no ejecuta acciones de agencia (CA-4) =="
TICKET_PROPIO="$(echo "$solicitudes" | tr '{' '\n' | grep 'horario del menú' | campo id)"
[ "$(codigo -H "Authorization: Bearer ${TOKEN_CLIENTE}" -H 'Content-Type: application/json' -X POST \
  "${HUB}/api/tickets/${TICKET_PROPIO}/classify" -d '{"impact":"alto","urgency":"media"}')" = "403" ] \
  && ok "clasificar como cliente: 403" || falla "un cliente pudo clasificar"
[ "$(codigo -H "Authorization: Bearer ${TOKEN_CLIENTE}" "${HUB}/api/audit-logs")" = "403" ] \
  && ok "la bitácora como cliente: 403" || falla "un cliente pudo abrir la bitácora"

echo "== 4. La agencia actúa y la bitácora lo registra (CA-5, CA-6) =="
respuesta="$(curl -s -m 10 -H "Authorization: Bearer ${TOKEN_AGENCIA}" -H 'Content-Type: application/json' -X POST \
  "${HUB}/api/tickets/${TICKET_PROPIO}/classify" -d '{"impact":"alto","urgency":"media","actor_id":999}')"
[ "$(echo "$respuesta" | campo priority)" = "P2" ] && ok "solicitud #${TICKET_PROPIO} clasificada P2 (el actor del cuerpo se ignora)" || falla "no se clasificó: ${respuesta}"
bitacora="$(agencia_get "${HUB}/api/audit-logs?entity=ticket&action=cambiar_prioridad")"
fila="$(echo "$bitacora" | tr '{' '\n' | grep "\"entity_id\":${TICKET_PROPIO}," | head -1)"
[ -n "$fila" ] && ok "la bitácora tiene la acción" || falla "la acción no aparece en la bitácora"
echo "$fila" | grep -q "Sofía Ramírez" && ok "a nombre de Sofía Ramírez, no del id 999 del cuerpo" || falla "el usuario de la fila no es el de la sesión"
hora="$(echo "$bitacora" | campo created_at)"   # la primera fila es la más reciente
[ -n "$hora" ] && ok "con su hora: ${hora}" || falla "la fila no tiene hora"
[ "$(codigo -H "Authorization: Bearer ${TOKEN_AGENCIA}" -X DELETE "${HUB}/api/audit-logs/1")" != "200" ] \
  && ok "la bitácora no tiene ruta para borrar (CA-7)" || falla "la bitácora se puede borrar"

echo
if [ "$fallos" -eq 0 ]; then echo "Demo de la spec 007: todo OK"; else echo "Demo de la spec 007: ${fallos} fallo(s)"; exit 1; fi

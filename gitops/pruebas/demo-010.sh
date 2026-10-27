#!/usr/bin/env bash
# Demo de cierre de la spec 010 (T18 y T20): comprueba los dashboards con datos reales del clúster.
#   1. El tablero de la agencia trae los 3 clientes, disponibilidad y carga por técnico.
#   2. El portal de La Sazón ve lo suyo, sin costo ni horas, y no puede pedir otro cliente.
#   3. La serie del mes tiene puntos de disponibilidad y latencia cada 5 min.
#   4. Se tumba el sitio de La Sazón: aparece el incidente de alerta y el tablero lo muestra caído.
#   5. Se levanta el sitio: el incidente queda mitigado, el MTTR deja de ser nulo y la serie tiene el hueco.
#   6. Se apaga Prometheus: la consola y el portal responden 200 con «sin datos» (null / listas vacías).
#   7. Se restaura todo (el trap también lo hace si algo falla).
#
# Uso:
#   HUB_PASSWORD='<contraseña de los usuarios sembrados>' bash gitops/pruebas/demo-010.sh
#   La contraseña sale del Secret hub-auth:
#     kubectl -n hub get secret hub-auth -o jsonpath='{.data.SEED_USER_PASSWORD}' | base64 -d
#   En desarrollo con docker compose: HUB=http://localhost:8000 HUB_PASSWORD=hub-desarrollo ...
#
# Requiere: clúster con las specs 003–009 aplicadas (Hub, 3 sitios, Prometheus, Blackbox, Traefik y
# Alertmanager), entradas *.hub.local en hosts, curl y kubectl. Variables opcionales:
#   HUB (http://hub.local), MES (mes actual), LIMITE (300 s), CLIENTE_ID (1), NAMESPACE (cliente-restaurante),
#   SITIO (http://restaurante.hub.local).
#
# Ojo: deja el sitio y Prometheus apagados un momento; al final (o al fallar) los vuelve a levantar.
set -uo pipefail

HUB="${HUB:-http://hub.local}"
MES="${MES:-$(date +%Y-%m)}"
LIMITE="${LIMITE:-300}"
CLIENTE_ID="${CLIENTE_ID:-1}"
NAMESPACE="${NAMESPACE:-cliente-restaurante}"
SITIO="${SITIO:-http://restaurante.hub.local}"
USUARIO_AGENCIA="${USUARIO_AGENCIA:-sofia@forjadigital.test}"
USUARIO_CLIENTE="${USUARIO_CLIENTE:-contacto@lasazon.test}"
: "${HUB_PASSWORD:?Falta HUB_PASSWORD (la contraseña de los usuarios sembrados; ver el encabezado)}"

fallos=0
INCIDENTE=""
SITIO_TOCADO=0
PROMETHEUS_TOCADO=0

ok()    { echo "   OK   $1"; }
falla() { echo "   FALLA $1"; fallos=$((fallos+1)); }
# Primer valor de un campo JSON simple (cadena o número)
campo() { sed -n "s/.*\"$1\": *\"\{0,1\}\([^\",}]*\)\"\{0,1\}.*/\1/p" | head -1; }
codigo() { curl -s -m 15 -o /dev/null -w '%{http_code}' "$@"; }

entrar() {   # entrar <correo> → token
  curl -s -m 15 -H 'Content-Type: application/json' -X POST "${HUB}/api/auth/login" \
    -d "{\"email\":\"$1\",\"password\":\"${HUB_PASSWORD}\"}" | campo access_token
}

TOKEN_AGENCIA="$(entrar "$USUARIO_AGENCIA")"
TOKEN_CLIENTE="$(entrar "$USUARIO_CLIENTE")"
if [ -z "$TOKEN_AGENCIA" ] || [ -z "$TOKEN_CLIENTE" ]; then
  echo "No se pudo entrar al Hub (¿HUB_PASSWORD correcta y usuarios sembrados?)." >&2
  exit 2
fi
agencia_get() { curl -s -m 60 -H "Authorization: Bearer ${TOKEN_AGENCIA}" "$@"; }
cliente_get() { curl -s -m 60 -H "Authorization: Bearer ${TOKEN_CLIENTE}" "$@"; }

restaurar() {
  if [ "$SITIO_TOCADO" = "1" ]; then
    kubectl -n "$NAMESPACE" scale deploy/web --replicas=1 >/dev/null 2>&1 || true
  fi
  if [ "$PROMETHEUS_TOCADO" = "1" ]; then
    kubectl -n monitoring scale deploy/prometheus --replicas=1 >/dev/null 2>&1 || true
  fi
}
trap restaurar EXIT

# ---------- Comprobaciones del clúster ----------

if ! kubectl get ns "$NAMESPACE" >/dev/null 2>&1; then
  echo "FALLA: no hay clúster a la mano (no existe el namespace ${NAMESPACE})." >&2
  echo "       Aplica la 003-009 o usa un kubeconfig válido y vuelve a intentar." >&2
  exit 2
fi
if ! kubectl -n monitoring get deploy/prometheus >/dev/null 2>&1; then
  echo "FALLA: falta Prometheus en monitoring (spec 008, T22)." >&2
  exit 2
fi
if ! kubectl -n "$NAMESPACE" get deploy/web >/dev/null 2>&1; then
  echo "FALLA: falta el Deployment web del sitio en ${NAMESPACE}." >&2
  exit 2
fi

tablero() { agencia_get "${HUB}/api/dashboard/agency?month=$1"; }
ficha()   { cliente_get "${HUB}/api/dashboard/client/${CLIENTE_ID}?month=$1"; }
serie()   { agencia_get "${HUB}/api/dashboard/client/${CLIENTE_ID}/series?month=$1"; }
cliente_del_tablero() { tablero "${1:-$MES}" | tr '{' '\n' | grep "\"client_id\":${CLIENTE_ID}," | head -1; }
incidentes() { agencia_get "${HUB}/api/incidents?client_id=${CLIENTE_ID}"; }
sitio_arriba() { [ "$(codigo "${SITIO}/health")" = "200" ]; }
sitio_abajo()  { [ "$(codigo "${SITIO}/health")" != "200" ]; }

esperar() {  # esperar "<descripción>" <función que devuelve 0 al cumplirse>
  local descripcion="$1" comprobacion="$2" limite
  limite=$(( $(date +%s) + LIMITE ))
  while [ "$(date +%s)" -lt "$limite" ]; do
    if "$comprobacion"; then return 0; fi
    sleep 5
  done
  falla "se acabó el tiempo esperando: ${descripcion}"
  return 1
}

# ---------- 1. Consola de la agencia (CA-1, CA-2, CA-3) ----------

echo "== 1. Tablero de la agencia del mes ${MES} =="
TABLERO="$(tablero "$MES")"
n_clientes="$(echo "$TABLERO" | grep -o '"client_id":' | wc -l | tr -d ' ')"
[ "$n_clientes" = "3" ] && ok "3 clientes en el tablero" || falla "hay ${n_clientes} clientes, se esperaban 3"
n_tecnicos="$(echo "$TABLERO" | grep -o '"user_id":' | wc -l | tr -d ' ')"
[ "$n_tecnicos" -ge 2 ] && ok "${n_tecnicos} técnicos con su carga" || falla "la carga por técnico está vacía"
LINEA="$(cliente_del_tablero "$MES")"
if [ -n "$LINEA" ]; then
  ok "La Sazón aparece en el tablero"
  echo "$LINEA" | grep -q '"sla_compliance":' && ok "trae cumplimiento de SLA" || falla "falta sla_compliance"
  echo "$LINEA" | grep -q '"open_tickets":' && ok "trae solicitudes abiertas/cerradas" || falla "faltan solicitudes"
  echo "$LINEA" | grep -q '"hours":' && echo "$LINEA" | grep -q '"cost":' \
    && ok "trae horas y costo" || falla "faltan horas o costo"
  if echo "$LINEA" | grep -q '"availability":null'; then
    falla "la disponibilidad es null con Prometheus encendido (¿Blackbox o job sitios?)"
  else
    ok "trae disponibilidad del mes"
  fi
  echo "$LINEA" | grep -q '"cumple_objetivo":true\|"cumple_objetivo":false' \
    && ok "dice si cumple el objetivo del plan" || falla "no dice si cumple el objetivo"
else
  falla "La Sazón no aparece en el tablero"
fi

# ---------- 2. Portal del cliente (CA-4, CA-7) ----------

echo "== 2. Portal de La Sazón =="
FICHA="$(ficha "$MES")"
echo "$FICHA" | grep -q '"availability":' && ok "ve su disponibilidad" || falla "no ve su disponibilidad"
echo "$FICHA" | grep -q '"slo_availability":' && ok "ve el objetivo de su plan" || falla "no ve el objetivo"
echo "$FICHA" | grep -qi '"cost"\|"hours"\|"technicians"' && falla "el portal muestra costo, horas o técnicos" \
  || ok "sin costo, horas ni técnicos (CA-7)"
[ "$(codigo -H "Authorization: Bearer ${TOKEN_CLIENTE}" "${HUB}/api/dashboard/client/2?month=${MES}")" = "404" ] \
  && ok "pedir El Tornillo da 404" || falla "el cliente pudo ver otro cliente"

# ---------- 3. Serie de 5 minutos (CA-6) ----------

echo "== 3. Serie de disponibilidad y latencia =="
SERIE="$(serie "$MES")"
echo "$SERIE" | grep -q '"availability":\[' && echo "$SERIE" | grep -q '"latency_p95":\[' \
  && ok "la respuesta trae las dos series" || falla "faltan las series"
n_puntos="$(echo "$SERIE" | grep -o '"timestamp":' | wc -l | tr -d ' ')"
[ "$n_puntos" -gt 0 ] && ok "${n_puntos} puntos en la serie" || falla "la serie está vacía (¿Prometheus sin datos?)"

# ---------- 4. La caída (T18) ----------

echo "== 4. Caída del sitio de La Sazón =="
BASE_ID="$(incidentes | grep -o '"id":[0-9]*' | cut -d: -f2 | sort -n | tail -1)"
BASE_ID="${BASE_ID:-0}"
SITIO_TOCADO=1
kubectl -n "$NAMESPACE" scale deploy/web --replicas=0 >/dev/null \
  && ok "sitio apagado (0 réplicas)" || falla "no se pudo apagar el sitio"
esperar "que el sitio deje de responder" sitio_abajo && ok "el sitio no responde"

detalle_incidente() { agencia_get "${HUB}/api/incidents/${INCIDENTE}"; }
nuevo_incidente() {
  local linea id
  # Se busca un incidente de alerta abierto con id mayor al de la línea base: así no cuenta uno viejo
  linea="$(incidentes | tr '{' '\n' | grep '"source":"alerta"' | grep '"status":"abierto"' | head -1)"
  id="$(echo "$linea" | grep -o '"id":[0-9]*' | head -1 | cut -d: -f2)"
  if [ -n "$id" ] && [ "$id" -gt "$BASE_ID" ]; then INCIDENTE="$id"; return 0; fi
  return 1
}
if esperar "que el monitoreo abra el incidente" nuevo_incidente; then
  ok "incidente #${INCIDENTE} abierto por la alerta"
  detalle_incidente | grep -q '"source":"alerta"' && ok "la fuente es la alerta" || falla "la fuente no es la alerta"
else
  falla "no se abrió un incidente nuevo (¿Alertmanager y el webhook del Hub?)"
fi

caido_en_tablero() { cliente_del_tablero "$MES" | grep -q '"service_status":"caido"'; }
esperar "que el tablero muestre el sitio caído" caido_en_tablero && ok "el tablero muestra el sitio caído"

# ---------- 5. La recuperación y el MTTR (CA-9) ----------

echo "== 5. Recuperación y MTTR =="
kubectl -n "$NAMESPACE" scale deploy/web --replicas=1 >/dev/null \
  && ok "sitio encendido (1 réplica)" || falla "no se pudo encender el sitio"
SITIO_TOCADO=0
kubectl -n "$NAMESPACE" rollout status deploy/web --timeout=180s >/dev/null 2>&1 || true
esperar "que el sitio responda 200" sitio_arriba && ok "el sitio responde 200"

incidente_mitigado() {
  local detalle
  detalle="$(detalle_incidente)"
  echo "$detalle" | grep -q '"status":"mitigado"\|"status":"cerrado"'
}
if esperar "que el incidente quede mitigado" incidente_mitigado; then
  ok "incidente #${INCIDENTE} mitigado"
  MTTR="$(cliente_del_tablero "$MES" | grep -o '"mttr":[0-9.]*' | head -1 | cut -d: -f2)"
  [ -n "$MTTR" ] && ok "el tablero muestra el MTTR: ${MTTR} min" || falla "el MTTR sigue en null"
  linea_incidente="$(incidentes | tr '{' '\n' | grep "\"id\":${INCIDENTE}," | head -1)"
  echo "$linea_incidente" | grep -q '"status":"mitigado"\|"status":"cerrado"' \
    && ok "el incidente aparece en el mes del cliente" || falla "el incidente no aparece en el listado"
fi

SERIE_FINAL="$(serie "$MES")"
echo "$SERIE_FINAL" | grep -q '"value":0' \
  && ok "la serie muestra el hueco de la caída (disponibilidad 0)" \
  || falla "la serie no muestra valores en 0 (¿la caída duró menos que el sondeo?)"

# ---------- 6. Prometheus apagado (CA-8) ----------

echo "== 6. Prometheus apagado =="
# Se usa el mismo mes de la demo, pero hay que esperar a que venza la caché de 60 s de la API
# (integrations/prometheus.py). Con otro mes sin datos la prueba no probaría nada: daría null
# aunque Prometheus estuviera encendido.
PROMETHEUS_TOCADO=1
kubectl -n monitoring scale deploy/prometheus --replicas=0 >/dev/null \
  && ok "Prometheus apagado" || falla "no se pudo apagar Prometheus"
kubectl -n monitoring rollout status deploy/prometheus --timeout=90s >/dev/null 2>&1 || true
echo "   (esperando 65 s a que venza la caché de disponibilidad)"
sleep 65

TABLERO_OFF="$(tablero "$MES")"
n_null="$(echo "$TABLERO_OFF" | grep -o '"availability":null' | wc -l | tr -d ' ')"
[ "$n_null" = "3" ] && ok "la consola responde con «sin datos» en los 3 clientes" \
  || falla "la consola no dio null para los 3 clientes (${n_null})"
[ "$(codigo -H "Authorization: Bearer ${TOKEN_AGENCIA}" "${HUB}/api/dashboard/agency?month=${MES}")" = "200" ] \
  && ok "la consola carga igual (200)" || falla "la consola no respondió 200"

FICHA_OFF="$(ficha "$MES")"
echo "$FICHA_OFF" | grep -q '"availability":null' && ok "el portal muestra «sin datos»" \
  || falla "el portal no muestra null"
SERIE_OFF="$(serie "$MES")"
echo "$SERIE_OFF" | grep -q '"availability":\[\]' && echo "$SERIE_OFF" | grep -q '"latency_p95":\[\]' \
  && ok "la serie queda vacía, sin errores" || falla "la serie no quedó vacía"

kubectl -n monitoring scale deploy/prometheus --replicas=1 >/dev/null 2>&1 || true
PROMETHEUS_TOCADO=0
ok "Prometheus encendido de nuevo (puede tardar en volver a tener datos)"

# ---------- Resumen ----------

echo
if [ "$fallos" -eq 0 ]; then
  echo "Demo de la spec 010: todo OK (mes ${MES}, incidente ${INCIDENTE:-sin dato})."
else
  echo "Demo de la spec 010: ${fallos} fallo(s)."
  exit 1
fi

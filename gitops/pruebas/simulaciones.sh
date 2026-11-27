#!/usr/bin/env bash
# Simulaciones de falla en el clúster (spec 016): qué pasa y qué se ve cuando una réplica se cae, la red se vuelve lenta o la API se satura.
#   replica     borra el Pod del sitio: el Deployment lo recrea; mide cuántos segundos no respondió y comprueba que NO hay alerta
#               (una caída más corta que los 30 s de SitioCaido no es un incidente: CA-9 de la spec 008)
#   latencia    añade 400 ms de espera a la red de cada Pod (netem en sus interfaces veth) durante 45 s y mide probe_duration_seconds en Prometheus
#   saturacion  lanza carga contra la API del Hub y comprueba que el HPA sube de 1 a 2 réplicas y vuelve a 1 al terminar
# Uso:  KUBECONFIG=... [SITIO=colegio] bash gitops/pruebas/simulaciones.sh [replica|latencia|saturacion|todas]
# Requisitos: clúster con el sitio dado de alta, metrics-server (k3s) y Docker (la latencia usa un contenedor con tc en la red del nodo).
# Todo lo que cambia se deshace al terminar (también si se interrumpe): la regla de red y el Pod de carga.
set -uo pipefail

SITIO="${SITIO:-colegio}"
NS="cliente-${SITIO}"
NODO="${NODO:-k3d-hub-server-0}"
ESCENARIO="${1:-todas}"
export MSYS_NO_PATHCONV=1

fallos=0
ok()    { echo "   OK   $1"; }
falla() { echo "   FALLA $1"; fallos=$((fallos+1)); }
prom()  { kubectl -n monitoring exec deploy/prometheus -- wget -qO- "http://localhost:9090/api/v1/query?query=$1" 2>/dev/null; }
valor() { sed -n 's/.*"value":\[[0-9.]*,"\([^"]*\)"\].*/\1/p' | head -1; }

tc_node() {
  docker run --rm --net "container:${NODO}" --cap-add NET_ADMIN alpine sh -c "apk add -q iproute2-tc >/dev/null 2>&1; $1" 2>&1
}
# Interfaces veth de los Pods del nodo: el tráfico entre Pods del mismo nodo sale por ellas, no por cni0
VETH="ip -o link | awk -F'[ :@]+' '/veth/ {print \$2}'"
latencia_on()  { tc_node "for d in \$($VETH); do tc qdisc add dev \$d root netem delay 150ms; done"; }
latencia_off() { tc_node "for d in \$($VETH); do tc qdisc del dev \$d root; done"; }
limpiar() {
  latencia_off >/dev/null 2>&1
  kubectl -n hub delete pod carga --ignore-not-found --wait=false >/dev/null 2>&1
}
trap limpiar EXIT

replica() {
  echo "== Réplica caída: se borra el Pod de ${NS}"
  kubectl get ns "$NS" >/dev/null 2>&1 || { falla "no existe ${NS}: dé de alta el sitio primero"; return; }
  antes="$(prom "count(ALERTS%7Balertname%3D%22SitioCaido%22%2Calertstate%3D%22firing%22%7D)" | valor)"
  pod="$(kubectl -n "$NS" get pod -l app=web -o name | head -1)"
  inicio=$(date +%s); kubectl -n "$NS" delete "$pod" --wait=false >/dev/null
  caido=0
  # Lo que cuenta es lo que ve el monitoreo: el sondeo de Blackbox, cada 5 s
  for _ in $(seq 1 90); do
    sleep 2
    [ "$(prom "probe_success%7Bjob%3D%22sitios%22%2Cclient%3D%22${SITIO}%22%7D" | valor)" = "1" ] && [ "$caido" = 1 ] && break
    [ "$(prom "probe_success%7Bjob%3D%22sitios%22%2Cclient%3D%22${SITIO}%22%7D" | valor)" = "0" ] && caido=1
    [ $(( $(date +%s) - inicio )) -ge 30 ] && [ "$caido" = 0 ] && break   # nunca lo vio caído: el reinicio fue más rápido que el sondeo
  done
  seg=$(( $(date +%s) - inicio ))
  [ "$(prom "probe_success%7Bjob%3D%22sitios%22%2Cclient%3D%22${SITIO}%22%7D" | valor)" = "1" ] && ok "el sondeo ve el sitio sano a los ${seg} s del borrado" || falla "el sitio no volvió en 3 minutos"
  [ "$caido" = 0 ] && ok "el reinicio fue más rápido que el sondeo de 5 s: el monitoreo ni lo vio" || { [ "$seg" -lt 30 ] && ok "la caída duró ${seg} s, menos de los 30 s de SitioCaido: no es un incidente" || echo "   (duró ${seg} s: SitioCaido puede haber disparado)"; }
  disparos="$(prom "count(ALERTS%7Balertname%3D%22SitioCaido%22%2Calertstate%3D%22firing%22%2Cclient%3D%22${SITIO}%22%7D)" | valor)"
  [ -z "$disparos" ] || [ "$disparos" = "0" ] && ok "no hay alerta SitioCaido de ${SITIO}" || echo "   (SitioCaido de ${SITIO} está disparada: ${disparos})"
  : "$antes" "$caido"
}

latencia() {
  echo "== Latencia: +150 ms en la red de los Pods durante 45 s"
  base="$(prom "probe_duration_seconds%7Bjob%3D%22sitios%22%2Cclient%3D%22${SITIO}%22%7D" | valor)"
  echo "   sondeo antes: ${base:-sin dato} s"
  latencia_on >/dev/null || { falla "no se pudo añadir la latencia (¿Docker y el módulo netem?)"; return; }
  sleep 45
  durante="$(prom "max_over_time(probe_duration_seconds%7Bjob%3D%22sitios%22%2Cclient%3D%22${SITIO}%22%7D%5B40s%5D)" | valor)"
  latencia_off >/dev/null
  echo "   sondeo durante (máximo): ${durante:-sin dato} s"
  awk -v d="${durante:-0}" -v b="${base:-0}" 'BEGIN { exit !(d > b + 0.3) }' && ok "Prometheus vio la lentitud: el sondeo pasó de ${base} s a ${durante} s" || falla "el sondeo no cambió"
  sleep 20
  despues="$(prom "probe_duration_seconds%7Bjob%3D%22sitios%22%2Cclient%3D%22${SITIO}%22%7D" | valor)"
  awk -v d="${despues:-9}" 'BEGIN { exit !(d < 0.3) }' && ok "con la latencia retirada el sondeo volvió a ${despues} s" || falla "el sondeo sigue lento (${despues} s)"
}

saturacion() {
  echo "== Saturación: carga contra la API del Hub"
  kubectl -n hub delete pod carga --ignore-not-found >/dev/null 2>&1
  kubectl -n hub run carga --image=busybox:1.36 --restart=Never --overrides='{"spec":{"securityContext":{"runAsNonRoot":true,"runAsUser":65534,"seccompProfile":{"type":"RuntimeDefault"}},"containers":[{"name":"carga","image":"busybox:1.36","command":["sh","-c","for i in $(seq 1 12); do (while true; do wget -qO- http://api:8000/health >/dev/null; done) & done; wait"],"securityContext":{"allowPrivilegeEscalation":false,"capabilities":{"drop":["ALL"]}},"resources":{"limits":{"cpu":"800m","memory":"64Mi"}}}]}}' >/dev/null 2>&1 \
    || { falla "no se pudo lanzar la carga"; return; }
  subio=0
  for _ in $(seq 1 24); do
    sleep 10
    r="$(kubectl -n hub get deploy api -o jsonpath='{.status.readyReplicas}')"
    cpu="$(kubectl -n hub get hpa api -o jsonpath='{.status.currentMetrics[0].resource.current.averageUtilization}')"
    echo "   api: ${r:-0} réplica(s), CPU ${cpu:-?}%"
    [ "${r:-0}" -ge 2 ] && { subio=1; break; }
  done
  [ "$subio" = 1 ] && ok "el HPA subió la API a 2 réplicas" || falla "el HPA no subió la API (¿la carga no alcanzó el 70 % de CPU?)"
  kubectl -n hub delete pod carga --ignore-not-found --wait=false >/dev/null 2>&1
  echo "   (la bajada a 1 réplica espera la ventana de estabilización de 2 minutos)"
  bajo=0
  for _ in $(seq 1 24); do
    sleep 10
    [ "$(kubectl -n hub get deploy api -o jsonpath='{.spec.replicas}')" = "1" ] && { bajo=1; break; }
  done
  [ "$bajo" = 1 ] && ok "terminada la carga, el HPA volvió a 1 réplica" || falla "el HPA no volvió a 1 réplica en 4 minutos"
}

case "$ESCENARIO" in
  replica) replica ;;
  latencia) latencia ;;
  saturacion) saturacion ;;
  todas) replica; latencia; saturacion ;;
  *) echo "Escenario desconocido: ${ESCENARIO}" >&2; exit 2 ;;
esac
echo
[ "$fallos" -eq 0 ] && echo "Simulaciones: todo como se esperaba." || { echo "${fallos} comprobación(es) fallaron."; exit 1; }

#!/usr/bin/env bash
# Informe de capacidad (spec 019, T04): por cada namespace de cliente, cuánto de su cuota tiene reservado (límites de los Pods), cuánto usa de verdad y qué margen queda;
# y lo mismo del nodo. Solo lee (kubectl get y kubectl top, este último de metrics-server); no cambia nada.
#   reservado  suma de los límites de los Pods frente a la cuota del plan (ResourceQuota)
#   uso        lo que gastan ahora los Pods (metrics-server)
#   margen     cuota − reservado: lo que cabe todavía sin cambiar de plan
# Con --estricto sale con código 1 si algún namespace tiene reservado más del 90 % de su cuota (sin margen para una publicación con Pod extra).
# Uso:  KUBECONFIG=... bash observability/capacidad.sh [--estricto]
set -uo pipefail
ESTRICTO=0; [ "${1:-}" = "--estricto" ] && ESTRICTO=1

command -v kubectl >/dev/null 2>&1 || { echo "Hace falta kubectl" >&2; exit 2; }

# Convierte cantidades de Kubernetes a milicores (cpu) o MiB (memoria); la unidad la decide quien llama
AWK_FUNCIONES='
function cpu(v) { if (v ~ /m$/) { sub(/m$/, "", v); return v + 0 } return v * 1000 }
function mem(v) { if (v ~ /Gi$/) { sub(/Gi$/, "", v); return v * 1024 } if (v ~ /Mi$/) { sub(/Mi$/, "", v); return v + 0 } if (v ~ /Ki$/) { sub(/Ki$/, "", v); return v / 1024 } return v / 1048576 }
'

echo "== Namespaces de clientes: cuota, reservado, uso y margen =="
printf '%-26s %-18s %-18s %-12s %-12s %s\n' "namespace" "CPU reservada/cuota" "Mem reservada/cuota" "CPU uso" "Mem uso" "margen"
USO="$(kubectl top pods -A --no-headers 2>/dev/null || true)"
sin_margen=0
while read -r ns lc uc lm um; do
  [ -z "$ns" ] && continue
  uso_cpu="$(printf '%s\n' "$USO" | awk -v ns="$ns" "$AWK_FUNCIONES"'$1 == ns { c += cpu($3); m += mem($4) } END { printf "%dm", c }')"
  uso_mem="$(printf '%s\n' "$USO" | awk -v ns="$ns" "$AWK_FUNCIONES"'$1 == ns { c += cpu($3); m += mem($4) } END { printf "%dMi", m }')"
  linea="$(awk -v lc="$lc" -v uc="$uc" -v lm="$lm" -v um="$um" "$AWK_FUNCIONES"'BEGIN {
    pc = (cpu(lc) > 0) ? 100 * cpu(uc) / cpu(lc) : 0; pm = (mem(lm) > 0) ? 100 * mem(um) / mem(lm) : 0
    peor = (pc > pm) ? pc : pm
    estado = (peor > 90) ? "SIN MARGEN" : (peor > 70) ? "AJUSTADO" : "HOLGADO"
    printf "%dm / %dm (%d%%)|%dMi / %dMi (%d%%)|%s (%d%% libre en CPU, %d%% en memoria)", cpu(uc), cpu(lc), pc, mem(um), mem(lm), pm, estado, 100 - pc, 100 - pm
    if (peor > 90) exit 3 }')"
  [ "$?" = 3 ] && sin_margen=$((sin_margen + 1))
  printf '%-26s %-18s %-18s %-12s %-12s %s\n' "$ns" "${linea%%|*}" "$(printf '%s' "$linea" | cut -d'|' -f2)" "$uso_cpu" "$uso_mem" "$(printf '%s' "$linea" | cut -d'|' -f3)"
done < <(kubectl get resourcequota -A --no-headers \
  -o custom-columns='NS:.metadata.namespace,LC:.status.hard.limits\.cpu,UC:.status.used.limits\.cpu,LM:.status.hard.limits\.memory,UM:.status.used.limits\.memory' \
  | awk '$1 ~ /^cliente-/')

echo
echo "== Nodo =="
kubectl top nodes --no-headers 2>/dev/null | awk '{ printf "%s: CPU %s (%s), memoria %s (%s)\n", $1, $2, $3, $4, $5 }'
kubectl get nodes --no-headers -o custom-columns='N:.metadata.name,CPU:.status.allocatable.cpu,MEM:.status.allocatable.memory' | awk "$AWK_FUNCIONES"'{ printf "%s asignable: %dm de CPU y %dMi de memoria\n", $1, cpu($2), mem($3) }'

echo
if [ "$sin_margen" -gt 0 ]; then
  echo "${sin_margen} namespace(s) sin margen (más del 90 % de la cuota reservada)."
  [ "$ESTRICTO" = 1 ] && exit 1
else
  echo "Todos los namespaces de clientes tienen margen."
fi

#!/usr/bin/env bash
# Demo de cierre de la spec 003 (T18): recorre los pasos de la demo y comprueba los criterios CA-1 a CA-6.
# Uso: bash gitops/pruebas/demo.sh        (necesita el clúster con todo aplicado y las entradas de hosts)
set -uo pipefail
cd "$(dirname "$0")"

fallos=0
ok()    { echo "   OK   $1"; }
falla() { echo "   FALLA $1"; fallos=$((fallos+1)); }

echo "== 1. Espacios y cuota de cada cliente según su plan (CA-1, CA-2) =="
kubectl get ns -l app.kubernetes.io/part-of=cloudops-hub -L hub/client,hub/plan --no-headers | sed 's/^/   /'
for ns in hub argocd monitoring gitea cliente-restaurante cliente-ferreteria cliente-consultorio; do
  kubectl get ns "$ns" >/dev/null 2>&1 && ok "existe $ns" || falla "falta $ns"
done
# plan -> cuota esperada (seed/plans.json)
esperada() { case "$1" in basico) echo "250m 256Mi";; estandar) echo "500m 512Mi";; premium) echo "1000m 1Gi";; esac; }
for par in restaurante:premium ferreteria:estandar consultorio:basico; do
  c="${par%%:*}"; plan="${par##*:}"
  real="$(kubectl -n "cliente-$c" get resourcequota plan -o jsonpath='{.spec.hard.limits\.cpu} {.spec.hard.limits\.memory}')"
  # Kubernetes guarda 1000m como 1: se compara en milicores
  cpu="${real%% *}"; case "$cpu" in *m) ;; *) cpu="$((cpu * 1000))m";; esac; real="$cpu ${real#* }"
  [ "$real" = "$(esperada "$plan")" ] && ok "cliente-$c: cuota $real = plan $plan" || falla "cliente-$c: cuota $real, se esperaba $(esperada "$plan")"
done

echo "== 2. Los 3 sitios y el Hub por su dirección (CA-5) =="
for host in restaurante ferreteria consultorio; do
  codigo="$(curl -s -m 10 -o /dev/null -w '%{http_code}' "http://${host}.hub.local/health")"
  [ "$codigo" = "200" ] && ok "${host}.hub.local/health -> 200" || falla "${host}.hub.local/health -> $codigo"
done
codigo="$(curl -s -m 10 -o /dev/null -w '%{http_code}' http://hub.local/)"
[ "$codigo" = "200" ] && ok "hub.local -> 200" || falla "hub.local -> $codigo"

echo "== 3. De la sala del restaurante a la ferretería (CA-3) =="
bash ./aislamiento-red.sh >/tmp/demo-red.log 2>&1 && ok "acceso entre clientes bloqueado" || { falla "aislamiento de red"; sed 's/^/     /' /tmp/demo-red.log; }

echo "== 4. Contenedor como root en cliente-restaurante (CA-4) =="
bash ./pod-security.sh >/tmp/demo-ps.log 2>&1 && ok "root y privilegiado rechazados" || { falla "Pod Security"; sed 's/^/     /' /tmp/demo-ps.log; }

echo "== 5. Un sitio con la salud fallando no recibe tráfico (CA-6) =="
bash ./readiness.sh >/tmp/demo-ready.log 2>&1 && ok "el Pod v2 no recibe tráfico" || { falla "readiness"; sed 's/^/     /' /tmp/demo-ready.log; }

echo
[ "$fallos" -eq 0 ] && echo "DEMO COMPLETA: todos los criterios pasan." || echo "DEMO CON $fallos FALLO(S)."
exit "$fallos"

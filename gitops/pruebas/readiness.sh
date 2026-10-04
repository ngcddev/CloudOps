#!/usr/bin/env bash
# Prueba de que un sitio con la salud fallando no recibe tráfico (spec 003 T15, CA-6).
# Crea en cliente-restaurante un Deployment aparte (web-v2-prueba) con la imagen v2, que responde 500
# en /health, y la misma etiqueta que el Service. Comprueba que su Pod nunca queda Ready y que el
# Service solo lista el Pod sano. No toca el Deployment `web` del sitio real.
# Uso: bash gitops/pruebas/readiness.sh [cliente]   (por defecto restaurante)
set -uo pipefail

CLIENTE="${1:-restaurante}"
NS="cliente-${CLIENTE}"
PRUEBA="web-v2-prueba"
trap 'kubectl -n "$NS" delete deploy "$PRUEBA" --now >/dev/null 2>&1' EXIT

# Copia del Deployment real con otro nombre y la imagen v2
kubectl -n "$NS" get deploy web -o json | python -c "
import json, sys
d = json.load(sys.stdin)
d['metadata'] = {'name': '$PRUEBA', 'namespace': '$NS'}
d.pop('status', None)
d['spec']['selector']['matchLabels'] = {'app': 'web', 'prueba': 'v2'}
tpl = d['spec']['template']
tpl['metadata']['labels'] = {'app': 'web', 'prueba': 'v2'}
c = tpl['spec']['containers'][0]
c['image'] = c['image'].rsplit(':', 1)[0] + ':v2'
json.dump(d, sys.stdout)
" | kubectl apply -f - >/dev/null || { echo "No se pudo crear el Deployment de prueba"; exit 2; }

echo ">> Esperando a que el Pod v2 arranque (no debe quedar Ready)"
kubectl -n "$NS" wait --for=condition=PodScheduled pod -l prueba=v2 --timeout=60s >/dev/null
sleep 25   # varias rondas de readiness probe

kubectl -n "$NS" get pods -l app=web -L prueba
listados=$(kubectl -n "$NS" get endpoints web -o jsonpath='{.subsets[*].addresses[*].ip}')
pod_v2_ip=$(kubectl -n "$NS" get pod -l prueba=v2 -o jsonpath='{.items[0].status.podIP}')
listo=$(kubectl -n "$NS" get pod -l prueba=v2 -o jsonpath='{.items[0].status.containerStatuses[0].ready}')
echo "Destinos del Service web: ${listados:-ninguno}   |   IP del Pod v2: $pod_v2_ip"

fallos=0
[ "$listo" = "false" ] && echo "OK: el Pod v2 está 0/1 Ready" || { echo "FALLÓ: el Pod v2 quedó Ready"; fallos=1; }
case " $listados " in
  *" $pod_v2_ip "*) echo "FALLÓ: el Service lista al Pod v2"; fallos=1 ;;
  *) echo "OK: el Service no lista al Pod v2" ;;
esac
exit $fallos

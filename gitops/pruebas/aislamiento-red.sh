#!/usr/bin/env bash
# Prueba de aislamiento de red entre clientes (spec 003 T13, CA-3).
# Lanza un Pod busybox en cliente-restaurante e intenta llegar (1) a su propio sitio, que debe
# funcionar, y (2) al sitio de la ferretería, que debe fallar (rechazado o por tiempo de espera, según el CNI).
# Uso: bash gitops/pruebas/aislamiento-red.sh [origen] [destino]   (por defecto restaurante -> ferreteria)
set -uo pipefail

ORIGEN="${1:-restaurante}"
DESTINO="${2:-ferreteria}"
NS="cliente-${ORIGEN}"
IMAGEN="${IMAGEN:-gitea.hub.local/forja-digital/busybox:v1}"
POD="prueba-red"

kubectl -n "$NS" delete pod "$POD" --ignore-not-found --now >/dev/null 2>&1
# El Pod cumple el perfil `restricted` del namespace: sin root, sin privilegios.
kubectl -n "$NS" run "$POD" --image="$IMAGEN" --restart=Never \
  --overrides='{"spec":{"securityContext":{"runAsNonRoot":true,"runAsUser":1000,"seccompProfile":{"type":"RuntimeDefault"}},"containers":[{"name":"prueba-red","image":"'"$IMAGEN"'","command":["sleep","300"],"securityContext":{"allowPrivilegeEscalation":false,"capabilities":{"drop":["ALL"]}},"resources":{"limits":{"cpu":"50m","memory":"32Mi"}}}]}}' >/dev/null
kubectl -n "$NS" wait --for=condition=Ready "pod/$POD" --timeout=120s >/dev/null || { echo "El Pod de prueba no arrancó"; exit 2; }
trap 'kubectl -n "$NS" delete pod "$POD" --now >/dev/null 2>&1' EXIT

fallos=0
echo ">> Desde $NS a su propio sitio (debe funcionar)"
if kubectl -n "$NS" exec "$POD" -- wget -q -T 5 -O - "http://web.${NS}.svc/health"; then echo; echo "   OK"; else echo "   FALLÓ (debía funcionar)"; fallos=1; fi

echo ">> Desde $NS al sitio de ${DESTINO} (debe fallar: rechazado o tiempo de espera)"
if kubectl -n "$NS" exec "$POD" -- wget -q -T 5 -O - "http://web.cliente-${DESTINO}.svc/health"; then echo; echo "   FALLÓ: el acceso entre clientes NO está bloqueado"; fallos=1; else echo "   OK: bloqueado"; fi

exit $fallos

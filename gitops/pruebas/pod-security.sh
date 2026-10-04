#!/usr/bin/env bash
# Prueba de Pod Security Admission `restricted` (spec 003 T14, CA-4).
# Intenta lanzar en cliente-restaurante (1) un Pod que corre como root y (2) uno privilegiado:
# los dos deben ser rechazados. Termina con error si alguno llegó a crearse.
# Uso: bash gitops/pruebas/pod-security.sh [cliente]   (por defecto restaurante)
set -uo pipefail

NS="cliente-${1:-restaurante}"
fallos=0

probar() {   # probar "<descripción>" <argumentos de kubectl run>
  local descripcion="$1"; shift
  echo ">> $descripcion (debe ser rechazado)"
  if salida=$(kubectl -n "$NS" run "$@" 2>&1); then
    echo "   FALLÓ: el Pod se creó"; kubectl -n "$NS" delete pod "$2" --now >/dev/null 2>&1
    fallos=1
  elif echo "$salida" | grep -q 'violates PodSecurity "restricted'; then
    echo "   OK: $(echo "$salida" | grep -o 'violates PodSecurity "restricted:[a-z]*"')"
  else
    echo "   FALLÓ por otra razón:"; echo "$salida" | sed 's/^/     /'; fallos=1
  fi
}

# 1) Sin securityContext: la imagen corre como root
probar "Contenedor que corre como root" root-test --image=nginx
# 2) Privilegiado y como root explícito
probar "Contenedor privilegiado" privilegiado-test --image=nginx \
  --overrides='{"spec":{"containers":[{"name":"privilegiado-test","image":"nginx","securityContext":{"privileged":true,"runAsUser":0}}]}}'

exit $fallos

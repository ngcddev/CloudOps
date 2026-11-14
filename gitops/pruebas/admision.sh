#!/usr/bin/env bash
# Prueba la política de admisión de imágenes (spec 016) contra el API server del clúster, sin crear nada (dry-run del servidor):
#   - una imagen de otro registro se rechaza        - `latest` y una imagen sin etiqueta se rechazan
#   - una imagen del registro propio con etiqueta se admite
#   - fuera de un namespace de cliente la política no interviene
# Uso:  KUBECONFIG=... [SITIO=colegio] bash gitops/pruebas/admision.sh
set -uo pipefail
SITIO="${SITIO:-colegio}"
NS="cliente-${SITIO}"
fallos=0
ok()    { echo "   OK   $1"; }
falla() { echo "   FALLA $1"; fallos=$((fallos+1)); }

pod() { # namespace imagen
  cat <<YAML
apiVersion: v1
kind: Pod
metadata: { name: prueba-admision, namespace: $1 }
spec:
  securityContext: { runAsNonRoot: true, runAsUser: 10001, seccompProfile: { type: RuntimeDefault } }
  containers:
    - name: c
      image: $2
      securityContext: { allowPrivilegeEscalation: false, capabilities: { drop: [ALL] } }
      resources: { requests: { cpu: 5m, memory: 8Mi }, limits: { cpu: 10m, memory: 16Mi } }   # la cuota del plan exige límites
YAML
}
intentar() { pod "$1" "$2" | kubectl apply --dry-run=server -f - 2>&1; }

kubectl get validatingadmissionpolicybinding imagenes-de-clientes >/dev/null 2>&1 || { echo "La política no está aplicada: kubectl apply -f gitops/platform/politicas/"; exit 1; }
kubectl get ns "$NS" >/dev/null 2>&1 || { echo "No existe ${NS}"; exit 1; }

salida="$(intentar "$NS" docker.io/library/nginx:1.27)"
echo "$salida" | grep -q "solo gitea.hub.local/forja-digital" && ok "una imagen de Docker Hub se rechaza" || falla "no se rechazó una imagen ajena: $salida"
salida="$(intentar "$NS" gitea.hub.local/forja-digital/${SITIO}-web:latest)"
echo "$salida" | grep -q "latest" && ok "«latest» se rechaza" || falla "no se rechazó latest: $salida"
salida="$(intentar "$NS" gitea.hub.local/forja-digital/${SITIO}-web)"
echo "$salida" | grep -q "etiqueta o un digest" && ok "una imagen sin etiqueta se rechaza" || falla "no se rechazó una imagen sin etiqueta: $salida"
salida="$(intentar "$NS" gitea.hub.local/forja-digital/${SITIO}-web:v1)"
echo "$salida" | grep -q "created (server dry run)" && ok "una imagen del registro propio con etiqueta se admite" || falla "se rechazó una imagen válida: $salida"
salida="$(intentar default docker.io/library/nginx:1.27)"
echo "$salida" | grep -q "created (server dry run)" && ok "fuera de un namespace de cliente no interviene" || falla "la política afectó a otro namespace: $salida"
echo
[ "$fallos" -eq 0 ] && echo "Admisión: la política se comporta como se espera." || { echo "${fallos} comprobación(es) fallaron."; exit 1; }

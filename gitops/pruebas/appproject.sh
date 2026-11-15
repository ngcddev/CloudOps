#!/usr/bin/env bash
# Prueba del AppProject `clientes` y del menor privilegio (spec 017, T06):
#   1. los Pods de los clientes no tienen el token de la API de Kubernetes montado
#   2. una Application del proyecto `clientes` que apunta a una carpeta con un ClusterRole (observability/alloy) es RECHAZADA por el proyecto
#      («resource ... is not permitted in project clientes») y no crea nada
#   3. una Application del proyecto que quiere desplegar en kube-system es rechazada por el destino
# La Application de prueba se borra al terminar (también si se interrumpe). No toca ningún cliente.
# Uso:  KUBECONFIG=... bash gitops/pruebas/appproject.sh
set -uo pipefail
fallos=0
ok()    { echo "   OK   $1"; }
falla() { echo "   FALLA $1"; fallos=$((fallos+1)); }
borrar() { kubectl -n argocd delete application prueba-appproject --ignore-not-found --wait=false >/dev/null 2>&1; kubectl -n argocd patch application prueba-appproject --type=merge -p '{"metadata":{"finalizers":null}}' >/dev/null 2>&1; }
trap borrar EXIT

kubectl -n argocd get appproject clientes >/dev/null 2>&1 || { echo "No existe el AppProject clientes: kubectl apply -k gitops/platform/argocd/applications"; exit 1; }

echo "== 1. Sin token de la API en los Pods de los clientes"
for ns in cliente-restaurante cliente-ferreteria cliente-consultorio; do
  for _ in $(seq 1 30); do kubectl -n "$ns" get pods --no-headers 2>/dev/null | grep -q Terminating || break; sleep 2; done   # un cambio reciente deja Pods viejos terminando
  pods="$(kubectl -n "$ns" get pods -o name 2>/dev/null)"
  [ -n "$pods" ] || { falla "${ns} no tiene Pods"; continue; }
  montados=0
  for pod in $pods; do
    if MSYS_NO_PATHCONV=1 kubectl -n "$ns" exec "$pod" -- ls /var/run/secrets/kubernetes.io/serviceaccount >/dev/null 2>&1; then montados=$((montados+1)); fi
  done
  [ "$montados" = 0 ] && ok "${ns}: ningún Pod tiene el token montado" || falla "${ns}: ${montados} Pod(s) con el token de la API montado"
done

crear() { # ruta namespace-destino
  borrar; sleep 2
  kubectl apply -f - >/dev/null <<YAML
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: prueba-appproject
  namespace: argocd
spec:
  project: clientes
  source:
    repoURL: http://gitea.gitea.svc:3000/forja-digital/hub-gitops.git
    targetRevision: main
    path: $1
  destination:
    server: https://kubernetes.default.svc
    namespace: $2
YAML
}
condiciones() { for _ in $(seq 1 30); do c="$(kubectl -n argocd get application prueba-appproject -o jsonpath='{range .status.conditions[*]}{.message}{"\n"}{end}' 2>/dev/null)"; [ -n "$c" ] && break; sleep 2; done; echo "$c"; }

echo "== 2. Un ClusterRole en la carpeta de un cliente se rechaza"
crear observability/alloy cliente-prueba
sleep 5
kubectl -n argocd patch application prueba-appproject --type=merge -p '{"operation":{"sync":{}}}' >/dev/null 2>&1
# El motivo de cada recurso rechazado está en el resultado de la sincronización: «resource <grupo>:<tipo> is not permitted in project clientes»
detalle=""
for _ in $(seq 1 30); do
  detalle="$(kubectl -n argocd get application prueba-appproject -o jsonpath='{range .status.operationState.syncResult.resources[*]}{.kind}{": "}{.message}{" || "}{end}' 2>/dev/null)"
  echo "$detalle" | grep -q "ClusterRole" && break
  sleep 2
done
echo "$detalle" | grep -q "ClusterRole: resource .*ClusterRole is not permitted in project clientes" && ok "el proyecto rechazó el ClusterRole y el resto de lo ajeno: $(echo "$detalle" | grep -o "ClusterRole: resource [^|]*" | head -1 | cut -c1-130)" || falla "el proyecto no rechazó el ClusterRole: ${detalle:-sin detalle}"
[ "$(kubectl -n argocd get application prueba-appproject -o jsonpath='{.status.operationState.phase}' 2>/dev/null)" = "Failed" ] && ok "la sincronización terminó en Failed: no se aplicó nada"
[ -z "$(kubectl get daemonset -n cliente-prueba alloy 2>/dev/null)" ] && ok "no se creó nada en el destino de la prueba"

echo "== 3. Desplegar en kube-system se rechaza"
crear clients/_base kube-system
msg="$(condiciones)"
echo "$msg" | grep -qi "destination\|not permitted" && ok "el destino se rechazó: $(echo "$msg" | head -1 | cut -c1-150)" || falla "kube-system no se rechazó: ${msg:-sin condición}"

echo
[ "$fallos" -eq 0 ] && echo "AppProject: los clientes no pueden salirse de sus namespaces ni crear permisos." || { echo "${fallos} comprobación(es) fallaron."; exit 1; }

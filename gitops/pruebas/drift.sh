#!/usr/bin/env bash
# Prueba de drift con selfHeal (spec 017, T01): alguien cambia el clúster a mano y Argo CD lo devuelve a lo que dice Git, sin que nadie toque Git.
#   1. escala a mano el Deployment `web` del sitio a 3 réplicas   → Argo CD lo marca OutOfSync y lo devuelve a las réplicas de Git
#   2. borra a mano el Ingress del sitio                           → Argo CD lo recrea y el sitio vuelve a responder
# Mide cuántos segundos tarda cada corrección y comprueba que la Application termina Synced/Healthy.
# Uso:  KUBECONFIG=... [SITIO=restaurante] bash gitops/pruebas/drift.sh
# No cambia nada en Git ni deja nada cambiado: lo que deshace es Argo CD. Si selfHeal estuviera apagado, la prueba lo dice y falla.
set -uo pipefail

SITIO="${SITIO:-restaurante}"
NS="cliente-${SITIO}"
APP="$NS"
LIMITE="${LIMITE:-180}"   # Argo CD revisa cada 30 s, pero recrear un recurso borrado ha tardado entre 55 y ~100 s
fallos=0
ok()    { echo "   OK   $1"; }
falla() { echo "   FALLA $1"; fallos=$((fallos+1)); }
sync_estado() { kubectl -n argocd get application "$APP" -o jsonpath='{.status.sync.status}/{.status.health.status}' 2>/dev/null; }

kubectl -n argocd get application "$APP" >/dev/null 2>&1 || { echo "No existe la Application ${APP} en Argo CD."; exit 1; }
[ "$(kubectl -n argocd get application "$APP" -o jsonpath='{.spec.syncPolicy.automated.selfHeal}')" = "true" ] \
  && ok "la Application ${APP} tiene selfHeal activo" || { falla "selfHeal no está activo en ${APP}"; exit 1; }
for _ in $(seq 1 30); do [ "$(sync_estado)" = "Synced/Healthy" ] && break; sleep 2; done
[ "$(sync_estado)" = "Synced/Healthy" ] && ok "parte de Synced/Healthy" || { falla "no parte en Synced/Healthy: $(sync_estado)"; exit 1; }

echo "== Drift 1: escalar a mano el Deployment web"
deseadas="$(kubectl -n "$NS" get deploy web -o jsonpath='{.spec.replicas}')"
inicio=$(date +%s)
kubectl -n "$NS" scale deploy/web --replicas=3 >/dev/null
echo "   a mano: web ${deseadas} → 3 réplicas (Git dice ${deseadas})"
visto_fuera=0; corregido=0
for _ in $(seq 1 "$LIMITE"); do
  estado="$(sync_estado)"
  case "$estado" in OutOfSync/*) visto_fuera=1 ;; esac
  if [ "$(kubectl -n "$NS" get deploy web -o jsonpath='{.spec.replicas}')" = "$deseadas" ]; then corregido=1; break; fi
  sleep 1
done
seg=$(( $(date +%s) - inicio ))
[ "$corregido" = 1 ] && ok "Argo CD devolvió web a ${deseadas} réplica(s) a los ${seg} s" || falla "Argo CD no corrigió el drift en ${LIMITE} s"
[ "$visto_fuera" = 1 ] && ok "la Application se vio OutOfSync mientras duró el drift" || echo "   (no alcancé a ver OutOfSync: la corrección fue más rápida que el sondeo de 1 s)"

echo "== Drift 2: borrar a mano el Ingress del sitio"
inicio=$(date +%s)
kubectl -n "$NS" delete ingress web >/dev/null
echo "   a mano: Ingress web borrado"
recreado=0
for _ in $(seq 1 "$LIMITE"); do
  kubectl -n "$NS" get ingress web >/dev/null 2>&1 && { recreado=1; break; }
  sleep 1
done
seg=$(( $(date +%s) - inicio ))
[ "$recreado" = 1 ] && ok "Argo CD recreó el Ingress a los ${seg} s" || falla "el Ingress no volvió en ${LIMITE} s"

echo "== Resultado"
for _ in $(seq 1 60); do [ "$(sync_estado)" = "Synced/Healthy" ] && break; sleep 2; done
[ "$(sync_estado)" = "Synced/Healthy" ] && ok "la Application terminó Synced/Healthy" || falla "terminó en $(sync_estado)"
[ "$(kubectl -n "$NS" get deploy web -o jsonpath='{.spec.replicas}')" = "$deseadas" ] && ok "el clúster quedó como dice Git" || falla "el clúster no quedó como dice Git"
echo
[ "$fallos" -eq 0 ] && echo "Drift: Git manda; Argo CD corrige lo que se cambie a mano." || { echo "${fallos} comprobación(es) fallaron."; exit 1; }

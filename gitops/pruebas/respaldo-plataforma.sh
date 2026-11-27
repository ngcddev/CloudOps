#!/usr/bin/env bash
# Respaldo de la plataforma fuera del nodo y prueba de que sirve (spec 016): lanza los CronJob de Gitea y Argo CD, copia lo que dejaron a una carpeta
# del equipo y comprueba el contenido: el dump de Gitea trae el repositorio hub-gitops y se puede clonar de él; el de Argo CD trae las Applications.
# Uso:  KUBECONFIG=... [DESTINO=./respaldos-plataforma] bash gitops/pruebas/respaldo-plataforma.sh
set -uo pipefail
DESTINO="${DESTINO:-./respaldos-plataforma}"
fallos=0
ok()    { echo "   OK   $1"; }
falla() { echo "   FALLA $1"; fallos=$((fallos+1)); }
mkdir -p "$DESTINO"

correr() { # namespace cronjob
  local ns="$1" cron="$2" job="manual-$(date +%s)"
  kubectl -n "$ns" create job --from="cronjob/${cron}" "$job" >/dev/null || return 1
  kubectl -n "$ns" wait --for=condition=complete "job/${job}" --timeout=180s >/dev/null 2>&1 \
    && ok "${cron}: $(kubectl -n "$ns" logs "job/${job}" 2>/dev/null | tail -1)" || falla "${cron} no terminó"
  kubectl -n "$ns" delete "job/${job}" --wait=false >/dev/null 2>&1
}

copiar() { # namespace pvc carpeta-local
  local ns="$1" pvc="$2" salida="$3" pod="lector-$(date +%s)"
  mkdir -p "$salida"
  kubectl -n "$ns" run "$pod" --image=busybox:1.36 --restart=Never --overrides="{\"spec\":{\"securityContext\":{\"runAsNonRoot\":true,\"runAsUser\":1000,\"seccompProfile\":{\"type\":\"RuntimeDefault\"}},\"containers\":[{\"name\":\"lector\",\"image\":\"busybox:1.36\",\"command\":[\"sleep\",\"120\"],\"securityContext\":{\"allowPrivilegeEscalation\":false,\"capabilities\":{\"drop\":[\"ALL\"]}},\"volumeMounts\":[{\"name\":\"r\",\"mountPath\":\"/respaldos\",\"readOnly\":true}]}],\"volumes\":[{\"name\":\"r\",\"persistentVolumeClaim\":{\"claimName\":\"${pvc}\"}}]}}" >/dev/null
  kubectl -n "$ns" wait --for=condition=Ready "pod/${pod}" --timeout=90s >/dev/null 2>&1
  MSYS_NO_PATHCONV=1 kubectl -n "$ns" exec "$pod" -- tar cf - -C /respaldos . 2>/dev/null | tar xf - -C "$salida"
  kubectl -n "$ns" delete pod "$pod" --wait=false >/dev/null 2>&1
}

echo "== Lanzando los respaldos"
correr gitea gitea-respaldo
correr argocd argocd-respaldo

echo "== Copiando fuera del nodo a ${DESTINO}"
copiar gitea gitea-respaldos "$DESTINO/gitea"
copiar argocd argocd-respaldos "$DESTINO/argocd"
gitea_dump="$(ls -t "$DESTINO"/gitea/gitea-*.tar.gz 2>/dev/null | head -1)"
argo_yaml="$(ls -t "$DESTINO"/argocd/argocd-*.yaml 2>/dev/null | head -1)"
[ -n "$gitea_dump" ] && ok "dump de Gitea: $(basename "$gitea_dump") ($(du -h "$gitea_dump" | cut -f1))" || falla "no se copió el dump de Gitea"
[ -n "$argo_yaml" ] && ok "configuración de Argo CD: $(basename "$argo_yaml")" || falla "no se copió la configuración de Argo CD"

echo "== Comprobando el contenido"
if [ -n "$gitea_dump" ]; then
  tmp="$(mktemp -d)"; tar xzf "$gitea_dump" -C "$tmp" 2>/dev/null
  [ -f "$tmp/gitea-db.sql" ] && ok "el dump trae la base de Gitea (usuarios y tokens)" || falla "el dump no trae la base"
  repo="$(find "$tmp" -type d -name 'hub-gitops.git' | head -1)"
  if [ -n "$repo" ]; then
    git clone -q "$repo" "$tmp/clon" 2>/dev/null && [ -f "$tmp/clon/clients/restaurante/kustomization.yaml" ] \
      && ok "se puede clonar hub-gitops desde el respaldo y trae clients/restaurante ($(git -C "$tmp/clon" rev-list --count HEAD) commits)" || falla "no se pudo clonar hub-gitops del respaldo"
  else
    falla "el dump no trae hub-gitops"
  fi
  rm -rf "$tmp"
fi
[ -n "$argo_yaml" ] && grep -q "name: cliente-restaurante" "$argo_yaml" && grep -q "kind: ApplicationSet" "$argo_yaml" \
  && ok "la configuración de Argo CD trae las Applications y el ApplicationSet" || falla "la configuración de Argo CD está incompleta"
echo
[ "$fallos" -eq 0 ] && echo "Respaldo de la plataforma: sirve y quedó fuera del nodo en ${DESTINO}." || { echo "${fallos} comprobación(es) fallaron."; exit 1; }

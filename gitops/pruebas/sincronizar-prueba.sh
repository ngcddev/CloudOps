#!/usr/bin/env bash
# Prueba el sincronizador de hub-gitops (spec 022) con repositorios locales, sin Gitea ni clúster: un «hub-gitops» y un «origin» de mentira (repos desnudos en una carpeta temporal) y un
# repositorio principal de mentira. Comprueba los dueños (no pisa la versión ni el catálogo que escribe el Hub), --simular, --comprobar, --limpiar y las precondiciones.
# Uso: bash gitops/pruebas/sincronizar-prueba.sh
set -uo pipefail
AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$AQUI/../sincronizar-hub-gitops.sh"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
fallos=0
ok()    { echo "   OK   $1"; }
falla() { echo "   FALLA $1"; fallos=$((fallos+1)); }
git_() { git -c user.name=Prueba -c user.email=prueba@forja.test -c init.defaultBranch=main "$@"; }
escribir() { mkdir -p "$(dirname "$1")"; printf '%s\n' "$2" > "$1"; }
en_hub() { git_ -C "$T/hub-lectura" pull -q origin main >/dev/null 2>&1; cat "$T/hub-lectura/$1" 2>/dev/null; }

# ---------- hub-gitops de mentira (lo que ya está desplegado y lo que escribe el Hub) ----------
git_ init -q --bare "$T/hub-gitops.git" && git_ clone -q "$T/hub-gitops.git" "$T/hub-semilla" 2>/dev/null
S="$T/hub-semilla"
escribir "$S/clients/_base/deployment.yaml" "base vieja"
escribir "$S/clients/ferreteria/kustomization.yaml" "newTag: v1.1   # lo escribió el Hub"
escribir "$S/clients/ferreteria/catalog-info.yaml" "catálogo del Hub"
escribir "$S/clients/ferreteria/extra.yaml" "extra viejo"
escribir "$S/clients/consultorio/kustomization.yaml" "newTag: v1"
escribir "$S/clients/consultorio/backend.yaml" "backend viejo"
escribir "$S/observability/prom.yml" "prometheus viejo"
escribir "$S/hub/api.yaml" "api vieja"
escribir "$S/platform/backstage/group.yaml" "grupo viejo"
escribir "$S/platform/argocd/x.yaml" "copia sin uso"
(cd "$S" && git_ add -A && git_ commit -q -m semilla && git_ push -q origin HEAD:main)
git_ clone -q "$T/hub-gitops.git" "$T/hub-lectura" 2>/dev/null

# ---------- repositorio principal de mentira, con un origin que tiene la rama dev ----------
git_ init -q --bare "$T/origin.git"
git_ init -q "$T/mono" && M="$T/mono"
escribir "$M/gitops/clients/_base/deployment.yaml" "base NUEVA con solo lectura"
escribir "$M/gitops/clients/ferreteria/kustomization.yaml" "newTag: v1   # versión del repositorio principal: NO debe pisar la del Hub"
escribir "$M/gitops/clients/ferreteria/catalog-info.yaml" "catálogo del repositorio principal"
escribir "$M/gitops/clients/ferreteria/extra.yaml" "extra NUEVO"
escribir "$M/gitops/clients/consultorio/kustomization.yaml" "newTag: v0"
escribir "$M/gitops/clients/consultorio/backend.yaml" "backend NUEVO con solo lectura"
escribir "$M/gitops/clients/nuevo/kustomization.yaml" "cliente que el Hub aún no dio de alta"
escribir "$M/observability/prom.yml" "prometheus NUEVO"
escribir "$M/gitops/hub/api.yaml" "api NUEVA"
escribir "$M/gitops/platform/backstage/group.yaml" "grupo NUEVO"
escribir "$M/gitops/platform/argocd/x.yaml" "esto no se copia"
(cd "$M" && git_ add -A && git_ commit -q -m principal && git_ remote add origin "$T/origin.git" && git_ push -q origin HEAD:dev && git_ fetch -q origin)
export REMOTO="$T/hub-gitops.git" RAIZ="$M"
sincronizar() { bash "$SCRIPT" "$@" 2>&1; }

echo "== --simular: muestra los cambios y no sube nada"
antes="$(git_ -C "$T/hub-gitops.git" rev-parse main)"
salida="$(sincronizar --simular)"; codigo=$?
despues="$(git_ -C "$T/hub-gitops.git" rev-parse main)"
[ "$codigo" = 0 ] && [ "$antes" = "$despues" ] && ok "--simular no subió nada (código 0)" || falla "--simular cambió hub-gitops (código ${codigo})"
echo "$salida" | grep -q "deployment.yaml" && ok "muestra los archivos que cambiarían" || falla "no mostró los cambios"

echo "== --comprobar antes de sincronizar: hay diferencias (código 1)"
sincronizar --comprobar >/dev/null; [ "$?" = 1 ] && ok "detecta que hub-gitops no está en sincronía" || falla "no detectó la diferencia"

echo "== sincronizar de verdad"
salida="$(sincronizar)"; codigo=$?
[ "$codigo" = 0 ] && ok "terminó bien" || { falla "falló (código ${codigo})"; echo "$salida" | tail -5; }
[ "$(en_hub clients/_base/deployment.yaml)" = "base NUEVA con solo lectura" ] && ok "la base del equipo se promovió" || falla "la base no se promovió"
[ "$(en_hub clients/consultorio/backend.yaml)" = "backend NUEVO con solo lectura" ] && ok "el backend del cliente (del equipo) se promovió" || falla "el backend no se promovió"
[ "$(en_hub clients/ferreteria/extra.yaml)" = "extra NUEVO" ] && ok "los demás archivos del cliente se promovieron" || falla "el extra no se promovió"
en_hub clients/ferreteria/kustomization.yaml | grep -q "v1.1.*lo escribió el Hub" && ok "NO pisó la versión que escribió el Hub (kustomization.yaml)" || falla "pisó la versión del Hub"
[ "$(en_hub clients/ferreteria/catalog-info.yaml)" = "catálogo del Hub" ] && ok "NO pisó el catalogo que escribe el Hub" || falla "pisó el catálogo del Hub"
en_hub clients/consultorio/kustomization.yaml | grep -q "newTag: v1$" && ok "la versión de otro cliente tampoco se tocó" || falla "tocó otra versión"
[ ! -e "$T/hub-lectura/clients/nuevo" ] && ok "un cliente que el Hub no creó se omite" || falla "creó un cliente que no existe en hub-gitops"
[ "$(en_hub observability/prom.yml)" = "prometheus NUEVO" ] && [ "$(en_hub hub/api.yaml)" = "api NUEVA" ] && [ "$(en_hub platform/backstage/group.yaml)" = "grupo NUEVO" ] && ok "observability, hub y backstage se promovieron" || falla "faltan observability, hub o backstage"
[ "$(en_hub platform/argocd/x.yaml)" = "copia sin uso" ] && ok "sin --limpiar no se retira la copia de platform/argocd" || falla "retiró platform/argocd sin pedirlo"
git_ -C "$T/hub-lectura" log -1 --format=%s | grep -q "sincronizar desde el repositorio principal ($(git_ -C "$M" rev-parse --short HEAD)" && ok "el commit dice de qué commit salió" || falla "el commit no dice el origen"

echo "== --comprobar después: en sincronía (código 0)"
sincronizar --comprobar >/dev/null; [ "$?" = 0 ] && ok "en sincronía" || falla "sigue diciendo que hay diferencias"
echo "== un cambio a mano en hub-gitops en un archivo del equipo se detecta"
(cd "$T/hub-lectura" && echo "a mano" >> observability/prom.yml && git_ commit -qam "cambio a mano" && git_ push -q origin HEAD:main)
sincronizar --comprobar >/dev/null; [ "$?" = 1 ] && ok "detecta el cambio a mano" || falla "no detectó el cambio a mano"
sincronizar >/dev/null; sincronizar --comprobar >/dev/null; [ "$?" = 0 ] && ok "sincronizar lo corrige" || falla "no se corrigió"

echo "== --limpiar retira las copias sin uso"
sincronizar --limpiar >/dev/null
[ ! -e "$(git_ -C "$T/hub-lectura" pull -q origin main >/dev/null 2>&1; echo "$T/hub-lectura/platform/argocd")" ] && ok "platform/argocd retirado" || falla "platform/argocd sigue"
[ -e "$T/hub-lectura/platform/backstage/group.yaml" ] && ok "platform/backstage se conserva" || falla "se borró platform/backstage"

echo "== precondiciones"
echo "sin guardar" >> "$M/observability/prom.yml"
sincronizar >/dev/null; [ "$?" = 3 ] && ok "rechaza un árbol con cambios sin guardar (código 3)" || falla "aceptó un árbol sucio"
sincronizar --comprobar >/dev/null; [ "$?" != 3 ] && ok "--comprobar sí funciona con el árbol sucio" || falla "--comprobar exigió árbol limpio"
(cd "$M" && git_ checkout -q -- observability/prom.yml)
(cd "$M" && echo "local" >> observability/prom.yml && git_ commit -qam "commit local sin mezclar")
salida="$(sincronizar)"; codigo=$?
[ "$codigo" = 3 ] && echo "$salida" | grep -q "mézclalo" && ok "rechaza un commit que no está en origin/dev ni origin/main (código 3)" || falla "aceptó un commit sin mezclar (código ${codigo})"
salida="$(sincronizar --forzar)"; echo "$salida" | grep -q "AVISO" && ok "--forzar lo permite y lo avisa" || falla "--forzar no avisó"

echo
[ "$fallos" -eq 0 ] && echo "Sincronizador de hub-gitops: todo OK" || { echo "${fallos} comprobación(es) fallaron"; exit 1; }

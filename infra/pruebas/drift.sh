#!/usr/bin/env bash
# Prueba el drift de OpenTofu (spec 019, T06): lo que alguien cambia a mano fuera de la configuración se detecta con `plan -detailed-exitcode`
# (0 = sin cambios, 2 = hay diferencias) y un `apply` lo devuelve a lo declarado.
#   1. aplica una configuración mínima (un archivo administrado con el proveedor `local`) y comprueba que el plan queda en 0 (idempotente)
#   2. cambia el archivo a mano y comprueba que el plan sale con 2 y nombra el recurso
#   3. aplica de nuevo: el archivo vuelve a lo declarado y el plan queda otra vez en 0
# No toca el clúster, Gitea ni el estado real: trabaja en una carpeta temporal dentro de infra/pruebas/ (ignorada por Git) y la borra al terminar.
# Para el entorno real el mismo criterio es:  GITEA_TOKEN=... infra/tofu.sh tofu plan -detailed-exitcode   (el código 2 es drift y se revisa antes de aplicar).
# Uso: bash infra/pruebas/drift.sh
set -uo pipefail
export MSYS_NO_PATHCONV=1
AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOFU_IMAGE="${TOFU_IMAGE:-ghcr.io/opentofu/opentofu:1.13.2}"
TMP="$AQUI/.drift"
fallos=0
ok()    { echo "   OK   $1"; }
falla() { echo "   FALLA $1"; fallos=$((fallos+1)); }
limpiar() { rm -rf "$TMP"; }
trap limpiar EXIT

rm -rf "$TMP"; mkdir -p "$TMP/salida"
cat > "$TMP/main.tf" <<'HCL'
terraform {
  required_providers {
    local = { source = "hashicorp/local", version = "2.5.2" }
  }
}

resource "local_file" "config" {
  filename = "/w/salida/config.txt"
  content  = "replicas = 1\n"
}
HCL
RUTA="$(cd "$TMP" && (pwd -W 2>/dev/null || pwd))"
tofu() { docker run --rm -v "${RUTA}:/w" -w /w "$TOFU_IMAGE" "$@"; }

echo "== Preparación"
tofu init -input=false >/dev/null 2>&1 && ok "tofu init" || { falla "tofu init no funcionó (¿sin red para bajar el proveedor?)"; exit 1; }
tofu apply -input=false -auto-approve >/dev/null 2>&1 && ok "apply inicial" || { falla "el apply inicial falló"; exit 1; }

echo "== Sin drift: el plan queda en 0"
tofu plan -input=false -detailed-exitcode >/dev/null 2>&1; codigo=$?
[ "$codigo" = 0 ] && ok "plan sin cambios (código 0): la configuración es idempotente" || falla "el plan salió con código ${codigo}"

echo "== Cambio a mano: el plan sale con 2"
printf 'replicas = 5\n' > "$TMP/salida/config.txt"
salida="$(tofu plan -input=false -detailed-exitcode -no-color 2>&1)"; codigo=$?
[ "$codigo" = 2 ] && ok "el plan detectó el drift (código 2)" || falla "el plan no detectó el cambio a mano (código ${codigo})"
echo "$salida" | grep -q "local_file.config" && ok "el plan nombra el recurso que cambió (local_file.config)" || falla "el plan no nombra el recurso"

echo "== Reconciliar: apply devuelve lo declarado"
tofu apply -input=false -auto-approve >/dev/null 2>&1
[ "$(tr -d '\r' < "$TMP/salida/config.txt")" = "replicas = 1" ] && ok "el archivo volvió a «replicas = 1»" || falla "el archivo no volvió a lo declarado"
tofu plan -input=false -detailed-exitcode >/dev/null 2>&1; codigo=$?
[ "$codigo" = 0 ] && ok "el plan vuelve a 0" || falla "el plan salió con código ${codigo} tras reconciliar"

echo
[ "$fallos" -eq 0 ] && echo "Drift de OpenTofu: se detecta y se corrige." || { echo "${fallos} comprobación(es) fallaron."; exit 1; }

#!/usr/bin/env bash
# Ejecuta UN comando de verificación y guarda todo lo que sirve de evidencia (spec 023): el comando, la salida completa, el código de salida, la hora UTC, la duración y el commit.
# Los valores de .env y .env.cluster que parecen secretos (PASSWORD, TOKEN, SECRET, KEY) se tapan en el registro antes de guardarlo.
# Uso:  bash entrega/evidencias/paso.sh <carpeta-de-la-corrida> <nivel> <id> <descripción> -- <comando...>
# Escribe <carpeta>/<nivel>/<id>.log y agrega una fila a <carpeta>/resultados.tsv (id, nivel, estado, código, segundos, inicio UTC, descripción, comando).
# Estado: PASO (código 0) · FALLO (otro código) · SALTADO (el comando dijo que se salta con el código 77).
set -u
carpeta=$1; nivel=$2; id=$3; descripcion=$4; shift 4
[ "${1:-}" = "--" ] && shift
# CORRER_SOLO="A01 A02": repite solo los pasos cuyo id empieza por alguno de esos prefijos (los demás se saltan sin dejar rastro)
if [ -n "${CORRER_SOLO:-}" ]; then
  coincide=0; for pref in $CORRER_SOLO; do case "$id" in "$pref"*) coincide=1;; esac; done
  [ "$coincide" -eq 1 ] || exit 0
fi
mkdir -p "$carpeta/$nivel"
log="$carpeta/$nivel/$id.log"
raiz=$(git rev-parse --show-toplevel)

# Script de sed que tapa los valores secretos conocidos (solo los de 6 caracteres o más)
filtro=$(mktemp)
for archivo in "$raiz/.env" "$raiz/.env.cluster"; do
  [ -f "$archivo" ] || continue
  grep -E '^[A-Za-z_]*(PASSWORD|TOKEN|SECRET|KEY)[A-Za-z_]*=' "$archivo" | while IFS='=' read -r k v; do
    v=${v%\"}; v=${v#\"}; [ ${#v} -ge 6 ] || continue
    printf 's|%s|[SECRETO]|g\n' "$(printf '%s' "$v" | sed -e 's/[][\.*^$|/&]/\&/g')"
  done >> "$filtro"
done

# Secretos extra que el que llama no quiere ver en los registros (uno por línea), por ejemplo la contraseña sembrada que sale de un Secret del clúster
if [ -n "${PASO_SECRETOS_EXTRA:-}" ]; then
  printf '%s
' "$PASO_SECRETOS_EXTRA" | while IFS= read -r v; do
    [ ${#v} -ge 6 ] || continue
    printf 's|%s|[SECRETO]|g
' "$(printf '%s' "$v" | sed -e 's/[][\.*^$|/&]/\&/g')"
  done >> "$filtro"
fi

inicio=$(date -u +%Y-%m-%dT%H:%M:%SZ); t0=$(date +%s)
{
  echo "# paso:     $id ($nivel)"
  echo "# qué:      $descripcion"
  echo "# comando:  $*"
  echo "# inicio:   $inicio"
  echo "# commit:   $(git -C "$raiz" rev-parse --short HEAD)$(git -C "$raiz" diff --quiet HEAD -- backend ai gitops observability pipelines infra frontend voz || echo ' +cambios locales')"
  echo "# ---------------------------------------------------------------"
} > "$log"
( cd "$raiz" && "$@" ) 2>&1 | sed -f "$filtro" >> "$log"
codigo=${PIPESTATUS[0]}
seg=$(( $(date +%s) - t0 ))
rm -f "$filtro"
if [ "$codigo" -eq 0 ]; then estado=PASO; elif [ "$codigo" -eq 77 ]; then estado=SALTADO; else estado=FALLO; fi
{ echo "# ---------------------------------------------------------------"; echo "# código de salida: $codigo · estado: $estado · duración: ${seg}s"; } >> "$log"
printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$id" "$nivel" "$estado" "$codigo" "$seg" "$inicio" "$descripcion" "$*" >> "$carpeta/resultados.tsv"
echo "[$estado] $nivel/$id (${seg}s) — $descripcion"

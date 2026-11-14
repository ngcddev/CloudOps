#!/bin/sh
# Respaldo de la base del Hub (spec 003, RNF de recuperación): un pg_dump en formato custom, verificado con pg_restore --list,
# y rotación de los últimos N. Lo corre el CronJob hub-db-backup (gitops/hub/backup.yaml) y también sirve a mano o en Docker.
# La conexión sale de las variables estándar de PostgreSQL (PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE); nunca van en el repo.
# Uso: PGDATABASE=hub RESPALDO_DIR=/respaldos RESPALDO_CONSERVAR=7 sh respaldar.sh
set -eu

DESTINO="${RESPALDO_DIR:-/respaldos}"
CONSERVAR="${RESPALDO_CONSERVAR:-7}"
: "${PGDATABASE:?Falta PGDATABASE}"

# Espera a la base (hasta 60 s): un Pod recién creado puede tardar unos segundos en quedar permitido por la NetworkPolicy del namespace
# y, sin esta espera, el primer intento fallaba con «Connection refused» aunque PostgreSQL estuviera sano (se vio en k3s)
for _ in $(seq 1 30); do pg_isready -q && break; sleep 2; done
pg_isready -q || { echo "La base no responde en ${PGHOST:-el socket local}: no se hizo nada." >&2; exit 1; }

mkdir -p "$DESTINO"
ARCHIVO="$DESTINO/${PGDATABASE}-$(date -u +%Y%m%dT%H%M%SZ).dump"
# Si algo falla, no queda un archivo a medias que parezca un respaldo
trap 'rm -f "$ARCHIVO.parcial"' EXIT

pg_dump --format=custom --no-owner --file="$ARCHIVO.parcial"
# Un respaldo que no se puede leer no sirve: se comprueba antes de aceptarlo
pg_restore --list "$ARCHIVO.parcial" > /dev/null
mv "$ARCHIVO.parcial" "$ARCHIVO"
echo "Respaldo creado: $ARCHIVO ($(wc -c < "$ARCHIVO") bytes)"

# Rotación: se conservan los N más recientes
ls -1t "$DESTINO"/"${PGDATABASE}"-*.dump 2>/dev/null | tail -n +"$((CONSERVAR + 1))" | while read -r viejo; do
  rm -f "$viejo"
  echo "Respaldo antiguo eliminado: $viejo"
done

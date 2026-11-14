#!/bin/sh
# Restaura un respaldo del Hub (hecho con respaldar.sh) en una base NUEVA, sin tocar la del Hub, y cuenta sus tablas.
# Sirve para probar un respaldo o para recuperar datos puntuales. Para reemplazar la base viva, ver runbooks/ (hay que
# detener la API antes). La conexión sale de PGHOST, PGPORT, PGUSER y PGPASSWORD; el usuario debe poder crear bases.
# Uso: sh restaurar.sh <archivo.dump> [base_destino]        (por defecto hub_restaurada)
#      REEMPLAZAR=1 sh restaurar.sh <archivo.dump> hub_restaurada   (borra la base de destino si ya existe)
set -eu

ARCHIVO="${1:?Uso: restaurar.sh <archivo.dump> [base_destino]}"
BASE="${2:-hub_restaurada}"
[ -f "$ARCHIVO" ] || { echo "No existe el respaldo $ARCHIVO" >&2; exit 1; }
# El nombre se usa dentro de SQL: solo letras, números y guion bajo
case "$BASE" in *[!a-zA-Z0-9_]*|"") echo "Nombre de base no válido: $BASE" >&2; exit 1 ;; esac

# Espera a la base (hasta 60 s): un Pod recién creado puede tardar unos segundos en quedar permitido por la NetworkPolicy del namespace
# y, sin esta espera, el primer intento fallaba con «Connection refused» aunque PostgreSQL estuviera sano (se vio en k3s)
for _ in $(seq 1 30); do pg_isready -q && break; sleep 2; done
pg_isready -q || { echo "La base no responde en ${PGHOST:-el socket local}: no se hizo nada." >&2; exit 1; }

existe="$(psql -d postgres -tAc "select 1 from pg_database where datname = '$BASE'")"
if [ -n "$existe" ]; then
  [ "${REEMPLAZAR:-0}" = "1" ] || { echo "La base $BASE ya existe; usa REEMPLAZAR=1 o elige otro nombre." >&2; exit 1; }
  dropdb --if-exists "$BASE"
fi
createdb "$BASE"
pg_restore --no-owner --exit-on-error --dbname="$BASE" "$ARCHIVO"
tablas="$(psql -d "$BASE" -tAc "select count(*) from information_schema.tables where table_schema = 'public'")"
echo "Restaurado en la base $BASE: $tablas tablas"

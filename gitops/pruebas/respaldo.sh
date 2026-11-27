#!/usr/bin/env bash
# Prueba el respaldo y la restauración de la base del Hub (runbook de recuperación): respalda con respaldar.sh, restaura en una
# base nueva con restaurar.sh y compara tabla por tabla el número de filas con la original. Usa la base del docker compose
# (`docker compose up -d db`); no toca la base `hub`: solo la lee y crea y borra `hub_restaurada`.
# En el clúster el mismo script corre en el CronJob:  kubectl -n hub create job --from=cronjob/hub-db-backup respaldo-manual
# Uso: bash gitops/pruebas/respaldo.sh
set -uo pipefail
export MSYS_NO_PATHCONV=1
RAIZ="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$RAIZ"

# </dev/null: dentro de un `while read`, docker exec se comería la lista que se está leyendo
db() { docker compose exec -T db "$@" </dev/null; }
conexion='PGUSER="$POSTGRES_USER" PGDATABASE="$POSTGRES_DB"'
fallos=0
ok() { echo "✓ $1"; }
mal() { echo "✗ $1"; fallos=$((fallos + 1)); }

db pg_isready >/dev/null 2>&1 || { echo "La base no está arriba: docker compose up -d db" >&2; exit 2; }
db sh -c 'rm -rf /tmp/respaldos /tmp/restaurar.sh /tmp/respaldar.sh' >/dev/null
docker compose cp gitops/hub/respaldo/respaldar.sh db:/tmp/respaldar.sh >/dev/null 2>&1
docker compose cp gitops/hub/respaldo/restaurar.sh db:/tmp/restaurar.sh >/dev/null 2>&1

# 1. Respaldo (con rotación: se hacen 3 y se conservan 2)
for i in 1 2 3; do
  salida="$(db sh -c "$conexion RESPALDO_DIR=/tmp/respaldos RESPALDO_CONSERVAR=2 sh /tmp/respaldar.sh" 2>&1)" || { mal "respaldar.sh falló: $salida"; break; }
  sleep 1
done
echo "$salida" | grep -q "Respaldo creado" && ok "respaldar.sh crea el respaldo" || mal "no se creó el respaldo"
n="$(db sh -c 'ls /tmp/respaldos | wc -l' | tr -d '\r ')"
[ "$n" = "2" ] && ok "la rotación conserva 2 de 3 respaldos" || mal "la rotación dejó $n respaldos (se esperaban 2)"
parciales="$(db sh -c 'ls /tmp/respaldos | grep -c parcial || true' | tr -d '\r ')"
[ "$parciales" = "0" ] && ok "no queda ningún archivo parcial" || mal "quedaron $parciales archivos .parcial"
ULTIMO="$(db sh -c 'ls -1t /tmp/respaldos/*.dump | head -1' | tr -d '\r')"

# 2. Restauración en una base nueva
db sh -c "$conexion sh /tmp/restaurar.sh $ULTIMO hub_restaurada" 2>&1 | grep -q "Restaurado en la base hub_restaurada" && ok "restaurar.sh restaura en hub_restaurada" || mal "la restauración falló"
db sh -c "$conexion sh /tmp/restaurar.sh $ULTIMO hub_restaurada" >/dev/null 2>&1 && mal "restaurar.sh sobrescribió una base existente sin REEMPLAZAR" || ok "restaurar.sh se niega a pisar una base existente"
db sh -c "$conexion sh /tmp/restaurar.sh $ULTIMO 'x; drop database hub'" >/dev/null 2>&1 && mal "restaurar.sh aceptó un nombre de base peligroso" || ok "restaurar.sh rechaza un nombre de base con SQL"

# 3. Mismas filas, tabla por tabla
contar() {  # contar <base>: «tabla filas» de todas las tablas públicas
  db sh -c "$conexion psql -d $1 -tAc \"select table_name from information_schema.tables where table_schema='public' order by 1\"" | tr -d '\r' | while read -r t; do
    [ -n "$t" ] && echo "$t $(db sh -c "$conexion psql -d $1 -tAc 'select count(*) from \"$t\"'" | tr -d '\r ')"
  done
}
original="$(contar "\$POSTGRES_DB")"; restaurada="$(contar hub_restaurada)"
tablas="$(echo "$original" | grep -c .)"
if [ "$tablas" -ge 10 ] && [ "$original" = "$restaurada" ]; then ok "las $tablas tablas tienen las mismas filas en la original y en la restaurada"; else mal "las filas difieren:"; diff <(echo "$original") <(echo "$restaurada"); fi

# 4. Limpieza
db sh -c "$conexion dropdb hub_restaurada; rm -rf /tmp/respaldos /tmp/restaurar.sh /tmp/respaldar.sh" >/dev/null 2>&1
[ "$fallos" -eq 0 ] && echo "Todo en verde." || { echo "Falló en $fallos paso(s)."; exit 1; }

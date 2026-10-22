#!/usr/bin/env bash
# Crea en el clúster el Secret `hub-db` con las credenciales de PostgreSQL (spec 003 T16).
# La contraseña se genera al azar y solo existe en el clúster: no se escribe en el repo ni en la
# pantalla. Si el Secret ya existe no se toca (cambiarla con la base ya creada la dejaría fuera).
# Para recuperar la contraseña: kubectl -n hub get secret hub-db -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d
set -euo pipefail

NS="${NS:-hub}"
if kubectl -n "$NS" get secret hub-db >/dev/null 2>&1; then
  echo "El Secret hub-db ya existe en $NS: no se cambia."
  exit 0
fi

USUARIO=hub
BASE=hub
# Clave alfanumérica de 24 caracteres sin depender de Python (en Windows `python` suele ser solo un alias)
CLAVE="$(head -c 48 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 24)"
[ "${#CLAVE}" -eq 24 ] || { echo "No se pudo generar la clave (¿hay /dev/urandom y base64?)." >&2; exit 1; }

kubectl -n "$NS" create secret generic hub-db \
  --from-literal=POSTGRES_USER="$USUARIO" \
  --from-literal=POSTGRES_PASSWORD="$CLAVE" \
  --from-literal=POSTGRES_DB="$BASE" \
  --from-literal=DATABASE_URL="postgresql+psycopg://${USUARIO}:${CLAVE}@postgres.${NS}.svc:5432/${BASE}"
echo "Secret hub-db creado en $NS."

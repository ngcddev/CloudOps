#!/usr/bin/env bash
# Crea en el clúster los Secrets del Hub (specs 003 T16 y 007 T20):
#   hub-db    credenciales de PostgreSQL
#   hub-auth  JWT_SECRET (firma de las sesiones) y SEED_USER_PASSWORD (contraseña de los usuarios sembrados)
# Los valores se generan al azar y solo existen en el clúster: no se escriben en el repo ni en la
# pantalla. Si un Secret ya existe no se toca (cambiar hub-db con la base ya creada la dejaría fuera;
# cambiar hub-auth cierra las sesiones abiertas).
# Para recuperar un valor:
#   kubectl -n hub get secret hub-db -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d
#   kubectl -n hub get secret hub-auth -o jsonpath='{.data.SEED_USER_PASSWORD}' | base64 -d
# Para cambiar la contraseña de los usuarios sembrados: borrar hub-auth, volver a correr el script y
# reiniciar la API (`kubectl -n hub rollout restart deploy/api`); la API solo da contraseña a quien no tiene.
set -euo pipefail

NS="${NS:-hub}"

# Clave alfanumérica sin depender de Python (en Windows `python` suele ser solo un alias)
clave() {  # clave <longitud>
  local largo="$1" valor
  valor="$(head -c $((largo * 3)) /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c "$largo")"
  [ "${#valor}" -eq "$largo" ] || { echo "No se pudo generar la clave (¿hay /dev/urandom y base64?)." >&2; exit 1; }
  printf '%s' "$valor"
}

existe() {  # existe <secret>
  kubectl -n "$NS" get secret "$1" >/dev/null 2>&1
}

if existe hub-db; then
  echo "El Secret hub-db ya existe en $NS: no se cambia."
else
  USUARIO=hub
  BASE=hub
  CLAVE="$(clave 24)"
  kubectl -n "$NS" create secret generic hub-db \
    --from-literal=POSTGRES_USER="$USUARIO" \
    --from-literal=POSTGRES_PASSWORD="$CLAVE" \
    --from-literal=POSTGRES_DB="$BASE" \
    --from-literal=DATABASE_URL="postgresql+psycopg://${USUARIO}:${CLAVE}@postgres.${NS}.svc:5432/${BASE}"
  echo "Secret hub-db creado en $NS."
fi

if existe hub-auth; then
  echo "El Secret hub-auth ya existe en $NS: no se cambia."
else
  kubectl -n "$NS" create secret generic hub-auth \
    --from-literal=JWT_SECRET="$(clave 48)" \
    --from-literal=SEED_USER_PASSWORD="$(clave 16)"
  echo "Secret hub-auth creado en $NS."
  echo "La contraseña de los usuarios sembrados está solo en el clúster; ver arriba cómo recuperarla."
fi

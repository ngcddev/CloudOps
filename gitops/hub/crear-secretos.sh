#!/usr/bin/env bash
# Crea en el clúster los Secrets del Hub (specs 003 T16 y 007 T20):
#   hub-db    credenciales de PostgreSQL
#   hub-auth  JWT_SECRET (firma de las sesiones) y SEED_USER_PASSWORD (contraseña de los usuarios sembrados)
#   hub-pipeline  PIPELINE_TOKEN (con él la puerta de seguridad de Gitea Actions cuenta sus resultados al Hub, spec 006)
#   hub-alertmanager  token (con él Alertmanager avisa al Hub de una caída, spec 008); va en los namespaces
#                     hub (lo lee la API) y monitoring (lo lee Alertmanager) con el mismo valor
# Los valores se generan al azar y solo existen en el clúster: no se escriben en el repo ni en la
# pantalla. Si un Secret ya existe no se toca (cambiar hub-db con la base ya creada la dejaría fuera;
# cambiar hub-auth cierra las sesiones abiertas).
# Para recuperar un valor:
#   kubectl -n hub get secret hub-db -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d
#   kubectl -n hub get secret hub-auth -o jsonpath='{.data.SEED_USER_PASSWORD}' | base64 -d
#   kubectl -n hub get secret hub-pipeline -o jsonpath='{.data.PIPELINE_TOKEN}' | base64 -d
#   kubectl -n hub get secret hub-alertmanager -o jsonpath='{.data.token}' | base64 -d
# Para cambiar la contraseña de los usuarios sembrados: borrar hub-auth, volver a correr el script y
# reiniciar la API (`kubectl -n hub rollout restart deploy/api`); la API solo da contraseña a quien no tiene.
set -euo pipefail

NS="${NS:-hub}"
MONITORING_NS="${MONITORING_NS:-monitoring}"

# Clave alfanumérica sin depender de Python (en Windows `python` suele ser solo un alias)
clave() {  # clave <longitud>
  local largo="$1" valor
  valor="$(head -c $((largo * 3)) /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c "$largo")"
  [ "${#valor}" -eq "$largo" ] || { echo "No se pudo generar la clave (¿hay /dev/urandom y base64?)." >&2; exit 1; }
  printf '%s' "$valor"
}

existe() {  # existe <secret> [namespace]
  kubectl -n "${2:-$NS}" get secret "$1" >/dev/null 2>&1
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

if existe hub-pipeline; then
  echo "El Secret hub-pipeline ya existe en $NS: no se cambia."
else
  kubectl -n "$NS" create secret generic hub-pipeline --from-literal=PIPELINE_TOKEN="$(clave 40)"
  echo "Secret hub-pipeline creado en $NS. Para cargarlo en Gitea: bash pipelines/configurar-gitea.sh (lo lee solo)."
fi

# hub-alertmanager: el mismo token en los dos namespaces. Si ya existe en uno, se copia al otro; así
# volver a correr el script nunca deja a Alertmanager y a la API con tokens distintos.
TOKEN_ALERTAS=""
for ns in "$NS" "$MONITORING_NS"; do
  if [ -z "$TOKEN_ALERTAS" ] && existe hub-alertmanager "$ns"; then
    TOKEN_ALERTAS="$(kubectl -n "$ns" get secret hub-alertmanager -o jsonpath='{.data.token}' | base64 -d)"
  fi
done
TOKEN_ALERTAS="${TOKEN_ALERTAS:-$(clave 40)}"
for ns in "$NS" "$MONITORING_NS"; do
  if existe hub-alertmanager "$ns"; then
    echo "El Secret hub-alertmanager ya existe en $ns: no se cambia."
  else
    kubectl -n "$ns" create secret generic hub-alertmanager --from-literal=token="$TOKEN_ALERTAS"
    echo "Secret hub-alertmanager creado en $ns."
  fi
done

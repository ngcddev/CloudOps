#!/usr/bin/env bash
# Valida y crea un cliente con OpenTofu sin tocar el inventario ante entradas invalidas (spec 011, T08).
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
TOFU_DIR="$SCRIPT_DIR/tofu"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
CLIENTS_FILE="$TOFU_DIR/clients.auto.tfvars.json"
PLANS_FILE="$REPO_ROOT/seed/plans.json"
IAC_TOOL="${IAC_TOOL:-tofu}"

usage() {
  echo "Uso: infra/client-new.sh <nombre> <dominio> <plan>" >&2
  exit 2
}

fail() {
  echo "Error: $*" >&2
  exit 1
}

[[ $# -eq 3 ]] || usage
NAME="$1"
HOST="$2"
PLAN="$3"

case "$IAC_TOOL" in
  tofu|terraform) ;;
  *) fail "herramienta invalida '$IAC_TOOL'; usa tofu o terraform." ;;
esac

if [[ ! "$NAME" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]; then
  fail "nombre invalido '$NAME'; usa minusculas, numeros y guiones simples."
fi

if [[ "$HOST" != *.hub.local || "$HOST" == .hub.local ]]; then
  fail "dominio invalido '$HOST'; debe terminar en .hub.local."
fi

# Se valida todo antes de crear el archivo candidato, para que entradas invalidas no alteren el inventario.
# Sin Python ni jq: el inventario y el catalogo de planes tienen formato fijo y se leen con grep y awk.
if [[ ! "$PLAN" =~ ^[a-z0-9-]+$ ]] || ! grep -Eq "\"code\": *\"$PLAN\"" "$PLANS_FILE" 2>/dev/null; then
  fail "el plan '$PLAN' no existe en seed/plans.json."
fi

# Entradas actuales del inventario, una por linea: "nombre dominio plan".
ENTRIES=""
if [[ -f "$CLIENTS_FILE" ]]; then
  ENTRIES="$(awk '
    /"[^"]+": *\{/ && !/"clients"/ { n = $0; sub(/^[^"]*"/, "", n); sub(/".*$/, "", n) }
    /"host"/ { h = $0; sub(/.*"host": *"/, "", h); sub(/".*/, "", h) }
    /"plan"/ { p = $0; sub(/.*"plan": *"/, "", p); sub(/".*/, "", p); print n, h, p }
  ' "$CLIENTS_FILE")" || fail "no se pudo leer el inventario de clientes."
fi

while read -r existing_name existing_host existing_plan; do
  [[ "$existing_name" == "$NAME" ]] || continue
  if [[ "$existing_host" != "$HOST" || "$existing_plan" != "$PLAN" ]]; then
    fail "el cliente '$NAME' ya existe con otro dominio o plan."
  fi
done <<< "$ENTRIES"

CANDIDATE_FILE="$(mktemp --suffix=.tfvars.json "$TOFU_DIR/.clients.auto.tfvars.XXXXXX")" ||
  fail "no se pudo preparar el inventario temporal."
{
  echo '{'
  echo '  "clients": {'
  # El cliente nuevo va al final; si ya estaba con los mismos datos no se repite.
  printf '%s\n%s %s %s\n' "$ENTRIES" "$NAME" "$HOST" "$PLAN" | awk '
    NF == 3 && !($1 in host) { orden[++total] = $1; host[$1] = $2; plan[$1] = $3 }
    END {
      for (i = 1; i <= total; i++) {
        k = orden[i]
        printf "    \"%s\": {\n      \"host\": \"%s\",\n      \"plan\": \"%s\"\n    }%s\n", k, host[k], plan[k], (i < total ? "," : "")
      }
    }'
  echo '  }'
  echo '}'
} > "$CANDIDATE_FILE"

PLAN_FILE_NAME="client-new-${NAME}-$$.tfplan"
PLAN_FILE_HOST="$SCRIPT_DIR/state/$PLAN_FILE_NAME"
CANDIDATE_NAME="$(basename -- "$CANDIDATE_FILE")"
cleanup() {
  [[ -z "${CANDIDATE_FILE:-}" ]] || rm -f -- "$CANDIDATE_FILE"
  rm -f -- "$PLAN_FILE_HOST"
}
trap cleanup EXIT

if [[ -z "${GITEA_TOKEN:-}" ]]; then
  fail "falta GITEA_TOKEN en el entorno; no se modifico el inventario."
fi

# El plan guardado asegura que el apply ejecute exactamente lo revisado.
"$SCRIPT_DIR/tofu.sh" "$IAC_TOOL" plan -input=false -var-file "$CANDIDATE_NAME" -out "/state/$PLAN_FILE_NAME"

# Conserva el inventario deseado aunque apply falle parcialmente, para poder reintentar.
mv -f -- "$CANDIDATE_FILE" "$CLIENTS_FILE"
CANDIDATE_FILE=""
"$SCRIPT_DIR/tofu.sh" "$IAC_TOOL" apply -input=false "/state/$PLAN_FILE_NAME"

echo "Cliente '$NAME' agregado y aplicado."
echo "Agrega esta entrada al archivo hosts: 127.0.0.1 $HOST"
echo "Pendiente: dar de alta '$NAME' en la consola del Hub."

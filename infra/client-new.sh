#!/usr/bin/env bash
# Valida y crea un cliente con OpenTofu sin tocar el inventario ante entradas invalidas (spec 011, T08).
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
TOFU_DIR="$SCRIPT_DIR/tofu"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
CLIENTS_FILE="$TOFU_DIR/clients.auto.tfvars.json"
PLANS_FILE="$REPO_ROOT/seed/plans.json"

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

if [[ ! "$NAME" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]; then
  fail "nombre invalido '$NAME'; usa minusculas, numeros y guiones simples."
fi

if [[ "$HOST" != *.hub.local || "$HOST" == .hub.local ]]; then
  fail "dominio invalido '$HOST'; debe terminar en .hub.local."
fi

PYTHON_BIN="${PYTHON:-}"
if [[ -z "$PYTHON_BIN" ]]; then
  for candidate in python3 python python.exe; do
    if command -v "$candidate" >/dev/null 2>&1; then
      PYTHON_BIN="$candidate"
      break
    fi
  done
fi
if [[ -z "$PYTHON_BIN" ]] && command -v cmd.exe >/dev/null 2>&1; then
  WINDOWS_PYTHON="$(cmd.exe /c where python.exe 2>/dev/null | tr -d '\r' | head -n 1 || true)"
  if [[ -n "$WINDOWS_PYTHON" ]]; then
    if command -v wslpath >/dev/null 2>&1; then
      PYTHON_BIN="$(wslpath -u "$WINDOWS_PYTHON")"
    elif command -v cygpath >/dev/null 2>&1; then
      PYTHON_BIN="$(cygpath -u "$WINDOWS_PYTHON")"
    fi
  fi
fi
[[ -n "$PYTHON_BIN" ]] || fail "se requiere Python 3; define PYTHON con la ruta del ejecutable."
PYTHON_PLATFORM="$("$PYTHON_BIN" -c 'import sys; print(sys.platform)' 2>/dev/null)" || \
  fail "no se pudo ejecutar Python desde '$PYTHON_BIN'."
PY_CLIENTS_FILE="$CLIENTS_FILE"
PY_PLANS_FILE="$PLANS_FILE"
if [[ "$PYTHON_PLATFORM" == win32 ]]; then
  if command -v wslpath >/dev/null 2>&1; then
    PY_CLIENTS_FILE="$(wslpath -w "$CLIENTS_FILE")"
    PY_PLANS_FILE="$(wslpath -w "$PLANS_FILE")"
  elif command -v cygpath >/dev/null 2>&1; then
    PY_CLIENTS_FILE="$(cygpath -w "$CLIENTS_FILE")"
    PY_PLANS_FILE="$(cygpath -w "$PLANS_FILE")"
  else
    fail "se necesita wslpath o cygpath para usar Python de Windows desde Bash."
  fi
fi

# Valida todo antes de crear el archivo candidato, para que entradas invalidas no alteren el inventario.
if ! CANDIDATE_FILE="$("$PYTHON_BIN" - "$NAME" "$HOST" "$PLAN" "$PY_CLIENTS_FILE" "$PY_PLANS_FILE" <<'PY'
import json
import sys
import tempfile
from pathlib import Path

name, host, plan, clients_file, plans_file = sys.argv[1:]
clients_path = Path(clients_file)


def fail(message):
    print(f"Error: {message}", file=sys.stderr)
    raise SystemExit(1)


try:
    plans = json.loads(Path(plans_file).read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError) as error:
    fail(f"no se pudo leer el catalogo de planes: {error}")

plan_codes = {item.get("code") for item in plans if isinstance(item, dict)}
if plan not in plan_codes:
    fail(f"el plan '{plan}' no existe en seed/plans.json.")

if clients_path.exists():
    try:
        inventory = json.loads(clients_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        fail(f"no se pudo leer el inventario de clientes: {error}")
else:
    inventory = {"clients": {}}

clients = inventory.get("clients")
if not isinstance(clients, dict):
    fail("el inventario debe contener un objeto 'clients'.")
if name in clients:
    fail(f"el cliente '{name}' ya existe en clients.auto.tfvars.json.")

updated_inventory = dict(inventory)
updated_clients = dict(clients)
updated_clients[name] = {"host": host, "plan": plan}
updated_inventory["clients"] = updated_clients

try:
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=clients_path.parent,
        prefix=".clients.auto.tfvars.json.",
        suffix=".tmp",
        delete=False,
    ) as candidate:
        json.dump(updated_inventory, candidate, ensure_ascii=False, indent=2)
        candidate.write("\n")
        print(candidate.name)
except OSError as error:
    fail(f"no se pudo preparar el inventario temporal: {error}")
PY
)"; then
  exit 1
fi
if [[ "$PYTHON_PLATFORM" == win32 ]]; then
  if command -v wslpath >/dev/null 2>&1; then
    CANDIDATE_FILE="$(wslpath -u "$CANDIDATE_FILE")"
  else
    CANDIDATE_FILE="$(cygpath -u "$CANDIDATE_FILE")"
  fi
fi

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
"$SCRIPT_DIR/tofu.sh" tofu plan -input=false -var-file "$CANDIDATE_NAME" -out "/state/$PLAN_FILE_NAME"

# Conserva el inventario deseado aunque apply falle parcialmente, para poder reintentar.
mv -f -- "$CANDIDATE_FILE" "$CLIENTS_FILE"
CANDIDATE_FILE=""
"$SCRIPT_DIR/tofu.sh" tofu apply -input=false "/state/$PLAN_FILE_NAME"

echo "Cliente '$NAME' agregado y aplicado."
echo "Agrega esta entrada al archivo hosts: 127.0.0.1 $HOST"
echo "Pendiente: dar de alta '$NAME' en la consola del Hub."

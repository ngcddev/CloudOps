#!/usr/bin/env bash
# Crea, verifica y elimina un cliente temporal contra el catálogo oficial (spec 011, T14).
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd -- "$INFRA_DIR/.." && pwd)"
TOFU_DIR="$INFRA_DIR/tofu"
TOFU_SH="$INFRA_DIR/tofu.sh"
CLIENTS_FILE="$TOFU_DIR/clients.auto.tfvars.json"
PLANS_FILE="$REPO_ROOT/seed/plans.json"
KUBECONFIG_FILE="$INFRA_DIR/.kubeconfig"
NAME="${TEST_CLIENT_NAME:-prueba-t14}"
HOST="${TEST_CLIENT_HOST:-${NAME}.hub.local}"
PLAN="${TEST_CLIENT_PLAN:-basico}"
KUBE_CONTEXT="${KUBE_CONTEXT:-k3d-hub}"
CLEANUP_NEEDED=0

fail() {
  echo "Error: $*" >&2
  exit 1
}

[[ -n "${GITEA_TOKEN:-}" ]] || fail "falta GITEA_TOKEN en el entorno."
[[ "$NAME" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]] || fail "nombre temporal invalido: '$NAME'."
[[ "$HOST" == *.hub.local && "$HOST" != .hub.local ]] || fail "dominio temporal invalido: '$HOST'."

PYTHON_BIN="${PYTHON:-}"
if [[ -z "$PYTHON_BIN" ]]; then
  for candidate in python3 python python.exe; do
    if command -v "$candidate" >/dev/null 2>&1; then
      PYTHON_BIN="$candidate"
      break
    fi
  done
fi
[[ -n "$PYTHON_BIN" ]] || fail "se requiere Python 3 para validar quota e inventario."

if command -v kubectl.exe >/dev/null 2>&1; then
  KUBECTL_BIN="kubectl.exe"
elif command -v kubectl >/dev/null 2>&1; then
  KUBECTL_BIN="kubectl"
else
  fail "no se encontro kubectl en PATH."
fi
kubectl() {
  "$KUBECTL_BIN" --context "$KUBE_CONTEXT" "$@"
}

[[ -f "$CLIENTS_FILE" ]] || fail "no existe el inventario '$CLIENTS_FILE'."
if "$PYTHON_BIN" - "$CLIENTS_FILE" "$NAME" <<'PY'
import json
import sys
from pathlib import Path

inventory = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if sys.argv[2] in inventory.get("clients", {}):
    raise SystemExit(0)
raise SystemExit(1)
PY
then
  fail "el cliente temporal '$NAME' ya esta en el inventario."
fi

BACKUP_DIR="$(mktemp -d)"
CLIENTS_BACKUP="$BACKUP_DIR/clients.auto.tfvars.json"
KUBECONFIG_BACKUP="$BACKUP_DIR/kubeconfig"
cp -- "$CLIENTS_FILE" "$CLIENTS_BACKUP"
HAD_KUBECONFIG=0
if [[ -f "$KUBECONFIG_FILE" ]]; then
  cp -- "$KUBECONFIG_FILE" "$KUBECONFIG_BACKUP"
  HAD_KUBECONFIG=1
fi

cleanup() {
  local exit_code=$?
  local cleanup_failed=0
  trap - EXIT

  if [[ "$CLEANUP_NEEDED" -eq 1 ]]; then
    echo ">> Eliminando el cliente temporal $NAME"
    if ! "$TOFU_SH" tofu destroy -input=false -auto-approve \
      "-target=module.client[\"$NAME\"]"; then
      echo "No se pudo destruir module.client[\"$NAME\"]; se conserva el inventario para recuperacion." >&2
      cleanup_failed=1
    elif ! kubectl wait --for=delete "namespace/cliente-$NAME" --timeout=180s; then
      echo "El namespace cliente-$NAME no se elimino tras el destroy." >&2
      cleanup_failed=1
    else
      cp -- "$CLIENTS_BACKUP" "$CLIENTS_FILE"
    fi
  else
    cp -- "$CLIENTS_BACKUP" "$CLIENTS_FILE"
  fi

  if [[ "$HAD_KUBECONFIG" -eq 1 ]]; then
    cp -- "$KUBECONFIG_BACKUP" "$KUBECONFIG_FILE"
  else
    rm -f -- "$KUBECONFIG_FILE"
  fi
  rm -rf -- "$BACKUP_DIR"

  if [[ "$cleanup_failed" -eq 1 ]]; then
    exit 1
  fi
  exit "$exit_code"
}
trap cleanup EXIT

"$TOFU_SH" tofu version >/dev/null
kubectl get nodes >/dev/null

echo ">> Creando $NAME ($PLAN)"
if ! bash "$INFRA_DIR/client-new.sh" "$NAME" "$HOST" "$PLAN"; then
  if "$PYTHON_BIN" - "$CLIENTS_FILE" "$NAME" <<'PY'
import json
import sys
from pathlib import Path

inventory = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
raise SystemExit(0 if sys.argv[2] in inventory.get("clients", {}) else 1)
PY
  then
    CLEANUP_NEEDED=1
  fi
  fail "client-new.sh no pudo completar la creacion de '$NAME'."
fi
CLEANUP_NEEDED=1

kubectl wait --for=jsonpath='{.status.sync.status}'=Synced \
  "application/cliente-$NAME" -n argocd --timeout=300s
kubectl wait --for=jsonpath='{.status.health.status}'=Healthy \
  "application/cliente-$NAME" -n argocd --timeout=300s

NAMESPACE_JSON="$(kubectl get namespace "cliente-$NAME" -o json)"
QUOTA_JSON="$(kubectl get resourcequota plan -n "cliente-$NAME" -o json)"
NAMESPACE_JSON="$NAMESPACE_JSON" QUOTA_JSON="$QUOTA_JSON" \
  "$PYTHON_BIN" - "$NAME" "$PLAN" "$PLANS_FILE" <<'PY'
import json
import os
import sys
from pathlib import Path

name, plan_code, plans_path = sys.argv[1:]
plans = json.loads(Path(plans_path).read_text(encoding="utf-8"))
plan = next((item for item in plans if item.get("code") == plan_code), None)
if plan is None:
    raise SystemExit(f"Plan ausente en seed/plans.json: {plan_code}")
namespace = json.loads(os.environ["NAMESPACE_JSON"])
quota = json.loads(os.environ["QUOTA_JSON"])
labels = namespace["metadata"].get("labels", {})
hard = quota["spec"]["hard"]
expected = {
    "hub/client": name,
    "hub/plan": plan_code,
    "limits.cpu": plan["cpu_quota"],
    "limits.memory": plan["memory_quota"],
}
actual = {
    "hub/client": labels.get("hub/client"),
    "hub/plan": labels.get("hub/plan"),
    "limits.cpu": hard.get("limits.cpu"),
    "limits.memory": hard.get("limits.memory"),
}
if actual != expected:
    raise SystemExit(f"Label/quota incorrecta: esperado={expected}, actual={actual}")
print(f"Labels y cuotas correctas para {name} ({plan_code}): {plan['cpu_quota']} / {plan['memory_quota']}")
PY

# El grep debe ignorar menciones de ejemplo, reglas de ignore, documentacion y codigo que crea tokens.
if git -C "$REPO_ROOT" grep -nE 'GITEA_TOKEN=|tfstate' -- \
  . ':!.env.example' ':!.gitignore' ':!**/.gitignore' ':!**/tasks.md' \
  ':!**/plan.md' ':!gitops/hub/crear-tokens.sh' ':!infra/tofu/providers.tf' \
  ':!infra/README.md' ':!infra/pruebas/crear-cliente.sh'; then
  fail "git grep encontro una referencia no permitida a token o state."
fi

echo "Prueba T14 OK; el cleanup quitara application, overlay, namespace y entrada temporal."

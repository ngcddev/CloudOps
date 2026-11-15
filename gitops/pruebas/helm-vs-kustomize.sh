#!/usr/bin/env bash
# Comprueba que el chart de Helm y Kustomize producen los mismos objetos (spec 017, T04): para cada cliente corre `helm template` (imagen alpine/helm, sin instalar nada)
# y `kustomize build` (kubectl kustomize) y compara, objeto por objeto, lo que cada uno renderiza. Así el chart no se desvía de lo que Argo CD aplica de verdad.
# Uso:  bash gitops/pruebas/helm-vs-kustomize.sh        (HELM_IMAGE=alpine/helm:latest por defecto; clientes: ferreteria y consultorio)
set -uo pipefail
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
HELM_IMAGE="${HELM_IMAGE:-alpine/helm:latest}"
CLIENTES="${CLIENTES:-ferreteria consultorio}"
export MSYS_NO_PATHCONV=1
ruta_docker() { (cd "$1" && (pwd -W 2>/dev/null || pwd)); }
conv() { if command -v cygpath >/dev/null 2>&1; then cygpath -m "$1"; else echo "$1"; fi; }

PYBIN=""
for candidato in python3 python; do if "$candidato" -c "import yaml" >/dev/null 2>&1; then PYBIN="$candidato"; break; fi; done
# Sin PyYAML en el equipo (Windows, por ejemplo) la comparación corre en un contenedor de Python
comparar() { # helm.yaml kustomize.yaml
  if [ -n "$PYBIN" ]; then
    "$PYBIN" "$(conv "$COMPARAR")" "$(conv "$1")" "$(conv "$2")"
  else
    docker run --rm -v "$(ruta_docker "$TMP"):/t:ro" python:3.12-slim sh -c "pip install -q pyyaml >/dev/null 2>&1 && python /t/comparar.py /t/$(basename "$1") /t/$(basename "$2")"
  fi
}
if command -v kubectl >/dev/null 2>&1; then
  kustomizar() { kubectl kustomize "$(conv "$1")"; }
else
  kustomizar() { docker run --rm -v "$(ruta_docker "$RAIZ/gitops"):/g:ro" registry.k8s.io/kustomize/kustomize:v5.4.3 build "/g/${1#"$RAIZ"/gitops/}"; }
fi

TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
COMPARAR="$TMP/comparar.py"
cat > "$COMPARAR" <<'PY'
import sys
import yaml

def cargar(ruta):
    objetos = {}
    with open(ruta, encoding="utf-8") as f:
        for doc in yaml.safe_load_all(f):
            if doc:
                objetos[(doc["kind"], doc["metadata"].get("namespace", ""), doc["metadata"]["name"])] = doc
    return objetos

helm, kustomize = cargar(sys.argv[1]), cargar(sys.argv[2])
errores = []
for clave in sorted(set(helm) | set(kustomize)):
    if clave not in helm:
        errores.append(f"falta en Helm: {clave}")
    elif clave not in kustomize:
        errores.append(f"sobra en Helm: {clave}")
    elif helm[clave] != kustomize[clave]:
        a, b = yaml.safe_dump(helm[clave], sort_keys=True).splitlines(), yaml.safe_dump(kustomize[clave], sort_keys=True).splitlines()
        distintas = [f"      helm: {x}   kustomize: {y}" for x, y in zip(a, b) if x != y][:4]
        errores.append(f"distinto: {clave}" + chr(10) + chr(10).join(distintas))
print(f"{len(kustomize)} objetos en Kustomize, {len(helm)} en Helm")
for e in errores:
    print("   " + e)
sys.exit(1 if errores else 0)
PY

fallos=0
for cliente in $CLIENTES; do
  echo "== ${cliente}"
  docker run --rm -v "$(ruta_docker "$RAIZ/gitops/charts"):/c:ro" "$HELM_IMAGE" lint /c/sitio-cliente -f "/c/sitio-cliente/valores/${cliente}.yaml" --strict >/dev/null 2>"$TMP/lint.txt"     || { echo "   FALLA helm lint: $(tail -3 "$TMP/lint.txt")"; fallos=$((fallos+1)); continue; }
  docker run --rm -v "$(ruta_docker "$RAIZ/gitops/charts"):/c:ro" "$HELM_IMAGE" template "$cliente" /c/sitio-cliente -f "/c/sitio-cliente/valores/${cliente}.yaml" > "$TMP/helm-${cliente}.yaml" \
    || { echo "   FALLA helm template"; fallos=$((fallos+1)); continue; }
  kustomizar "$RAIZ/gitops/clients/${cliente}" > "$TMP/kustomize-${cliente}.yaml" || { echo "   FALLA kustomize build"; fallos=$((fallos+1)); continue; }
  if comparar "$TMP/helm-${cliente}.yaml" "$TMP/kustomize-${cliente}.yaml"; then
    echo "   OK   el chart y Kustomize dan los mismos objetos"
  else
    echo "   FALLA el chart se desvía de Kustomize"; fallos=$((fallos+1))
  fi
done
echo
[ "$fallos" -eq 0 ] && echo "Helm y Kustomize coinciden." || { echo "${fallos} cliente(s) con diferencias."; exit 1; }

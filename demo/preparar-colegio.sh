#!/usr/bin/env bash
# Deja la puerta de seguridad del colegio en «ok» para v1 y v2 (spec 016). Dos caminos:
#   · con el runner de Gitea Actions encendido (docker compose -f pipelines/runner/docker-compose.yml up -d) y el repositorio forja-digital/colegio
#     sembrado (pipelines/sembrar-repos-sitios.sh colegio): se vuelven a subir las etiquetas v1 y v2 y la puerta corre sola, como en la demo real
#     (≈1 min por versión; probado el 14 nov: dos corridas ok con los 11 controles registrados en el Hub);
#   · sin runner: se simula con los mismos pasos de pipelines/puerta.sh (≈2 min por versión).
# Se lanza apenas se da de alta el sitio, en otra terminal, mientras se cuenta v1; v2 queda lista antes del cambio.
# Uso:  GITEA_ADMIN_USER=... GITEA_ADMIN_PASSWORD=... bash demo/preparar-colegio.sh      (KUBECONFIG apuntando al clúster)
set -uo pipefail
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
cd "$RAIZ"
GITEA_URL="${GITEA_URL:-http://gitea.hub.local}"

if docker ps --format '{{.Names}}' | grep -q '^runner-runner-1$' && [ -n "${GITEA_ADMIN_USER:-}" ] && [ -n "${GITEA_ADMIN_PASSWORD:-}" ]; then
  echo "→ Runner de Gitea Actions encendido: se vuelven a subir las etiquetas v1 y v2 del colegio"
  autorizacion="Authorization: Basic $(printf '%s:%s' "$GITEA_ADMIN_USER" "$GITEA_ADMIN_PASSWORD" | base64 | tr -d '\n')"
  git_gitea() { git -c "http.extraheader=${autorizacion}" -c user.name="Forja Digital" -c user.email="hub@forjadigital.test" "$@"; }
  tmp="$(mktemp -d)"
  git_gitea clone -q "${GITEA_URL%/}/forja-digital/colegio.git" "$tmp/colegio" || { echo "No se pudo clonar forja-digital/colegio" >&2; exit 1; }
  # Los scripts de la puerta viajan dentro del repositorio del sitio (.gitea/puerta/): se actualizan con los de pipelines/ para que lleguen las
  # excepciones con vencimiento de trivy-excepciones.yaml (T14); sin ellas la puerta frena por las CVE de nginx (T20). Si no cambió nada no hay commit.
  mkdir -p "$tmp/colegio/.gitea/puerta" "$tmp/colegio/.gitea/workflows"
  cp pipelines/puerta.sh pipelines/reportar.sh pipelines/lib.sh pipelines/cosign.pub pipelines/trivy-excepciones.yaml "$tmp/colegio/.gitea/puerta/"
  cp pipelines/puerta.yaml "$tmp/colegio/.gitea/workflows/puerta.yaml"
  git_gitea -C "$tmp/colegio" add -A .gitea
  git_gitea -C "$tmp/colegio" update-index --chmod=+x .gitea/puerta/puerta.sh .gitea/puerta/reportar.sh
  if ! git_gitea -C "$tmp/colegio" diff --cached --quiet; then
    git_gitea -C "$tmp/colegio" commit -q -m "chore: scripts de la puerta actualizados (excepciones de laboratorio con vencimiento)"       && git_gitea -C "$tmp/colegio" push -q origin HEAD:main && echo "   scripts de la puerta actualizados en el repositorio"
  fi
  for version in v1 v2; do
    git_gitea -C "$tmp/colegio" push -q origin ":refs/tags/${version}" 2>/dev/null   # borrar la etiqueta remota; si no existe no pasa nada
    git_gitea -C "$tmp/colegio" tag -f "${version}" HEAD >/dev/null                 # v1 y v2 son el mismo código: la versión llega como APP_VERSION
    git_gitea -C "$tmp/colegio" push -q origin "refs/tags/${version}" 2>&1 | tail -1
    echo "   etiqueta ${version} subida: la puerta corre en el runner"
    sleep 90   # una corrida a la vez (capacidad 1 del runner)
  done
  rm -rf "$tmp"
  echo "Listo: colegio v1 y v2 enviadas al runner (el resultado aparece en el Hub en «Seguridad»)."
  exit 0
fi

echo "→ Sin runner: se simula la puerta (≈2 min por versión)"
export HUB_URL="${HUB_URL:-http://hub.local}"
export HUB_PIPELINE_TOKEN="${HUB_PIPELINE_TOKEN:-$(kubectl -n hub get secret hub-pipeline -o jsonpath='{.data.PIPELINE_TOKEN}' | base64 -d)}"
[ -n "$HUB_PIPELINE_TOKEN" ] || { echo "Falta HUB_PIPELINE_TOKEN (Secret hub-pipeline del clúster)" >&2; exit 1; }
export SITE=colegio
for version in v1 v2; do
  echo "→ Puerta de seguridad de colegio ${version}"
  VERSION_FIJA="$version" bash pipelines/pruebas/simular-puerta.sh limpia | tail -3 || exit 1
done
echo "Listo: colegio v1 y v2 con la puerta en ok."

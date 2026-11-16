#!/usr/bin/env bash
# Publica la documentación como código en Backstage (TechDocs, spec 017 T02): genera el sitio con mkdocs (imagen spotify/techdocs, sin instalar nada) a partir de
# gitops/platform/backstage/docs/ y lo copia al volumen que Backstage sirve. La imagen de Backstage no trae mkdocs ni Docker, por eso se genera fuera (builder: external).
# Uso:  KUBECONFIG=... bash gitops/platform/backstage/publicar-docs.sh
# Requisitos: Docker, el Deployment de Backstage con el volumen de TechDocs (kubectl apply -k gitops/platform/backstage) y la entrada plataforma-cloudops en el catálogo.
set -euo pipefail
AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENTIDAD="${ENTIDAD:-default/component/plataforma-cloudops}"
# Fijada por digest (era `latest`; auditoría IA-02): la imagen del 3 nov 2026. Para actualizarla: docker pull spotify/techdocs && docker inspect --format '{{index .RepoDigests 0}}' spotify/techdocs
IMAGEN="${TECHDOCS_IMAGE:-spotify/techdocs@sha256:ea86a849ba14694b635a31348eb7529515ae51a38d2d3edac6eb6eaffb7d1a94}"
export MSYS_NO_PATHCONV=1
conv() { if command -v cygpath >/dev/null 2>&1; then cygpath -m "$1"; else echo "$1"; fi; }
ruta_docker() { (cd "$1" && (pwd -W 2>/dev/null || pwd)); }

SITIO="$(mktemp -d)"; trap 'rm -rf "$SITIO"' EXIT
echo "→ Generando el sitio con mkdocs"
docker run --rm -v "$(ruta_docker "$AQUI/docs"):/content:ro" -v "$(ruta_docker "$SITIO"):/out" -w /content "$IMAGEN" build -q -d /out
[ -f "$SITIO/index.html" ] || { echo "mkdocs no generó index.html" >&2; exit 1; }
# techdocs_metadata.json es lo que Backstage lee para saber que la documentación existe y qué archivos trae
GEN="$(mktemp)"
cat > "$GEN" <<'PY'
import json, os, sys, time
raiz = sys.argv[1]
archivos = sorted(os.path.relpath(os.path.join(d, f), raiz).replace(os.sep, "/") for d, _, fs in os.walk(raiz) for f in fs)
json.dump({"site_name": "Plataforma CloudOps Client Hub", "site_description": "", "build_timestamp": int(time.time() * 1000), "files": archivos},
          open(os.path.join(raiz, "techdocs_metadata.json"), "w"), ensure_ascii=False)
PY
PYBIN=""
for candidato in python python3; do if "$candidato" -c "import json" >/dev/null 2>&1; then PYBIN="$candidato"; break; fi; done
[ -n "$PYBIN" ] || { echo "Hace falta Python para escribir techdocs_metadata.json" >&2; exit 1; }
"$PYBIN" "$(conv "$GEN")" "$(conv "$SITIO")"; rm -f "$GEN"
echo "   $(find "$SITIO" -type f | wc -l) archivos"

echo "→ Copiando a Backstage (${ENTIDAD})"
kubectl -n hub exec deploy/backstage -- sh -c "rm -rf /techdocs/${ENTIDAD} && mkdir -p /techdocs/${ENTIDAD}"
tar cf - -C "$SITIO" . | kubectl -n hub exec -i deploy/backstage -- tar xf - -C "/techdocs/${ENTIDAD}"
echo "Listo: la documentación se ve en https://backstage.hub.local/docs/${ENTIDAD}"

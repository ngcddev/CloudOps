#!/usr/bin/env bash
# Kit offline del laboratorio (diplomado, sección 9 «Continuidad sin Internet»): junta en una carpeta lo que hace falta para armar el
# entorno sin Internet y lo restaura en otro equipo. Contiene: imágenes OCI (docker save), paquetes de Python (wheels del backend), caché de
# npm del frontend, la base de datos de vulnerabilidades de Trivy y el inventario de los modelos de Ollama. Todo con sumas SHA-256 en un
# manifiesto, para comprobar que nada se corrompió al copiarlo.
#
#   exportar  [carpeta]   descarga y guarda (con Internet). Opciones: --imagenes "a:1 b:2" (lista propia), --sin-python, --sin-npm,
#                         --sin-trivy, --con-modelos (copia ~/.ollama/models: pesa varios GB)
#   verificar [carpeta]   comprueba las sumas SHA-256 del manifiesto
#   restaurar [carpeta]   verifica y carga las imágenes en Docker; deja las rutas de wheels y npm listas para usar sin red
#   listar                muestra las imágenes que entrarían al kit, sin descargar nada
#
# Modelos de Ollama: no hay un comando de exportación; el kit guarda el inventario (`ollama list`) y, con --con-modelos, copia la carpeta de
# modelos. En el equipo destino se copia a ~/.ollama/models. Uso típico: bash infra/kit-offline.sh exportar kit-offline
set -uo pipefail
export MSYS_NO_PATHCONV=1
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
cd "$RAIZ"
accion="${1:-}"; shift || true

# Imágenes del proyecto: las fijadas en los manifiestos del clúster, en los compose y en las herramientas de la puerta de seguridad
imagenes_del_proyecto() {
  {
    for carpeta in gitops/hub observability gitops/clients/restaurante; do
      kubectl kustomize "$(cd "$carpeta" && (pwd -W 2>/dev/null || pwd))" 2>/dev/null | grep -E '^\s+image:' | sed -E 's/^\s+image:\s*//; s/"//g'
    done
    for archivo in gitops/platform/gitea/deployment.yaml gitops/platform/backstage/deployment.yaml; do
      grep -E '^\s+image:' "$archivo" | sed -E 's/^\s+image:\s*//; s/"//g'
    done
    grep -E '_IMAGE="\$\{[A-Z_]+:-' pipelines/lib.sh | sed -E 's/.*:-([^}]*)\}.*/\1/'
    grep -hE '^FROM ' apps/*/Dockerfile* backend/Dockerfile ai/servidor-mlflow/Dockerfile 2>/dev/null | awk '{print $2}' | grep -v -E '^(deps|base|build|dev|prod)'
    echo "registry:2"; echo "postgres:16-alpine"
  } | grep -v -E '^\s*$' | grep -v -E '/plantilla|^gitea\.hub\.local/' | sort -u
}

declare -a OPCIONES_IMAGENES=()
modo_python=1; modo_npm=1; modo_trivy=1; modo_modelos=0; lista_propia=""
carpeta="kit-offline"
parsear() {
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --imagenes) lista_propia="$2"; shift ;;
      --sin-python) modo_python=0 ;;
      --sin-npm) modo_npm=0 ;;
      --sin-trivy) modo_trivy=0 ;;
      --con-modelos) modo_modelos=1 ;;
      -*) echo "Opción desconocida: $1" >&2; exit 2 ;;
      *) carpeta="$1" ;;
    esac
    shift
  done
}

ruta_host() { (cd "$1" && (pwd -W 2>/dev/null || pwd)); }
sumas() { (cd "$1" && find . -type f ! -name manifiesto.sha256 -print0 | sort -z | xargs -0 sha256sum > manifiesto.sha256); }

exportar() {
  parsear "$@"
  mkdir -p "$carpeta"
  local host; host="$(ruta_host "$carpeta")"
  local imagenes
  if [ -n "$lista_propia" ]; then imagenes="$lista_propia"; else imagenes="$(imagenes_del_proyecto)"; fi
  echo "→ Imágenes ($(echo "$imagenes" | wc -w)):"; echo "$imagenes" | tr ' ' '\n' | sed 's/^/   /'
  : > "$carpeta/imagenes.txt"
  local guardables=()
  for imagen in $imagenes; do
    if docker image inspect "$imagen" >/dev/null 2>&1 || docker pull -q "$imagen" >/dev/null 2>&1; then
      guardables+=("$imagen"); echo "$imagen $(docker image inspect "$imagen" --format '{{.Id}}')" >> "$carpeta/imagenes.txt"
    else
      echo "✗ no se pudo obtener $imagen" >&2; return 1
    fi
  done
  docker save -o "$carpeta/imagenes.tar" "${guardables[@]}" || return 1
  echo "✓ imágenes guardadas en imagenes.tar ($(du -h "$carpeta/imagenes.tar" | cut -f1))"

  if [ "$modo_python" = 1 ]; then
    mkdir -p "$carpeta/python"
    docker run --rm -v "$(ruta_host backend):/src:ro" -v "$host/python:/out" python:3.12-slim \
      pip download -q --no-cache-dir -d /out -r /src/requirements.txt -r /src/requirements-dev.txt 2>&1 | grep -v -i -E 'notice|warning'
    echo "✓ paquetes de Python (backend y pruebas): $(ls "$carpeta/python" | wc -l) archivos"
  fi
  if [ "$modo_npm" = 1 ]; then
    mkdir -p "$carpeta/npm-cache"
    (cd frontend && npm ci --ignore-scripts --no-audit --no-fund --cache "$host/npm-cache" --prefer-offline >/dev/null 2>&1) && echo "✓ caché de npm del frontend ($(du -sh "$carpeta/npm-cache" | cut -f1))" || { echo "✗ npm ci falló" >&2; return 1; }
  fi
  if [ "$modo_trivy" = 1 ] && docker volume inspect puerta-trivy-cache >/dev/null 2>&1; then
    docker run --rm -v puerta-trivy-cache:/cache:ro -v "$host:/out" alpine:3.20 tar czf /out/trivy-cache.tgz -C /cache . 2>/dev/null \
      && echo "✓ base de vulnerabilidades de Trivy (volumen puerta-trivy-cache)" || echo "· sin base de Trivy (no se pudo empaquetar)"
  else
    echo "· sin base de Trivy: corre la puerta una vez con Internet para llenar el volumen puerta-trivy-cache"
  fi
  { command -v ollama >/dev/null 2>&1 && ollama list; } > "$carpeta/modelos-ollama.txt" 2>/dev/null || echo "(ollama no está instalado en este equipo)" > "$carpeta/modelos-ollama.txt"
  if [ "$modo_modelos" = 1 ]; then
    origen="${OLLAMA_MODELS:-$HOME/.ollama/models}"
    [ -d "$origen" ] && cp -r "$origen" "$carpeta/ollama-models" && echo "✓ modelos de Ollama copiados de $origen" || echo "✗ no encontré la carpeta de modelos: $origen" >&2
  else
    echo "· modelos de Ollama: solo el inventario (modelos-ollama.txt); usa --con-modelos para copiarlos"
  fi
  date -u +"Kit creado el %Y-%m-%dT%H:%M:%SZ en el commit $(git rev-parse --short HEAD 2>/dev/null || echo desconocido)" > "$carpeta/LEEME.txt"
  sumas "$carpeta"
  echo "✓ manifiesto con $(wc -l < "$carpeta/manifiesto.sha256") sumas SHA-256. Kit listo en $carpeta"
}

verificar() {
  parsear "$@"
  [ -f "$carpeta/manifiesto.sha256" ] || { echo "✗ no hay manifiesto en $carpeta" >&2; return 1; }
  if (cd "$carpeta" && sha256sum --quiet -c manifiesto.sha256); then echo "✓ todas las sumas coinciden"; else echo "✗ el kit está corrupto o incompleto" >&2; return 1; fi
}

restaurar() {
  parsear "$@"
  verificar "$carpeta" || return 1
  docker load -i "$carpeta/imagenes.tar" >/dev/null || { echo "✗ no se pudieron cargar las imágenes" >&2; return 1; }
  echo "✓ imágenes cargadas en Docker: $(wc -l < "$carpeta/imagenes.txt")"
  [ -d "$carpeta/python" ] && echo "  Python sin red:  pip install --no-index --find-links $carpeta/python -r backend/requirements-dev.txt"
  [ -d "$carpeta/npm-cache" ] && echo "  npm sin red:     cd frontend && npm ci --offline --cache $(ruta_host "$carpeta")/npm-cache"
  [ -f "$carpeta/trivy-cache.tgz" ] && echo "  Trivy sin red:   docker volume create puerta-trivy-cache && docker run --rm -v puerta-trivy-cache:/cache -v \$PWD/$carpeta:/in alpine:3.20 tar xzf /in/trivy-cache.tgz -C /cache  (y TRIVY_SKIP_DB_UPDATE=1)"
  [ -d "$carpeta/ollama-models" ] && echo "  Ollama:          copia $carpeta/ollama-models a ~/.ollama/models"
}

case "$accion" in
  exportar) exportar "$@" ;;
  verificar) verificar "$@" ;;
  restaurar) restaurar "$@" ;;
  listar) imagenes_del_proyecto ;;
  *) sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//'; exit 2 ;;
esac

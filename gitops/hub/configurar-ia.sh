#!/usr/bin/env bash
# Conecta el Hub del clúster con Ollama del PC B y elige cómo arma el asistente su contexto (spec 012, T27): crea el ConfigMap
# hub-ia (que la API lee como variables de entorno, opcional) y reinicia la API. La IP del PC B no va en el repositorio.
# Antes, en el PC B: ollama pull qwen2.5:7b-instruct  y  ollama pull nomic-embed-text  (este último solo para el modo rag).
# Uso:  bash gitops/hub/configurar-ia.sh <url-de-ollama> [completo|recuperacion|rag] [--solo-mostrar]
#   bash gitops/hub/configurar-ia.sh http://192.168.1.50:11434 rag
#   --solo-mostrar imprime el ConfigMap sin aplicarlo (no necesita el clúster)
set -euo pipefail

URL="${1:?Uso: configurar-ia.sh <url-de-ollama> [completo|recuperacion|rag] [--solo-mostrar]}"
MODO="${2:-completo}"
SOLO_MOSTRAR=0
for argumento in "$@"; do [ "$argumento" = "--solo-mostrar" ] && SOLO_MOSTRAR=1; done
[ "$MODO" = "--solo-mostrar" ] && MODO=completo

case "$URL" in http://*|https://*) ;; *) echo "La URL de Ollama debe empezar con http:// o https://: $URL" >&2; exit 1 ;; esac
case "$MODO" in completo|recuperacion|rag) ;; *) echo "Modo no válido: $MODO (completo, recuperacion o rag)" >&2; exit 1 ;; esac

configmap() {
  kubectl -n hub create configmap hub-ia \
    --from-literal=OLLAMA_URL="${URL%/}" \
    --from-literal=OLLAMA_MODEL=qwen2.5:7b-instruct \
    --from-literal=OLLAMA_EMBED_MODEL=nomic-embed-text \
    --from-literal=ASSISTANT_CONTEXT_MODE="$MODO" \
    --from-literal=RAG_TOP_K=4 \
    --from-literal=RAG_MIN_SCORE=0.60 \
    --dry-run=client -o yaml
}

if [ "$SOLO_MOSTRAR" = 1 ]; then
  configmap
  exit 0
fi
configmap | kubectl apply -f -
kubectl -n hub rollout restart deployment/api
kubectl -n hub rollout status deployment/api --timeout=120s
echo "Hub conectado a ${URL%/} en modo ${MODO}. Con rag, indexa la ayuda:  POST /api/assistant/reindex (consola de agencia)."

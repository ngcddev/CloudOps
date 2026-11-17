#!/usr/bin/env bash
# Genera las figuras del informe final (PNG) a partir de los archivos Mermaid de esta carpeta, con mermaid-cli en contenedor (no instala nada en el equipo).
# Los diagramas se escribieron a partir de HECHOS.md (elementos y relaciones verificados en el código y en la corrida de evidencias).
# Uso: bash entrega/informe/figuras/generar.sh
set -euo pipefail
AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if command -v cygpath >/dev/null 2>&1; then MONTAJE="$(cygpath -w "$AQUI")"; else MONTAJE="$AQUI"; fi
for f in "$AQUI"/*.mmd; do
  n="$(basename "$f" .mmd)"
  MSYS_NO_PATHCONV=1 docker run --rm -u 0 -v "$MONTAJE:/data" minlag/mermaid-cli:11.4.0 -i "/data/$n.mmd" -o "/data/$n.png" -b white -w 1600 -s 2 >/dev/null
  echo "✓ $n.png"
done

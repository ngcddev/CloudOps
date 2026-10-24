#!/usr/bin/env bash
# Cuenta al Hub qué pasó en la puerta de seguridad (spec 006, T07): POST /api/pipeline-events.
#   reportar.sh inicio
#   reportar.sh paso <control> <ok|fallo> "<resumen>" [imagen] [reporte.json]
#   reportar.sh fin <ok|fallo> [digests.json]
# Variables: HUB_URL, HUB_PIPELINE_TOKEN, SITE (repositorio del sitio), VERSION (tag), COMMIT_SHA, IMAGES
# (imágenes que debe producir la versión, separadas por espacio; solo en `inicio`).
# Falla (código distinto de 0) si el Hub no responde bien: sin que el Hub lo sepa, la versión no se publica.
set -euo pipefail

: "${HUB_URL:?Falta HUB_URL}"
: "${HUB_PIPELINE_TOKEN:?Falta HUB_PIPELINE_TOKEN}"
: "${SITE:?Falta SITE}"
: "${VERSION:?Falta VERSION}"

JQ_IMAGE="${JQ_IMAGE:-ghcr.io/jqlang/jq:1.8.1}"
# jq local si existe; si no, el de un contenedor (el runner solo necesita Docker). Todo entra por stdin.
jq_run() {
  if command -v jq >/dev/null 2>&1; then
    jq "$@"
  else
    docker run --rm -i "$JQ_IMAGE" "$@"
  fi
}

evento="${1:?Uso: reportar.sh inicio | paso <control> <ok|fallo> <resumen> [imagen] [reporte] | fin <ok|fallo> [digests]}"
base=(--arg event "$evento" --arg site "$SITE" --arg version "$VERSION" --arg commit "${COMMIT_SHA:-}")
vacio=/dev/null  # entrada vacía para `jq -n`

case "$evento" in
  inicio)
    cuerpo="$(jq_run -n "${base[@]}" --arg images "${IMAGES:-}" \
      '{event: $event, site: $site, version: $version, commit_sha: (if $commit != "" then $commit else null end),
        images: ($images | split(" ") | map(select(. != "")))}' < "$vacio")"
    ;;
  paso)
    control="${2:?Falta el control}"; estado="${3:?Falta el resultado (ok|fallo)}"; resumen="${4:-}"
    imagen="${5:-}"; reporte="${6:-}"
    if [ -n "$reporte" ] && [ -s "$reporte" ]; then
      cuerpo="$(jq_run --slurp "${base[@]}" --arg step "$control" --arg status "$estado" --arg summary "$resumen" --arg image "$imagen" \
        '{event: $event, site: $site, version: $version, step: $step, status: $status, summary: $summary,
          image: (if $image != "" then $image else null end), report: .[0]}' < "$reporte")"
    else
      cuerpo="$(jq_run -n "${base[@]}" --arg step "$control" --arg status "$estado" --arg summary "$resumen" --arg image "$imagen" \
        '{event: $event, site: $site, version: $version, step: $step, status: $status, summary: $summary,
          image: (if $image != "" then $image else null end)}' < "$vacio")"
    fi
    ;;
  fin)
    estado="${2:?Falta el resultado (ok|fallo)}"; digests="${3:-}"
    if [ -n "$digests" ] && [ -s "$digests" ]; then
      cuerpo="$(jq_run --slurp "${base[@]}" --arg status "$estado" \
        '{event: $event, site: $site, version: $version, status: $status, image_digests: .[0]}' < "$digests")"
    else
      cuerpo="$(jq_run -n "${base[@]}" --arg status "$estado" \
        '{event: $event, site: $site, version: $version, status: $status}' < "$vacio")"
    fi
    ;;
  *) echo "Evento desconocido: $evento" >&2; exit 2 ;;
esac

# El cuerpo viaja por stdin (puede traer un SBOM de varios MB) y la respuesta vuelve en la salida
salida="$(printf '%s' "$cuerpo" | curl -sS -m 60 -w $'\n%{http_code}' \
  -H "Authorization: Bearer ${HUB_PIPELINE_TOKEN}" -H 'Content-Type: application/json' \
  -X POST "${HUB_URL%/}/api/pipeline-events" --data-binary @-)" || salida=$'\n000'
codigo="${salida##*$'\n'}"
respuesta="${salida%$'\n'*}"

if [ "${codigo:0:1}" != "2" ]; then
  echo "El Hub rechazó el evento «${evento}» (HTTP ${codigo}): ${respuesta:0:400}" >&2
  exit 1
fi
id="$(printf '%s' "$respuesta" | jq_run -r '.id')"
estado_corrida="$(printf '%s' "$respuesta" | jq_run -r '.status')"
echo "Hub: ${evento} ${2:-} registrado (corrida #${id}, estado ${estado_corrida})."

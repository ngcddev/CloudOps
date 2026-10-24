#!/usr/bin/env bash
# Puerta de seguridad de una versión de un sitio (spec 006). Un paso por llamada; el workflow los encadena
# y cada uno cuenta su resultado al Hub con reportar.sh. Si un paso falla, el workflow se detiene.
#
#   puerta.sh inicio            abre la corrida en el Hub
#   puerta.sh secretos          Gitleaks sobre los commits nuevos de la versión (antes de construir nada)
#   puerta.sh construir         docker build de cada imagen del sitio
#   puerta.sh vulnerabilidades  Trivy: falla si hay una CVE crítica con arreglo disponible
#   puerta.sh sbom              Syft: inventario de componentes (SPDX), se guarda como evidencia
#   puerta.sh firmar            sube la imagen al registro y la firma con Cosign
#   puerta.sh verificar         cosign verify con la clave pública, sobre el digest que se subió
#   puerta.sh fin               cierra la corrida (JOB_STATUS=success|failure|cancelled); corre siempre
#
# Variables: SITE (repositorio del sitio), VERSION (tag), HUB_URL, HUB_PIPELINE_TOKEN; para firmar y verificar:
# REGISTRY, ORG, REGISTRY_USER, REGISTRY_PASSWORD, COSIGN_PRIVATE_KEY, COSIGN_PASSWORD y pipelines/cosign.pub.
# Desde la raíz del repositorio del sitio, con el tag de la versión ya descargado.
set -euo pipefail

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
paso="${1:?Uso: puerta.sh inicio|secretos|construir|vulnerabilidades|sbom|firmar|verificar|fin}"

: "${SITE:?Falta SITE}"
: "${VERSION:?Falta VERSION}"
REGISTRY="${REGISTRY:-gitea.hub.local}"
ORG="${ORG:-forja-digital}"
COSIGN_PUB="${COSIGN_PUB:-$AQUI/cosign.pub}"
OUT="${PUERTA_OUT:-.puerta}"
# El registro de Gitea del laboratorio va por HTTP: se desactiva TLS (0 si algún día tiene certificado)
REGISTRY_INSEGURO="${REGISTRY_INSEGURO:-1}"
COMMIT_SHA="${COMMIT_SHA:-$(git rev-parse HEAD 2>/dev/null || true)}"
export SITE VERSION COMMIT_SHA

# shellcheck source=lib.sh
source "$AQUI/lib.sh"
mkdir -p "$OUT"
export PUERTA_OUT="$OUT"  # reportar.sh guarda ahí el id de la corrida

# Imágenes que produce el sitio: una (`Dockerfile`) o dos (consultorio: -web y -api)
imagenes() {
  if [ -f Dockerfile ]; then
    echo "$SITE"
  elif [ -f Dockerfile.frontend ] && [ -f Dockerfile.backend ]; then
    echo "${SITE}-web ${SITE}-api"
  else
    echo "No hay Dockerfile en el repositorio de ${SITE}." >&2
    return 1
  fi
}

dockerfile_de() {
  case "$1" in
    "$SITE") echo Dockerfile ;;
    *-web) echo Dockerfile.frontend ;;
    *-api) echo Dockerfile.backend ;;
  esac
}

reportar() { bash "$AQUI/reportar.sh" "$@"; }

# Un control falló: se cuenta al Hub y el paso termina con error
fallo() {  # fallo <control> "<resumen>" [imagen] [reporte]
  reportar paso "$1" fallo "$2" "${3:-}" "${4:-}" || true
  echo "✕ $1: $2" >&2
  exit 1
}

registro_args() {  # opciones de TLS y credenciales para skopeo
  [ "$REGISTRY_INSEGURO" = "1" ] && printf '%s\n' --dest-tls-verify=false
  [ -n "${REGISTRY_USER:-}" ] && printf '%s\n' --dest-creds "${REGISTRY_USER}:${REGISTRY_PASSWORD:-}"
  return 0
}

cosign_registro_args() {  # opciones del registro para cosign
  [ "$REGISTRY_INSEGURO" = "1" ] && printf '%s\n' --allow-http-registry
  [ -n "${REGISTRY_USER:-}" ] && printf '%s\n' --registry-username "$REGISTRY_USER" --registry-password "${REGISTRY_PASSWORD:-}"
  return 0
}

case "$paso" in
  inicio)
    IMAGES="$(imagenes)" reportar inicio
    ;;

  secretos)
    # Solo los commits que esta versión suma sobre la anterior: un secreto viejo ya corregido no bloquea
    # para siempre, uno nuevo sí
    anterior="$(git describe --tags --abbrev=0 "${VERSION}^" 2>/dev/null || true)"
    rango="${anterior:+${anterior}..}${VERSION}"
    commits="$(git rev-list --count "$rango")"
    reporte="$OUT/gitleaks.json"
    if [ "$commits" = "0" ]; then
      # Versiones que apuntan al mismo commit que la anterior (por ejemplo v1 y v2 de los sitios semilla)
      echo '[]' > "$reporte"
      reportar paso secretos ok "Sin commits nuevos desde ${anterior}: ya se revisaron con esa versión" "" "$reporte"
    elif docker_run -v "${HOST_PWD}:/repo" \
        -e GIT_CONFIG_COUNT=1 -e GIT_CONFIG_KEY_0=safe.directory -e GIT_CONFIG_VALUE_0=/repo \
        "$GITLEAKS_IMAGE" git /repo --log-opts="$rango" --redact --no-banner --exit-code 1 \
        --report-format json --report-path "/repo/${reporte}"; then
      reportar paso secretos ok "Sin secretos en ${commits} commit(s) nuevo(s) (${rango})" "" "$reporte"
    else
      detalle="$(jq_run -r '[.[] | "\(.File):\(.StartLine) (\(.RuleID))"] | .[:5] | join(", ")' < "$reporte" 2>/dev/null || true)"
      total="$(jq_run 'length' < "$reporte" 2>/dev/null || echo '?')"
      fallo secretos "${total} hallazgo(s) en ${rango}: ${detalle}" "" "$reporte"
    fi
    ;;

  construir)
    for imagen in $(imagenes); do
      if docker build -q --build-arg "APP_VERSION=${VERSION}" -f "$(dockerfile_de "$imagen")" \
          -t "puerta/${imagen}:${VERSION}" . >/dev/null; then
        docker save "puerta/${imagen}:${VERSION}" -o "${OUT}/${imagen}.tar"
        reportar paso construccion ok "Imagen construida con $(dockerfile_de "$imagen")" "$imagen"
      else
        fallo construccion "No se pudo construir la imagen con $(dockerfile_de "$imagen")" "$imagen"
      fi
    done
    ;;

  vulnerabilidades)
    for imagen in $(imagenes); do
      reporte="${OUT}/trivy-${imagen}.json"
      if docker_run -v "${HOST_PWD}/${OUT}:/out" -v puerta-trivy-cache:/root/.cache "$TRIVY_IMAGE" image \
          --input "/out/${imagen}.tar" --severity CRITICAL --ignore-unfixed --exit-code 1 --quiet \
          ${TRIVY_SKIP_DB_UPDATE:+--skip-db-update} --format json --output "/out/trivy-${imagen}.json"; then
        reportar paso vulnerabilidades ok "Sin vulnerabilidades críticas con arreglo disponible" "$imagen" "$reporte"
      else
        [ -s "$reporte" ] || fallo vulnerabilidades "Trivy no pudo revisar la imagen (¿falta la base de datos?)" "$imagen"
        total="$(jq_run '[.Results[]?.Vulnerabilities[]? | select(.Severity == "CRITICAL")] | length' < "$reporte")"
        detalle="$(jq_run -r '[.Results[]?.Vulnerabilities[]? | select(.Severity == "CRITICAL") | "\(.VulnerabilityID) (\(.PkgName))"] | .[:5] | join(", ")' < "$reporte")"
        fallo vulnerabilidades "${total} vulnerabilidad(es) crítica(s): ${detalle}" "$imagen" "$reporte"
      fi
    done
    ;;

  sbom)
    for imagen in $(imagenes); do
      reporte="${OUT}/sbom-${imagen}.spdx.json"
      if docker_run -v "${HOST_PWD}/${OUT}:/out" "$SYFT_IMAGE" scan "docker-archive:/out/${imagen}.tar" \
          -o "spdx-json=/out/sbom-${imagen}.spdx.json" -q; then
        componentes="$(jq_run '.packages | length' < "$reporte")"
        reportar paso sbom ok "Inventario SPDX con ${componentes} componente(s)" "$imagen" "$reporte"
      else
        fallo sbom "No se pudo generar el inventario de componentes" "$imagen"
      fi
    done
    ;;

  firmar)
    : "${COSIGN_PRIVATE_KEY:?Falta COSIGN_PRIVATE_KEY (secreto de Gitea Actions)}"
    for imagen in $(imagenes); do
      destino="${REGISTRY}/${ORG}/${imagen}"
      mapfile -t registro < <(registro_args)
      if ! docker_run -v "${HOST_PWD}/${OUT}:/out" "$SKOPEO_IMAGE" copy "${registro[@]}" \
          --digestfile "/out/${imagen}.digest" "docker-archive:/out/${imagen}.tar" "docker://${destino}:${VERSION}"; then
        fallo firma "No se pudo subir la imagen a ${REGISTRY}" "$imagen"
      fi
      digest="$(cat "${OUT}/${imagen}.digest")"
      mapfile -t cosign_reg < <(cosign_registro_args)
      if docker_run -e COSIGN_PRIVATE_KEY -e COSIGN_PASSWORD "$COSIGN_IMAGE" sign --key env://COSIGN_PRIVATE_KEY \
          --yes --use-signing-config=false --tlog-upload=false "${cosign_reg[@]}" "${destino}@${digest}"; then
        reportar paso firma ok "Imagen subida como ${imagen}:${VERSION} (${digest:0:19}…) y firmada" "$imagen"
      else
        fallo firma "No se pudo firmar la imagen ${imagen}@${digest:0:19}…" "$imagen"
      fi
    done
    ;;

  verificar)
    [ -f "$COSIGN_PUB" ] || { echo "Falta la clave pública $COSIGN_PUB" >&2; exit 1; }
    for imagen in $(imagenes); do
      digest="$(cat "${OUT}/${imagen}.digest")"
      reporte="${OUT}/verify-${imagen}.json"
      mapfile -t cosign_reg < <(cosign_registro_args)
      # La verificación es sobre el digest que se subió, no sobre la etiqueta: nadie la puede cambiar en medio
      # Se monta la carpeta de la clave (con ruta de Windows si hace falta) y se lee por nombre
      carpeta_pub="$(cd "$(dirname "$COSIGN_PUB")" && (pwd -W 2>/dev/null || pwd))"
      if docker_run -v "${carpeta_pub}:/pub:ro" "$COSIGN_IMAGE" verify --key "/pub/$(basename "$COSIGN_PUB")" \
          --insecure-ignore-tlog=true "${cosign_reg[@]}" "${REGISTRY}/${ORG}/${imagen}@${digest}" > "$reporte"; then
        reportar paso verificacion ok "Firma válida con la clave pública del Hub (${digest:0:19}…)" "$imagen" "$reporte"
      else
        fallo verificacion "La firma de ${imagen}@${digest:0:19}… no es válida o falta" "$imagen"
      fi
    done
    ;;

  fin)
    estado=fallo
    [ "${JOB_STATUS:-}" = "success" ] && estado=ok
    digests="${OUT}/digests.json"
    {
      printf '{'
      separador=''
      for imagen in $(imagenes 2>/dev/null || true); do
        [ -s "${OUT}/${imagen}.digest" ] || continue
        printf '%s"%s":"%s"' "$separador" "$imagen" "$(cat "${OUT}/${imagen}.digest")"
        separador=','
      done
      printf '}'
    } > "$digests"
    reportar fin "$estado" "$digests"
    ;;

  *)
    echo "Paso desconocido: $paso" >&2
    exit 2
    ;;
esac

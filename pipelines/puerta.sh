#!/usr/bin/env bash
# Puerta de seguridad de una versión de un sitio (spec 006). Un paso por llamada; el workflow los encadena
# y cada uno cuenta su resultado al Hub con reportar.sh. Si un paso falla, el workflow se detiene.
#
#   puerta.sh inicio            abre la corrida en el Hub
#   puerta.sh secretos          Gitleaks sobre los commits nuevos de la versión (antes de construir nada)
#   puerta.sh construir         pruebas del sitio (si tiene backend con pytest) y docker build de cada imagen
#   puerta.sh vulnerabilidades  Trivy: falla si hay una CVE crítica con arreglo disponible
#   puerta.sh sbom              Syft: inventario de componentes (SPDX), se guarda como evidencia
#   puerta.sh firmar            sube la imagen al registro, la firma con Cosign y le adjunta la procedencia SLSA v1 y el SBOM (SPDX)
#   puerta.sh verificar         cosign verify y verify-attestation con la clave pública, sobre el digest que se subió
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
    # Pruebas del sitio: si trae un backend con pytest.ini se corren antes de construir; si fallan, no se construye nada.
    # El fallo se cuenta como fallo de la construcción (el Hub tiene un control por imagen, no uno por pruebas).
    pruebas="sin pruebas automatizadas"
    if [ -f backend/pytest.ini ]; then
      if docker_run -v "${HOST_PWD}/backend:/app" -w /app "$PYTHON_IMAGE" sh -c \
          'pip install -q --no-cache-dir -r requirements.txt -r requirements-dev.txt && python -m pytest -q' > "${OUT}/pruebas.log" 2>&1; then
        pruebas="pruebas del sitio: $(tail -1 "${OUT}/pruebas.log")"
      else
        # El Hub guarda los reportes como JSON: la salida de pytest viaja envuelta en un objeto
        jq_run -Rs '{salida: .}' < "${OUT}/pruebas.log" > "${OUT}/pruebas.json"
        # «construccion» es un control por imagen: el fallo se anota en la primera imagen del sitio
        fallo construccion "Las pruebas del sitio fallaron: $(tail -1 "${OUT}/pruebas.log")" "$(imagenes | cut -d' ' -f1)" "${OUT}/pruebas.json"
      fi
    fi
    for imagen in $(imagenes); do
      if docker build -q --build-arg "APP_VERSION=${VERSION}" -f "$(dockerfile_de "$imagen")" \
          -t "puerta/${imagen}:${VERSION}" . >/dev/null; then
        docker save "puerta/${imagen}:${VERSION}" -o "${OUT}/${imagen}.tar"
        reportar paso construccion ok "Imagen construida con $(dockerfile_de "$imagen") (${pruebas})" "$imagen"
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
    # Configuración (spec 016): los Dockerfile del sitio con `trivy config`; un hallazgo ALTO o CRÍTICO (root, puertos, secretos en ENV) frena la puerta.
    # Se anota en la primera imagen: el Hub tiene un control de vulnerabilidades por imagen, no uno aparte para la configuración.
    reporte_config="${OUT}/trivy-config.json"
    if docker_run -v "${HOST_PWD}:/repo:ro" -v "${HOST_PWD}/${OUT}:/out" -v puerta-trivy-cache:/root/.cache "$TRIVY_IMAGE" config         --severity HIGH,CRITICAL --exit-code 1 --quiet ${TRIVY_SKIP_DB_UPDATE:+--skip-check-update}         --format json --output /out/trivy-config.json /repo; then
      echo "Configuración de los Dockerfile sin hallazgos altos ni críticos."
    else
      [ -s "$reporte_config" ] || fallo vulnerabilidades "Trivy no pudo revisar la configuración de los Dockerfile" "$(imagenes | cut -d' ' -f1)"
      detalle="$(jq_run -r '[.Results[]? | select(.Misconfigurations != null) | .Target as $t | .Misconfigurations[] | "\($t): \(.ID) \(.Title)"] | .[:5] | join(", ")' < "$reporte_config")"
      fallo vulnerabilidades "Configuración insegura (Dockerfile o manifiestos): ${detalle}" "$(imagenes | cut -d' ' -f1)" "$reporte_config"
    fi
    # Dependencias declaradas por el sitio (spec 018, SCA): requirements.txt, package-lock.json…; un hallazgo ALTO o CRÍTICO con arreglo publicado frena la puerta.
    reporte_deps="${OUT}/trivy-dependencias.json"
    if docker_run -v "${HOST_PWD}:/repo:ro" -v "${HOST_PWD}/${OUT}:/out" -v puerta-trivy-cache:/root/.cache "$TRIVY_IMAGE" fs --scanners vuln \
        --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1 --quiet ${TRIVY_SKIP_DB_UPDATE:+--skip-db-update} --skip-dirs /repo/.puerta --skip-dirs '**/node_modules' \
        --format json --output /out/trivy-dependencias.json /repo; then
      echo "Dependencias del sitio sin vulnerabilidades altas ni críticas con arreglo."
    else
      [ -s "$reporte_deps" ] || fallo vulnerabilidades "Trivy no pudo revisar las dependencias del sitio" "$(imagenes | cut -d' ' -f1)"
      detalle="$(jq_run -r '[.Results[]? | .Target as $t | .Vulnerabilities[]? | "\($t): \(.PkgName) \(.InstalledVersion) a \(.FixedVersion) (\(.VulnerabilityID))"] | .[:4] | join(", ")' < "$reporte_deps")"
      fallo vulnerabilidades "Dependencia vulnerable con arreglo publicado: ${detalle}" "$(imagenes | cut -d' ' -f1)" "$reporte_deps"
    fi
    ;;

  sbom)
    for imagen in $(imagenes); do
      reporte="${OUT}/sbom-${imagen}.spdx.json"
      if docker_run -v "${HOST_PWD}/${OUT}:/out" "$SYFT_IMAGE" scan "docker-archive:/out/${imagen}.tar" \
          -o "spdx-json=/out/sbom-${imagen}.spdx.json" -q; then
        componentes="$(jq_run '.packages | length' < "$reporte")"
        # Licencias (spec 016): Trivy clasifica las del inventario. Una prohibida (AGPL, SSPL…) frena la puerta; las restringidas
        # (GPL de la imagen base) se informan: usar un componente así no obliga a publicar el sitio, pero hay que saberlo.
        licencias="${OUT}/licencias-${imagen}.json"
        if ! docker_run -v "${HOST_PWD}/${OUT}:/out" -v puerta-trivy-cache:/root/.cache "$TRIVY_IMAGE" sbom --scanners license             --severity CRITICAL --exit-code 1 --quiet ${TRIVY_SKIP_DB_UPDATE:+--skip-db-update} --format json             --output "/out/licencias-${imagen}.json" "/out/sbom-${imagen}.spdx.json"; then
          detalle="$(jq_run -r '[.Results[]?.Licenses[]? | select(.Severity == "CRITICAL") | "\(.Name) (\(.PkgName))"] | .[:5] | join(", ")' < "$licencias" 2>/dev/null || true)"
          fallo sbom "Licencia prohibida en el inventario: ${detalle:-no se pudo revisar}" "$imagen" "$licencias"
        fi
        restringidas="$(jq_run '[.Results[]?.Licenses[]? | select(.Severity == "HIGH")] | length' < "$licencias" 2>/dev/null || echo 0)"
        reportar paso sbom ok "Inventario SPDX con ${componentes} componente(s); licencias: ninguna prohibida y ${restringidas} restringida(s) (informativo)" "$imagen" "$reporte"
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
      if ! docker_run -e COSIGN_PRIVATE_KEY -e COSIGN_PASSWORD "$COSIGN_IMAGE" sign --key env://COSIGN_PRIVATE_KEY \
          --yes --use-signing-config=false --tlog-upload=false "${cosign_reg[@]}" "${destino}@${digest}"; then
        fallo firma "No se pudo firmar la imagen ${imagen}@${digest:0:19}…" "$imagen"
      fi
      # Procedencia (SLSA v1): qué commit, qué repositorio y qué corrida produjeron esta imagen. Va firmada y atada al digest:
      # `verificar` comprueba que el commit declarado sea el de la versión. No es una certificación de nivel SLSA.
      jq_run -n --arg sitio "$SITE" --arg version "$VERSION" --arg imagen "$imagen" --arg dockerfile "$(dockerfile_de "$imagen")" \
          --arg repo "${REPO_URL:-$(git config --get remote.origin.url 2>/dev/null || echo desconocido)}" --arg commit "$COMMIT_SHA" \
          --arg corrida "${RUN_URL:-desconocida}" --arg ahora "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
          --arg gitleaks "$GITLEAKS_IMAGE" --arg trivy "$TRIVY_IMAGE" --arg syft "$SYFT_IMAGE" --arg cosign "$COSIGN_IMAGE" \
          '{buildDefinition: {buildType: "https://forja-digital.local/puerta/v1",
              externalParameters: {sitio: $sitio, version: $version, imagen: $imagen, ref: ("refs/tags/" + $version), dockerfile: $dockerfile},
              internalParameters: {herramientas: {gitleaks: $gitleaks, trivy: $trivy, syft: $syft, cosign: $cosign}},
              resolvedDependencies: [{uri: ("git+" + $repo + "@refs/tags/" + $version), digest: {gitCommit: $commit}}]},
            runDetails: {builder: {id: "https://forja-digital.local/puerta/runner"}, metadata: {invocationId: $corrida, finishedOn: $ahora}}}' \
          < /dev/null > "${OUT}/provenance-${imagen}.json"
      if ! docker_run -e COSIGN_PRIVATE_KEY -e COSIGN_PASSWORD -v "${HOST_PWD}/${OUT}:/out" "$COSIGN_IMAGE" attest --key env://COSIGN_PRIVATE_KEY \
          --yes --use-signing-config=false --tlog-upload=false --type slsaprovenance1 --predicate "/out/provenance-${imagen}.json" \
          "${cosign_reg[@]}" "${destino}@${digest}" >/dev/null; then
        fallo firma "La imagen se firmó pero no se pudo adjuntar su procedencia (${imagen}@${digest:0:19}…)" "$imagen"
      fi
      # SBOM (SPDX, spec 018): viaja con la imagen, firmado y atado al digest, para que quien reciba la imagen sepa qué contiene sin volver a escanearla
      # ni fiarse de un archivo suelto. `verificar` lo comprueba con la misma clave.
      if docker_run -e COSIGN_PRIVATE_KEY -e COSIGN_PASSWORD -v "${HOST_PWD}/${OUT}:/out" "$COSIGN_IMAGE" attest --key env://COSIGN_PRIVATE_KEY \
          --yes --use-signing-config=false --tlog-upload=false --type spdxjson --predicate "/out/sbom-${imagen}.spdx.json" \
          "${cosign_reg[@]}" "${destino}@${digest}" >/dev/null; then
        reportar paso firma ok "Imagen subida como ${imagen}:${VERSION} (${digest:0:19}…), firmada y con su procedencia SLSA y su SBOM" "$imagen" "${OUT}/provenance-${imagen}.json"
      else
        fallo firma "La imagen se firmó pero no se pudo adjuntar su SBOM (${imagen}@${digest:0:19}…)" "$imagen"
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
        :
      else
        fallo verificacion "La firma de ${imagen}@${digest:0:19}… no es válida o falta" "$imagen"
      fi
      # La procedencia también debe estar firmada con la misma clave y declarar el commit de esta versión
      procedencia="${OUT}/verify-attestation-${imagen}.json"
      if ! docker_run -v "${carpeta_pub}:/pub:ro" "$COSIGN_IMAGE" verify-attestation --key "/pub/$(basename "$COSIGN_PUB")" \
          --type slsaprovenance1 --insecure-ignore-tlog=true "${cosign_reg[@]}" "${REGISTRY}/${ORG}/${imagen}@${digest}" > "$procedencia" 2>/dev/null; then
        fallo verificacion "La imagen ${imagen}@${digest:0:19}… no tiene una procedencia SLSA firmada válida" "$imagen"
      fi
      commit_declarado="$(jq_run -r '.payload' < "$procedencia" | head -1 | base64 -d | jq_run -r '.predicate.buildDefinition.resolvedDependencies[0].digest.gitCommit')"
      if [ -n "${COMMIT_SHA:-}" ] && [ "$commit_declarado" != "$COMMIT_SHA" ]; then
        fallo verificacion "La procedencia de ${imagen} declara el commit ${commit_declarado:0:12}, no el de la versión (${COMMIT_SHA:0:12})" "$imagen"
      fi
      # El SBOM atestado también debe estar firmado con la misma clave y traer componentes: un inventario vacío no describe nada
      sbom_atestado="${OUT}/verify-attestation-sbom-${imagen}.json"
      if ! docker_run -v "${carpeta_pub}:/pub:ro" "$COSIGN_IMAGE" verify-attestation --key "/pub/$(basename "$COSIGN_PUB")" \
          --type spdxjson --insecure-ignore-tlog=true "${cosign_reg[@]}" "${REGISTRY}/${ORG}/${imagen}@${digest}" > "$sbom_atestado" 2>/dev/null; then
        fallo verificacion "La imagen ${imagen}@${digest:0:19}… no tiene un SBOM firmado válido" "$imagen"
      fi
      componentes="$(jq_run -r '.payload' < "$sbom_atestado" | head -1 | base64 -d | jq_run -r '.predicate.packages | length' 2>/dev/null || echo 0)"
      if [ "${componentes:-0}" -lt 1 ]; then
        fallo verificacion "El SBOM atestado de ${imagen} no trae componentes" "$imagen"
      fi
      reportar paso verificacion ok "Firma, procedencia SLSA y SBOM (${componentes} componentes) válidos con la clave pública del Hub (${digest:0:19}…, commit ${commit_declarado:0:12})" "$imagen" "$reporte"
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

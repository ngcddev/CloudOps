#!/usr/bin/env bash
# Simula en una sola máquina lo que hará el workflow de la puerta de seguridad (spec 006, T08-T11): corre
# los mismos pasos de pipelines/puerta.sh contra el Hub real y un registro local, sin Gitea ni runner.
#
#   limpia    versión sin problemas: pasa los seis controles, queda firmada y verificada
#   secreto   un commit nuevo con una clave de AWS falsa: falla en «secretos» y no construye nada
#   vulnerable  imagen base vieja con CVE críticas: falla en «vulnerabilidades»
#   firma-ajena  se verifica con otra clave pública: falla en «verificación»
#   todas     las cuatro, en ese orden (por defecto)
#
# Uso:  HUB_URL=http://localhost:8000 HUB_PIPELINE_TOKEN=<token> bash pipelines/pruebas/simular-puerta.sh [escenario]
#   SITE=ferreteria (por defecto) debe existir en el Hub; cada corrida usa una versión nueva (sim-<n>).
#   La primera vez baja las imágenes de las herramientas y la base de datos de Trivy (unos minutos).
# No toca nada del repositorio: todo ocurre en una carpeta temporal y en contenedores que se borran al terminar.
set -uo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PUERTA="$RAIZ/pipelines/puerta.sh"
: "${HUB_URL:?Falta HUB_URL}"
: "${HUB_PIPELINE_TOKEN:?Falta HUB_PIPELINE_TOKEN}"
SITE="${SITE:-ferreteria}"
ESCENARIO="${1:-todas}"
RED=puerta-sim
REGISTRO=puerta-registro
COSIGN_IMAGE="${COSIGN_IMAGE:-ghcr.io/sigstore/cosign/cosign:v3.1.4}"
export MSYS_NO_PATHCONV=1

fallos=0
ok()    { echo "   OK   $1"; }
falla() { echo "   FALLA $1"; fallos=$((fallos+1)); }

TMP="$(mktemp -d)"
TMP_HOST="$(cd "$TMP" && (pwd -W 2>/dev/null || pwd))"
limpiar() {
  docker rm -f "$REGISTRO" >/dev/null 2>&1
  docker network rm "$RED" >/dev/null 2>&1
  rm -rf "$TMP"
}
trap limpiar EXIT

echo "== Preparación: red, registro local y claves de prueba =="
docker network create "$RED" >/dev/null 2>&1 || true
docker rm -f "$REGISTRO" >/dev/null 2>&1
docker run -d --name "$REGISTRO" --network "$RED" registry:2 >/dev/null && ok "registro local ${REGISTRO}:5000"
export COSIGN_PASSWORD="clave-de-prueba-local"
mkdir -p "$TMP/claves" "$TMP/claves-ajenas"
for carpeta in claves claves-ajenas; do
  docker run --rm -e COSIGN_PASSWORD -v "${TMP_HOST}/${carpeta}:/k" -w /k "$COSIGN_IMAGE" generate-key-pair >/dev/null 2>&1 \
    && ok "par de claves de prueba en ${carpeta}" || { falla "no se pudieron crear las claves"; exit 1; }
done
export COSIGN_PRIVATE_KEY
COSIGN_PRIVATE_KEY="$(cat "$TMP/claves/cosign.key")"

# Repositorio del sitio de prueba, copiado de apps/<sitio>, con una primera versión limpia
REPO="$TMP/sitio"
cp -r "$RAIZ/apps/$SITE" "$REPO"
# Carpeta de los archivos web del sitio: src/ (una imagen) o frontend/ (consultorio, con -web y -api)
if [ -f "$REPO/Dockerfile" ]; then WEB=src; else WEB=frontend; fi
# Lo que genera la puerta (imágenes, reportes) no es del repositorio ni del contexto de construcción
printf '.puerta\n' >> "$REPO/.dockerignore"
(cd "$REPO" && git init -q -b main . && git config user.email prueba@forja.test && git config user.name "Prueba local" \
  && printf '.puerta/\n' >> .git/info/exclude \
  && git add -A && git commit -q -m "feat: versión inicial" && git tag base)

siguiente=$(( $(date +%s) % 100000 ))
# Deja en V la versión siguiente (sin subshell: el contador tiene que avanzar de verdad)
nueva_version() { siguiente=$((siguiente + 1)); V="sim-${siguiente}"; }

# correr <escenario> <versión> <clave pública>: los pasos del workflow, y el cierre que corre siempre
correr() {
  local version="$1" pub="$2" estado=success
  (
    cd "$REPO" || exit 1
    export SITE VERSION="$version" HUB_URL HUB_PIPELINE_TOKEN COSIGN_PUB="$pub" PUERTA_OUT=.puerta
    export REGISTRY="${REGISTRO}:5000" ORG=forja-digital DOCKER_NETWORK="$RED" REGISTRY_INSEGURO=1 TRIVY_SKIP_DB_UPDATE="${TRIVY_SKIP_DB_UPDATE:-}"
    for paso in inicio secretos construir vulnerabilidades sbom firmar verificar; do
      bash "$PUERTA" "$paso" || exit 1
    done
  ) || estado=failure
  (cd "$REPO" && SITE="$SITE" VERSION="$version" HUB_URL="$HUB_URL" HUB_PIPELINE_TOKEN="$HUB_PIPELINE_TOKEN" \
    JOB_STATUS="$estado" PUERTA_OUT=.puerta bash "$PUERTA" fin)
  [ "$estado" = success ]
}

# estado_en_el_hub <versión>: la última corrida de la versión según el Hub (necesita sesión de agencia)
estado_en_el_hub() {
  curl -s -m 10 -H "Authorization: Bearer ${HUB_SESION:-}" "${HUB_URL%/}/api/services/status" >/dev/null 2>&1
}

verificar_corrida() {  # verificar_corrida <versión> <estado esperado> [control que falla]
  local version="$1" esperado="$2" control="${3:-}"
  [ -n "${HUB_SESION:-}" ] || return 0
  local servicios id corridas
  servicios="$(curl -s -m 10 -H "Authorization: Bearer ${HUB_SESION}" "${HUB_URL%/}/api/services/status")"
  id="$(echo "$servicios" | tr '{' '\n' | grep "cliente-${SITE}\"" | sed -n 's/.*"service_id":\([0-9]*\).*/\1/p' | head -1)"
  corridas="$(curl -s -m 10 -H "Authorization: Bearer ${HUB_SESION}" "${HUB_URL%/}/api/services/${id}/security-runs")"
  local corrida
  corrida="$(echo "$corridas" | tr '{' '\n' | grep "\"version\":\"${version}\"" | head -1)"
  if echo "$corrida" | grep -q "\"status\":\"${esperado}\""; then ok "el Hub registró ${version} en «${esperado}»"; else falla "el Hub no tiene ${version} en «${esperado}»: ${corrida:0:200}"; fi
  if [ -n "$control" ]; then
    echo "$corridas" | grep -q "\"failed_step\":\"${control}\"" && ok "el control que falló fue «${control}»" || falla "el control que falló no fue «${control}»"
  fi
}

# Sesión de agencia (opcional) para comprobar lo que quedó en el Hub
if [ -n "${HUB_USUARIO:-}" ] && [ -n "${HUB_PASSWORD:-}" ]; then
  HUB_SESION="$(curl -s -m 10 -H 'Content-Type: application/json' -X POST "${HUB_URL%/}/api/auth/login" \
    -d "{\"email\":\"${HUB_USUARIO}\",\"password\":\"${HUB_PASSWORD}\"}" | sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p')"
fi

escenario_limpia() {
  echo "== Escenario «limpia»: debe pasar los seis controles =="
  local v; nueva_version; v="$V"
  (cd "$REPO" && git checkout -q -B limpia base && echo "<!-- ${v} -->" >> "$WEB/index.html" && git commit -qam "feat: ajuste menor" && git tag "$v")
  if correr "$v" "$TMP/claves/cosign.pub"; then ok "la puerta terminó bien"; else falla "la puerta falló en una versión limpia"; fi
  verificar_corrida "$v" ok
}

escenario_secreto() {
  # La clave de AWS es falsa pero no contiene la palabra EXAMPLE: Gitleaks ignora las que sí la tienen
  echo "== Escenario «secreto»: una clave de AWS en un archivo =="
  local v; nueva_version; v="$V"
  (cd "$REPO" && git checkout -q -B secreto base && printf 'const aws = "AKIA%s";\nconst secret = "%s";\n' "Z3MQ7XK2VWR9TDLP" "hV8nQ4xT1mK9rB6cYd2LpW7sJf0zGa3UeXo5NiRt" > "$WEB/config.js" \
    && git add -A && git commit -qm "feat: integración" && git tag "$v")
  if correr "$v" "$TMP/claves/cosign.pub"; then falla "la puerta dejó pasar un secreto"; else ok "la puerta se detuvo"; fi
  verificar_corrida "$v" fallo secretos
  [ ! -e "$REPO/.puerta/${SITE}.tar" ] && ok "no se construyó ninguna imagen" || falla "se construyó una imagen a pesar del secreto"
}

escenario_vulnerable() {
  echo "== Escenario «vulnerable»: imagen base vieja =="
  local v; nueva_version; v="$V"
  (cd "$REPO" && git checkout -q -B vulnerable base && sed -i 's#^FROM .*#FROM nginx:1.14-alpine#' Dockerfile && git commit -qam "build: imagen base" && git tag "$v")
  if correr "$v" "$TMP/claves/cosign.pub"; then falla "la puerta dejó pasar una imagen vulnerable"; else ok "la puerta se detuvo"; fi
  verificar_corrida "$v" fallo vulnerabilidades
}

escenario_firma_ajena() {
  echo "== Escenario «firma-ajena»: se verifica con otra clave pública =="
  local v; nueva_version; v="$V"
  (cd "$REPO" && git checkout -q -B ajena base && echo "<!-- ${v} -->" >> "$WEB/index.html" && git commit -qam "feat: ajuste" && git tag "$v")
  if correr "$v" "$TMP/claves-ajenas/cosign.pub"; then falla "la verificación aceptó una clave ajena"; else ok "la puerta se detuvo"; fi
  verificar_corrida "$v" fallo verificacion
}

case "$ESCENARIO" in
  limpia) escenario_limpia ;;
  secreto) escenario_secreto ;;
  vulnerable) escenario_vulnerable ;;
  firma-ajena) escenario_firma_ajena ;;
  todas) escenario_limpia; escenario_secreto; escenario_vulnerable; escenario_firma_ajena ;;
  *) echo "Escenario desconocido: $ESCENARIO" >&2; exit 2 ;;
esac

echo
if [ "$fallos" -eq 0 ]; then echo "Simulación de la puerta: todo OK"; else echo "Simulación de la puerta: ${fallos} fallo(s)"; exit 1; fi

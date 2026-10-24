#!/usr/bin/env bash
# Demo de cierre de la spec 006 (T24): recorre la demo y comprueba los criterios CA-1 a CA-7.
#   1. En El Tornillo, subir una versión con una contraseña: la puerta falla en «secretos», la solicitud queda
#      «rechazada» y el cliente lee el texto del glosario.
#   2. Subir una versión limpia: pasa los seis controles, se aprueba en el Hub y se escribe en hub-gitops.
#   3. Abrir la evidencia guardada (SBOM) de la versión publicada.
#   4. Un Pod root en el namespace del cliente es rechazado (solo si hay clúster; ver gitops/pruebas/pod-security.sh).
#
# Uso:  HUB_PASSWORD='<contraseña>' GITEA_ADMIN_USER=forja-admin GITEA_ADMIN_PASSWORD='<contraseña>' \
#         bash gitops/pruebas/demo-006.sh
# Antes: el runner registrado y los repos sembrados (pipelines/README.md), El Tornillo en una versión que ya pasó la
# puerta. Variables opcionales: HUB (http://hub.local), GITEA (http://gitea.hub.local), ORG (forja-digital),
# HUB_USUARIO (sofia@forjadigital.test), CLIENTE_USUARIO (contacto@eltornillo.test), LIMITE (segundos de espera, 420).
# Deja en Gitea dos etiquetas nuevas (v9.<hora>) y, si se aprueba, un commit en hub-gitops: para volver atrás,
# `git revert` de ese commit (ver gitops/pruebas/ciclo-gitops.sh).
set -uo pipefail

HUB="${HUB:-http://hub.local}"
GITEA="${GITEA:-http://gitea.hub.local}"
ORG="${ORG:-forja-digital}"
HUB_USUARIO="${HUB_USUARIO:-sofia@forjadigital.test}"
CLIENTE_USUARIO="${CLIENTE_USUARIO:-contacto@eltornillo.test}"
LIMITE="${LIMITE:-420}"
: "${HUB_PASSWORD:?Falta HUB_PASSWORD (la contraseña de los usuarios sembrados)}"
: "${GITEA_ADMIN_USER:?Falta GITEA_ADMIN_USER}"
: "${GITEA_ADMIN_PASSWORD:?Falta GITEA_ADMIN_PASSWORD}"

# La raíz del repo, calculada antes de entrar a la carpeta temporal del sitio
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

fallos=0
ok()    { echo "   OK   $1"; }
falla() { echo "   FALLA $1"; fallos=$((fallos+1)); }
campo() { sed -n "s/.*\"$1\": *\"\{0,1\}\([^\",}]*\)\"\{0,1\}.*/\1/p" | head -1; }
codigo() { curl -s -m 15 -o /dev/null -w '%{http_code}' "$@"; }

entrar() {  # entrar <correo> → token del Hub
  curl -s -m 10 -H 'Content-Type: application/json' -X POST "${HUB}/api/auth/login" \
    -d "{\"email\":\"$1\",\"password\":\"${HUB_PASSWORD}\"}" | campo access_token
}
TOKEN="$(entrar "$HUB_USUARIO")"
TOKEN_CLIENTE="$(entrar "$CLIENTE_USUARIO")"
[ -n "$TOKEN" ] && [ -n "$TOKEN_CLIENTE" ] || { echo "No se pudo entrar al Hub (¿HUB_PASSWORD correcta?)"; exit 1; }
hub()    { curl -s -m 20 -H "Authorization: Bearer ${TOKEN}" -H 'Content-Type: application/json' "$@"; }
hub_cli() { curl -s -m 20 -H "Authorization: Bearer ${TOKEN_CLIENTE}" "$@"; }

autorizacion="Authorization: Basic $(printf '%s:%s' "$GITEA_ADMIN_USER" "$GITEA_ADMIN_PASSWORD" | base64 | tr -d '\n')"
git_gitea() { git -c "http.extraheader=${autorizacion}" -c user.name="Demo 006" -c user.email="demo@forjadigital.test" "$@"; }

SERVICIO="$(hub "${HUB}/api/services/status" | tr '{' '\n' | grep '"cliente-ferreteria"' | campo service_id)"
[ -n "$SERVICIO" ] && ok "servicio de El Tornillo: #${SERVICIO}" || { falla "no se encontró El Tornillo en ${HUB}"; exit 1; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
sello="$(date +%H%M%S)"
git_gitea clone -q "${GITEA%/}/${ORG}/ferreteria.git" "$TMP/sitio" 2>/dev/null || { falla "no se pudo clonar ${ORG}/ferreteria"; exit 1; }
cd "$TMP/sitio" || exit 1
BASE="$(git tag --sort=version:refname | head -1)"   # la primera versión: una base conocida y limpia
[ -n "$BASE" ] || { falla "el repositorio no tiene versiones (¿se sembró con pipelines/sembrar-repos-sitios.sh?)"; exit 1; }

# Estado de la puerta de un cambio y control que falló: el primero que aparece es el de la versión, no el de un control
estado_puerta() { hub "${HUB}/api/change-requests/$1/checks" | grep -o '"status":"[a-z_]*","failed_step":[^,]*' | head -1 | sed 's/.*"status":"\([a-z_]*\)".*/\1/'; }
control_fallido() { hub "${HUB}/api/change-requests/$1/checks" | grep -o '"failed_step":"[a-z_]*"' | head -1 | sed 's/.*:"\(.*\)"/\1/'; }

pedir_cambio() {  # pedir_cambio <versión> → deja en CAMBIO_ULTIMO y TICKET_ULTIMO los ids
  TICKET_ULTIMO="$(hub -X POST "${HUB}/api/tickets" -d "{\"service_id\":${SERVICIO},\"title\":\"Publicar ${1}\",\"description\":\"Demo de la puerta de seguridad\",\"kind\":\"cambio\"}" | campo id)"
  RESPUESTA_ULTIMA="$(hub -X POST "${HUB}/api/change-requests" -d "{\"ticket_id\":${TICKET_ULTIMO},\"to_version\":\"${1}\"}")"
  CAMBIO_ULTIMO="$(echo "$RESPUESTA_ULTIMA" | campo id)"
}

esperar() {  # esperar "<descripción>" <comando que devuelve 0 cuando se cumple>
  local limite=$(( $(date +%s) + LIMITE ))
  while [ "$(date +%s)" -lt "$limite" ]; do eval "$2" && return 0; sleep 5; done
  falla "se acabó el tiempo esperando: $1"; return 1
}

echo "== 1. Una versión con una contraseña (CA-1, CA-5) =="
MALA="v9.${sello}a"
pedir_cambio "$MALA"; CAMBIO_MALO="$CAMBIO_ULTIMO"; TICKET_MALO="$TICKET_ULTIMO"
[ -n "$CAMBIO_MALO" ] && ok "cambio #${CAMBIO_MALO} hacia ${MALA} en pendiente" || { falla "no se creó el cambio: ${RESPUESTA_ULTIMA:0:200}"; exit 1; }
git checkout -q -b "demo-mala-${sello}" "$BASE"
printf 'const aws = "AKIA%s";\nconst token = "%s";\n' "Z3MQ7XK2VWR9TDLP" "hV8nQ4xT1mK9rB6cYd2LpW7sJf0zGa3UeXo5NiRt" > src/config.js
git add -A && git_gitea commit -q -m "feat: integración con el proveedor" && git tag "$MALA" && git_gitea push -q origin "$MALA" 2>/dev/null \
  && ok "versión ${MALA} subida a Gitea" || { falla "no se pudo subir ${MALA}"; exit 1; }
esperar "que la solicitud ${CAMBIO_MALO} se rechace" '[ "$(estado_puerta "${CAMBIO_MALO}")" = "fallo" ]' && {
  [ "$(control_fallido "${CAMBIO_MALO}")" = "secretos" ] \
    && ok "la puerta falló en «secretos»" || falla "la puerta no falló en «secretos»"
  estado="$(hub "${HUB}/api/change-requests" | tr '{' '\n' | grep "\"id\":${CAMBIO_MALO}," | campo status)"
  [ "$estado" = "rechazada" ] && ok "la solicitud quedó «rechazada»" || falla "la solicitud quedó «${estado}»"
  [ "$(codigo -H "Authorization: Bearer ${TOKEN}" -H 'Content-Type: application/json' -X POST "${HUB}/api/change-requests/${CAMBIO_MALO}/approve")" = "409" ] \
    && ok "aprobarla ya no es posible (409)" || falla "se pudo aprobar una versión rechazada"
  vista="$(hub_cli "${HUB}/api/tickets/${TICKET_MALO}")"
  echo "$vista" | grep -q "Una actualización fue detenida porque contenía información sensible." \
    && ok "el cliente lee el texto del glosario" || falla "el cliente no ve el texto del glosario"
  echo "$vista" | grep -qi "gitleaks\|secretos en el c\|corrida" && falla "el cliente ve jerga técnica" || ok "el cliente no ve jerga técnica"
}

echo "== 2. Una versión limpia pasa los controles y se publica (CA-2, CA-3, CA-4) =="
BUENA="v9.${sello}b"
pedir_cambio "$BUENA"; CAMBIO_BUENO="$CAMBIO_ULTIMO"
[ -n "$CAMBIO_BUENO" ] && ok "cambio #${CAMBIO_BUENO} hacia ${BUENA} en pendiente" || { falla "no se creó el cambio: ${RESPUESTA_ULTIMA:0:200}"; exit 1; }
git checkout -q -b "demo-buena-${sello}" "$BASE"
echo "<!-- ${BUENA} -->" >> src/index.html
git add -A && git_gitea commit -q -m "feat: ajuste menor del sitio" && git tag "$BUENA" && git_gitea push -q origin "$BUENA" 2>/dev/null \
  && ok "versión ${BUENA} subida a Gitea" || { falla "no se pudo subir ${BUENA}"; exit 1; }
[ "$(codigo -H "Authorization: Bearer ${TOKEN}" -H 'Content-Type: application/json' -X POST "${HUB}/api/change-requests/${CAMBIO_BUENO}/approve")" = "409" ] \
  && ok "mientras corren los controles, aprobar responde 409 (CA-6)" || echo "   (la corrida ya había terminado: se omite la comprobación de 409)"
esperar "que la puerta termine en ok" '[ "$(estado_puerta "${CAMBIO_BUENO}")" = "ok" ]' && {
  ok "la puerta terminó en «ok»"
  checks="$(hub "${HUB}/api/change-requests/${CAMBIO_BUENO}/checks")"
  n="$(echo "$checks" | grep -o '"step":"' | wc -l | tr -d ' ')"
  [ "$n" = "6" ] && ok "seis controles registrados (secretos, construcción, vulnerabilidades, SBOM, firma, verificación)" || falla "hay ${n} controles, se esperaban 6"
  aprobado="$(hub -X POST "${HUB}/api/change-requests/${CAMBIO_BUENO}/approve")"
  SHA="$(echo "$aprobado" | campo gitops_commit_sha)"
  [ "$(echo "$aprobado" | campo status)" = "en_validacion" ] && ok "aprobado: commit ${SHA:0:7} en hub-gitops" || falla "no se pudo aprobar: ${aprobado:0:200}"
  if [ -n "$SHA" ]; then
    commit="$(curl -s -m 10 "${GITEA%/}/api/v1/repos/${ORG}/hub-gitops/git/commits/${SHA}")"
    echo "$commit" | grep -q "versión ${BUENA}" && ok "el commit existe en Gitea y dice «versión ${BUENA}»" || falla "no se encontró el commit en hub-gitops"
  fi
}

echo "== 3. La evidencia queda guardada (CA-4) =="
ID_SBOM="$(hub "${HUB}/api/change-requests/${CAMBIO_BUENO}/checks" | tr '{' '\n' | grep '"step":"sbom"' | campo id)"
if [ -n "$ID_SBOM" ]; then
  reporte="$(hub "${HUB}/api/security-checks/${ID_SBOM}/report")"
  # Sin `echo | grep -q`: con pipefail, grep cierra la tubería a mitad de un SBOM de varios MB y el echo falla
  [[ "$reporte" == *spdxVersion* ]] && ok "el SBOM (SPDX) se descarga desde el Hub" || falla "el reporte del SBOM no es un SPDX"
else
  falla "no hay control de SBOM en la corrida"
fi

echo "== 4. Pod root rechazado por la plataforma (CA-7) =="
if command -v kubectl >/dev/null 2>&1 && kubectl get ns cliente-ferreteria >/dev/null 2>&1; then
  bash "$RAIZ/gitops/pruebas/pod-security.sh" ferreteria >/dev/null 2>&1 && ok "el Pod con root fue rechazado" || falla "Pod Security dejó pasar un Pod root"
else
  echo "   (sin clúster a la mano: se omite; corre gitops/pruebas/pod-security.sh ferreteria donde esté k3s)"
fi

echo
if [ "$fallos" -eq 0 ]; then echo "Demo de la spec 006: todo OK"; else echo "Demo de la spec 006: ${fallos} fallo(s)"; exit 1; fi

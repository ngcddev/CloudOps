#!/usr/bin/env bash
# Túneles del clúster local hacia el Hub del VPS (spec 011, T18). Abre túneles rápidos de Cloudflare hacia Gitea,
# Argo CD y Prometheus del clúster k3d-hub, comprueba que respondan y arma las variables que el Hub del VPS necesita
# en el Environment de Dokploy. Los tokens salen de los Secrets del clúster, no se imprimen (se muestran con
# asteriscos) y el bloque completo queda en el portapapeles. No escribe nada en disco.
#
# Uso (desde la raíz del repo, en Git Bash, con el contexto k3d-hub):
#   CLOUDFLARED="/ruta/a/cloudflared.exe" bash gitops/pruebas/tuneles-vps.sh
# Déjelo corriendo mientras dure la demo: al cerrarlo (Ctrl+C) se apagan los túneles. Cada corrida da URLs nuevas;
# si se reinicia hay que actualizar las variables en Dokploy y volver a desplegar.
#
# AVISO: mientras los túneles estén abiertos, Gitea, Argo CD y Prometheus son accesibles desde internet con la
# URL aleatoria. Solo hay datos de laboratorio, pero ciérrelos apenas termine.
set -uo pipefail

CLOUDFLARED="${CLOUDFLARED:-cloudflared}"
CONTEXTO="k3d-hub"
PUERTO_PROM="${PUERTO_PROM:-9090}"
PIDS=()
LOGS=""

limpiar() {
  trap - INT TERM EXIT
  echo
  echo "Cerrando túneles y port-forward..."
  for pid in "${PIDS[@]:-}"; do [ -n "$pid" ] && kill "$pid" 2>/dev/null; done
  # Respaldo en Windows: los procesos nativos no siempre atienden el kill de Git Bash
  nombre="$(basename "$CLOUDFLARED")"; taskkill //F //IM "${nombre%.exe}.exe" >/dev/null 2>&1 || true
  [ -n "$LOGS" ] && rm -rf "$LOGS"
  exit 0
}
trap limpiar INT TERM EXIT

if ! command -v "$CLOUDFLARED" >/dev/null 2>&1 && [ ! -x "$CLOUDFLARED" ]; then
  echo "No se encontró cloudflared. Indique la ruta: CLOUDFLARED=\"/ruta/cloudflared.exe\" bash $0"; exit 1
fi
if [ "$(kubectl config current-context 2>/dev/null)" != "$CONTEXTO" ]; then
  echo "El contexto de kubectl no es $CONTEXTO (kubectl config use-context $CONTEXTO)"; exit 1
fi
LOGS="$(mktemp -d)"

URL=""
# Abre un túnel y deja su URL en la variable URL. Con tercer argumento, reescribe el Host (Traefik enruta por nombre).
abrir_tunel() {
  local nombre="$1" destino="$2" host="${3:-}" log="$LOGS/$1.log"
  URL=""
  if [ -n "$host" ]; then
    "$CLOUDFLARED" tunnel --no-autoupdate --url "$destino" --http-host-header "$host" >"$log" 2>&1 &
  else
    "$CLOUDFLARED" tunnel --no-autoupdate --url "$destino" >"$log" 2>&1 &
  fi
  PIDS+=("$!")
  for _ in $(seq 1 30); do
    URL="$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' "$log" | head -1)"
    [ -n "$URL" ] && return 0
    sleep 2
  done
  echo "   FALLA no se obtuvo la URL del túnel de ${nombre}. Últimas líneas de su registro:"
  tail -5 "$log" | cut -c1-200
  return 1
}

# Espera a que una URL responda 200 (el nombre nuevo tarda unos segundos en resolverse)
probar() {
  local nombre="$1" url="$2" ruta="$3" codigo=""
  for _ in $(seq 1 20); do
    codigo="$(curl -s -o /dev/null -m 8 -w '%{http_code}' "${url}${ruta}")"
    if [ "$codigo" = "200" ]; then echo "   OK   ${nombre}: ${url}"; return 0; fi
    sleep 3
  done
  echo "   FALLA ${nombre} no responde 200 en ${url}${ruta} (último código: ${codigo:-sin respuesta})"
  return 1
}

secreto() { kubectl -n "$1" get secret "$2" -o "jsonpath={.data.$3}" 2>/dev/null | base64 -d; }

fallos=0
echo "== Abriendo túneles =="
abrir_tunel gitea  http://localhost:80 gitea.hub.local  && URL_GITEA="$URL"  || exit 1
abrir_tunel argocd http://localhost:80 argocd.hub.local && URL_ARGOCD="$URL" || exit 1

# Prometheus solo existe dentro del clúster: se expone con un port-forward local
kubectl -n monitoring port-forward svc/prometheus "${PUERTO_PROM}:9090" >"$LOGS/portforward.log" 2>&1 &
PIDS+=("$!")
for _ in $(seq 1 15); do
  curl -s -o /dev/null -m 2 "http://localhost:${PUERTO_PROM}/-/ready" && break
  sleep 1
done
abrir_tunel prometheus "http://localhost:${PUERTO_PROM}" && URL_PROM="$URL" || exit 1

echo "== Comprobando que respondan =="
probar "Gitea"      "$URL_GITEA"  "/api/v1/version" || fallos=$((fallos + 1))
probar "Argo CD"    "$URL_ARGOCD" "/api/version"    || fallos=$((fallos + 1))
probar "Prometheus" "$URL_PROM"   "/-/ready"        || fallos=$((fallos + 1))
[ "$fallos" -eq 0 ] || { echo "Algún túnel no respondió; no se arma el bloque."; exit 1; }

TOKEN_GITEA="$(secreto hub hub-gitops-tokens GITEA_TOKEN)"
TOKEN_ARGOCD="$(secreto hub hub-gitops-tokens ARGOCD_TOKEN)"
TOKEN_ALERTAS="$(secreto monitoring hub-alertmanager token)"
TOKEN_PIPELINE="$(secreto hub hub-pipeline PIPELINE_TOKEN)"
for nombre in TOKEN_GITEA TOKEN_ARGOCD TOKEN_ALERTAS TOKEN_PIPELINE; do
  [ -n "${!nombre}" ] || { echo "   FALLA no se pudo leer ${nombre} de los Secrets del clúster"; exit 1; }
done

BLOQUE="GITEA_URL=${URL_GITEA}
GITEA_PUBLIC_URL=${URL_GITEA}
GITEA_TOKEN=${TOKEN_GITEA}
ARGOCD_URL=${URL_ARGOCD}
ARGOCD_TOKEN=${TOKEN_ARGOCD}
PROMETHEUS_URL=${URL_PROM}
ALERTMANAGER_TOKEN=${TOKEN_ALERTAS}
PIPELINE_TOKEN=${TOKEN_PIPELINE}"

echo
echo "== Variables para el Environment del servicio cloudops en Dokploy =="
echo "$BLOQUE" | sed -E 's/^([A-Z]+_TOKEN)=.*/\1=********/'
if printf '%s\n' "$BLOQUE" | clip 2>/dev/null || printf '%s\n' "$BLOQUE" | clip.exe 2>/dev/null; then
  echo
  echo "El bloque completo (con los tokens) quedó en el portapapeles: péguelo en Dokploy y luego haga Deploy."
else
  echo "No se pudo copiar al portapapeles; ejecute los comandos de cada token a mano."
fi
echo
echo "Túneles abiertos. Déjelos corriendo; Ctrl+C los cierra."

# Vigilancia: avisa una sola vez si un túnel o el port-forward se cae
caido=""
while true; do
  sleep 20
  for i in "${!PIDS[@]}"; do
    if ! kill -0 "${PIDS[$i]}" 2>/dev/null && [[ "$caido" != *"|$i|"* ]]; then
      caido="${caido}|$i|"
      echo "$(date +%H:%M:%S) AVISO: se cayó uno de los procesos (túnel o port-forward) #$i; reinicie el script y actualice Dokploy."
    fi
  done
done

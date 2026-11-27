#!/usr/bin/env bash
# Instalador de CloudOps Client Hub desde cero hasta http://hub.local (Windows con Docker Desktop, en Git Bash).
# Uso, desde la raíz del repositorio:   bash infra/instalar.sh              (instala, o continúa donde quedó)
#                                       bash infra/instalar.sh --comprobar  (solo revisa requisitos, no cambia nada)
# Claves: opcionales en .env.cluster (GITEA_ADMIN_PASSWORD y SEED_USER_PASSWORD; letras y números, 12 o más). Lo que falte se genera.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
ESTADO=.instalacion-estado
HOSTS=/c/Windows/System32/drivers/etc/hosts
NOMBRES="hub.local restaurante.hub.local ferreteria.hub.local consultorio.hub.local gitea.hub.local argocd.hub.local grafana.hub.local mlflow.hub.local backstage.hub.local ferreteria-staging.hub.local colegio.hub.local"
K3D=ghcr.io/k3d-io/k3d:5.8.3

morir() { echo "ERROR: $1" >&2; exit 1; }
k3d_run() { MSYS_NO_PATHCONV=1 docker run --rm -v /var/run/docker.sock:/var/run/docker.sock "$@"; }

# ---------- Requisitos ----------
for c in docker git kubectl curl ollama; do command -v "$c" >/dev/null 2>&1 || morir "falta '$c' en el PATH"; done
python -c "import sys" >/dev/null 2>&1 || morir "falta Python 3 (el comando 'python' debe funcionar)"
docker info >/dev/null 2>&1 || morir "Docker Desktop no está en ejecución"
ollama list >/dev/null 2>&1 || morir "Ollama no está abierto"
# Protección: nunca tocar un clúster que no haya creado este instalador
if docker inspect k3d-hub-server-0 >/dev/null 2>&1 && [ ! -f "$ESTADO" ]; then
  morir "ya existe un clúster k3d-hub que no creó este instalador: no se toca nada"
fi
if [ ! -f "$ESTADO" ] && curl -s -m 3 http://127.0.0.1:80 >/dev/null 2>&1; then
  morir "el puerto 80 está ocupado (cierra XAMPP, Apache o IIS)"
fi
echo "Requisitos: OK"
[ "${1:-}" = "--comprobar" ] && exit 0
touch "$ESTADO"

# ---------- Claves ----------
aleatoria() { head -c 96 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | cut -c1-24; }
touch .env.cluster
sed -i 's/\r$//' .env.cluster
set -a; . ./.env.cluster; set +a
asegurar() {  # asegurar <variable> <valor por defecto>
  if [ -z "${!1:-}" ]; then
    sed -i "/^$1=/d" .env.cluster
    printf '\n%s=%s\n' "$1" "$2" >> .env.cluster
    export "$1=$2"
  fi
}
asegurar GITEA_ADMIN_USER forja-admin
asegurar GITEA_ADMIN_PASSWORD "$(aleatoria)"
asegurar SEED_USER_PASSWORD "$(aleatoria)"
for v in GITEA_ADMIN_PASSWORD SEED_USER_PASSWORD; do
  [[ "${!v}" =~ ^[A-Za-z0-9]{12,}$ ]] || morir "$v debe tener solo letras y números, 12 o más"
done
export GITEA_USER="$GITEA_ADMIN_USER" GITEA_PASSWORD="$GITEA_ADMIN_PASSWORD"
export REGISTRY_USER="$GITEA_ADMIN_USER" REGISTRY_PASSWORD="$GITEA_ADMIN_PASSWORD"
export KUBECONFIG="$(cygpath -m "$HOME")/.kube/k3d-hub.yaml"

# ---------- Pasos (cada uno se ejecuta una vez; si falla, se vuelve a lanzar el instalador) ----------
paso() {  # paso <función> <título>
  if grep -qx "$1" "$ESTADO"; then echo "== $2 (ya hecho)"; return; fi
  echo; echo "== $2"
  "$1"
  echo "$1" >> "$ESTADO"
}

modelos() { ollama pull qwen2.5:7b-instruct; ollama pull nomic-embed-text; }

tiene_nombre() { tr -d '\r' < "$HOSTS" | grep -v '^[[:space:]]*#' | grep -qE "[[:space:]]${1//./\.}([[:space:]]|$)"; }

nombres() {
  local n faltan=""
  for n in $NOMBRES; do tiene_nombre "$n" || faltan="$faltan $n"; done
  [ -z "$faltan" ] && return 0
  echo "Windows pedirá permiso de administrador para editar el archivo hosts."
  # El cambio va en un archivo temporal de PowerShell: así no hay problemas de comillas al elevar permisos
  printf 'Add-Content -Path "$env:SystemRoot/System32/drivers/etc/hosts" -Value ([Environment]::NewLine + "127.0.0.1%s")\r\n' "$faltan" > .agregar-hosts.ps1
  powershell.exe -NoProfile -Command "Start-Process powershell -Verb RunAs -Wait -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File',('\"' + (Resolve-Path .agregar-hosts.ps1).Path + '\"')" || true
  rm -f .agregar-hosts.ps1
  tiene_nombre gitea.hub.local || morir "no se actualizó hosts. Agrega a mano esta línea: 127.0.0.1$faltan"
}

cluster() {
  docker network inspect k3d-hub >/dev/null 2>&1 || docker network create k3d-hub --subnet 172.30.0.0/24 --gateway 172.30.0.1 >/dev/null
  if ! docker inspect k3d-hub-server-0 >/dev/null 2>&1; then
    k3d_run -v "$(pwd -W)/gitops/platform/k3s/registries.yaml:/cfg/registries.yaml:ro" "$K3D" cluster create hub \
      --image rancher/k3s:v1.32.9-k3s1 --network k3d-hub -p "80:80@loadbalancer" -p "443:443@loadbalancer" \
      --registry-config /cfg/registries.yaml --host-alias "172.30.0.1:gitea.hub.local" --wait
  fi
  mkdir -p "$HOME/.kube"
  k3d_run "$K3D" kubeconfig get hub > "$KUBECONFIG"
  local puerto; puerto="$(docker port k3d-hub-serverlb 6443 | head -1 | sed 's/.*://')"
  sed -i "s#server: .*#server: https://127.0.0.1:${puerto}#" "$KUBECONFIG"
  kubectl wait --for=condition=Ready node --all --timeout=180s
}

gitea() {
  kubectl apply -f gitops/platform/namespaces.yaml
  kubectl apply -k gitops/platform/gitea
  kubectl -n gitea rollout status deploy/gitea --timeout=600s
  if ! kubectl -n gitea exec deploy/gitea -- gitea admin user list | grep -qw "$GITEA_ADMIN_USER"; then
    kubectl -n gitea exec deploy/gitea -- gitea admin user create --admin --username "$GITEA_ADMIN_USER" \
      --password "$GITEA_ADMIN_PASSWORD" --email admin@forja.test --must-change-password=false >/dev/null
  fi
  for _ in $(seq 1 60); do curl -sf -m 5 http://gitea.hub.local/api/healthz >/dev/null && return 0; sleep 5; done
  morir "Gitea no responde en gitea.hub.local"
}

claves() {
  # La contraseña de los usuarios se fija antes; crear-secretos.sh respeta lo que ya existe y genera el resto al azar
  kubectl -n hub get secret hub-auth >/dev/null 2>&1 || kubectl -n hub create secret generic hub-auth \
    --from-literal=JWT_SECRET="$(aleatoria)$(aleatoria)" --from-literal=SEED_USER_PASSWORD="$SEED_USER_PASSWORD"
  bash gitops/hub/crear-secretos.sh
  bash pipelines/configurar-gitea.sh --rotar-claves    # claves de firma nuevas y organización de Gitea
}

imagenes() {
  bash apps/publicar-imagenes.sh
  bash apps/publicar-imagenes.sh ferreteria:v1.1
  bash apps/publicar-imagenes.sh hub-api hub-web hub-voz mlflow colegio-web colegio-api
}

argocd() {
  kubectl apply -k gitops/platform/argocd --server-side --force-conflicts
  kubectl -n argocd rollout status deploy/argocd-server --timeout=600s
  for _ in $(seq 1 60); do curl -sf -m 5 http://argocd.hub.local/healthz >/dev/null && return 0; sleep 5; done
  morir "Argo CD no responde en argocd.hub.local"
}

gitops() {
  bash gitops/platform/gitea/sembrar-hub-gitops.sh
  bash gitops/hub/crear-tokens.sh
  bash gitops/sincronizar-hub-gitops.sh --limpiar
}

desplegar() {
  local a=gitops/platform/argocd/applications f
  kubectl apply -k "$a"
  for f in hub monitoring plataforma-mlops plataforma-respaldo plataforma-backstage; do kubectl apply -f "$a/$f.yaml"; done
  kubectl apply -f gitops/platform/politicas/
  echo "Esperando a que todo quede Synced y Healthy (hasta 20 min)..."
  for _ in $(seq 1 120); do
    local estado; estado="$(kubectl get applications -n argocd --no-headers 2>/dev/null || true)"
    if [ -n "$estado" ] && ! echo "$estado" | awk '$2!="Synced" || $3!="Healthy"' | grep -q .; then return 0; fi
    sleep 10
  done
  kubectl get applications -n argocd
  morir "hay aplicaciones sin sanar; revisa 'kubectl get pods -A' y vuelve a lanzar el instalador"
}

ia() { bash gitops/hub/configurar-ia.sh http://host.docker.internal:11434 rag; }

puerta() {
  export GITEA_INSTANCE_URL=http://gitea.hub.local
  export GITEA_RUNNER_REGISTRATION_TOKEN="$(curl -s -u "$GITEA_ADMIN_USER:$GITEA_ADMIN_PASSWORD" http://gitea.hub.local/api/v1/admin/runners/registration-token | sed -n 's/.*"token":"\([^"]*\)".*/\1/p')"
  docker compose -f pipelines/runner/docker-compose.yml up -d --build
  # Sin etiquetas: la puerta corre una sola vez, en el paso de datos
  bash pipelines/sembrar-repos-sitios.sh --sin-etiquetas restaurante ferreteria consultorio colegio
}

datos() { bash demo/dejar-demo-lista.sh; }

paso modelos   "1/10 Modelos de IA (descarga grande)"
paso nombres   "2/10 Nombres *.hub.local"
paso cluster   "3/10 Clúster k3d"
paso gitea     "4/10 Gitea"
paso claves    "5/10 Secretos y claves de firma"
paso imagenes  "6/10 Imágenes (lo más lento)"
paso argocd    "7/10 Argo CD"
paso gitops    "8/10 Repositorio GitOps y tokens"
paso desplegar "9/10 Hub, sitios y plataforma, con IA y puerta de seguridad"
paso ia        "      Conexión con Ollama"
paso puerta    "      Runner y repositorios de los sitios"
paso datos     "10/10 Datos de demostración"

# El registro en MLflow es complementario: si falla, el Hub sigue funcionando con la compuerta de su imagen
if MSYS_NO_PATHCONV=1 docker run --rm --add-host mlflow.hub.local:host-gateway -e MLFLOW_TRACKING_URI=http://mlflow.hub.local \
     -v "$(pwd -W):/repo" -w /repo python:3.12-slim sh -c "pip install -q -r ai/requirements.txt && python ai/classifier/train.py --promover"; then
  echo "Compuerta registrada en MLflow."
else
  echo "AVISO: no se pudo registrar la compuerta en MLflow."
fi

printf '%s' "$SEED_USER_PASSWORD" | clip.exe
echo
echo "LISTO: http://hub.local   usuario: sofia@forjadigital.test"
echo "La contraseña quedó en el portapapeles (pégala con Ctrl+V). Las claves están en .env.cluster."

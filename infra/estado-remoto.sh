#!/usr/bin/env bash
# Estado remoto de OpenTofu con bloqueo (spec 016). SeaweedFS hace de almacén S3 en el laboratorio (MinIO ya no publica imágenes);
# en producción basta cambiar `endpoints` en backend_remoto.tf.example por el S3 de la nube.
#   iniciar   levanta SeaweedFS (contenedor `estado-remoto` en la red k3d-hub) y crea el bucket `tofu-estado`; las credenciales se generan y
#             quedan en infra/.estado-remoto.env (ignorado por Git)
#   probar    prueba el backend de infra/tofu/backend_remoto.tf.example en una carpeta temporal: aplica, comprueba que el estado quedó en el
#             bucket y que un segundo `apply` simultáneo es rechazado por el bloqueo. No toca el estado real
#   activar   copia el backend a infra/tofu/backend_override.tf y migra el estado local al bucket
#   parar     detiene el almacén (el volumen conserva el estado)
# Uso:  bash infra/estado-remoto.sh <iniciar|probar|activar|parar>
set -euo pipefail
AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$AQUI/.estado-remoto.env"
RED="${NETWORK:-k3d-hub}"
S3_IMAGE="${S3_IMAGE:-chrislusf/seaweedfs:latest}"
AWS_CLI_IMAGE="${AWS_CLI_IMAGE:-amazon/aws-cli:latest}"
TOFU_IMAGE="ghcr.io/opentofu/opentofu:1.13.2"
export MSYS_NO_PATHCONV=1
paso() { echo "→ $1"; }
ruta_docker() { (cd "$1" && (pwd -W 2>/dev/null || pwd)); }

cargar() { [ -f "$ENV_FILE" ] || { echo "Falta $ENV_FILE: corre primero «iniciar»." >&2; exit 1; }; set -a; . "$ENV_FILE"; set +a; }

tofu() { # carpeta args…  (corre en la red del almacén, con las credenciales en el entorno)
  local carpeta="$1"; shift
  docker run --rm --network "$RED" -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -v "$(ruta_docker "$carpeta"):/w" -w /w "$TOFU_IMAGE" "$@"
}

aws_s3() { # argumentos de `aws`
  docker run --rm --network "$RED" -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_DEFAULT_REGION=us-east-1 "$AWS_CLI_IMAGE" --endpoint-url http://estado-remoto:8333 "$@"
}

iniciar() {
  docker network inspect "$RED" >/dev/null 2>&1 || docker network create "$RED" >/dev/null
  if [ ! -f "$ENV_FILE" ]; then
    printf 'AWS_ACCESS_KEY_ID=tofu%s\nAWS_SECRET_ACCESS_KEY=%s\n' "$(head -c6 /dev/urandom | od -An -tx1 | tr -d ' \n')" "$(head -c24 /dev/urandom | od -An -tx1 | tr -d ' \n')" > "$ENV_FILE"
    chmod 600 "$ENV_FILE" 2>/dev/null || true
  fi
  cargar
  docker rm -f estado-remoto >/dev/null 2>&1 || true
  paso "Levantando SeaweedFS (estado-remoto)"
  local cfg; cfg="$(mktemp -d)"
  printf '{"identities":[{"name":"tofu","credentials":[{"accessKey":"%s","secretKey":"%s"}],"actions":["Admin","Read","Write","List"]}]}' \
    "$AWS_ACCESS_KEY_ID" "$AWS_SECRET_ACCESS_KEY" > "$cfg/s3.json"
  docker volume create estado_remoto_datos >/dev/null
  docker run -d --name estado-remoto --network "$RED" --restart unless-stopped --memory 384m \
    -v estado_remoto_datos:/data -v "$(ruta_docker "$cfg"):/cfg:ro" \
    "$S3_IMAGE" server -dir=/data -s3 -s3.port=8333 -s3.config=/cfg/s3.json >/dev/null
  for _ in $(seq 1 40); do
    aws_s3 s3 mb s3://tofu-estado >/dev/null 2>&1 && break
    aws_s3 s3 ls s3://tofu-estado >/dev/null 2>&1 && break
    sleep 2
  done
  aws_s3 s3 ls s3://tofu-estado >/dev/null 2>&1 && echo "   bucket tofu-estado listo" || { echo "   FALLA no se pudo crear el bucket" >&2; return 1; }
}

probar() {
  cargar
  local tmp; tmp="$(mktemp -d)"
  cp "$AQUI/tofu/backend_remoto.tf.example" "$tmp/backend.tf"
  sed -i 's#cloudops/terraform.tfstate#prueba/terraform.tfstate#' "$tmp/backend.tf"
  cat > "$tmp/main.tf" <<'TF'
resource "terraform_data" "demo" { input = "estado remoto" }
output "listo" { value = terraform_data.demo.id != "" }
TF
  paso "init con el backend S3"
  tofu "$tmp" init -input=false >/dev/null && echo "   OK   init"
  paso "apply"
  tofu "$tmp" apply -auto-approve -input=false >/dev/null && echo "   OK   apply"
  paso "el estado quedó en el bucket"
  aws_s3 s3 ls s3://tofu-estado/prueba/ | grep -q terraform.tfstate && echo "   OK   tofu-estado/prueba/terraform.tfstate" || { echo "   FALLA no está el estado" >&2; return 1; }
  [ ! -f "$tmp/terraform.tfstate" ] && echo "   OK   no hay estado local" || { echo "   FALLA hay estado local" >&2; return 1; }
  paso "el bloqueo impide dos apply a la vez"
  # un apply lento toma el bloqueo; un segundo apply debe fallar con «Error acquiring the state lock»
  cat > "$tmp/main.tf" <<'TF'
resource "terraform_data" "lento" {
  triggers_replace = timestamp()
  provisioner "local-exec" { command = "sleep 25" }
}
TF
  tofu "$tmp" apply -auto-approve -input=false >/dev/null 2>&1 &
  local pid=$!
  sleep 15
  local segundo; segundo="$(tofu "$tmp" apply -auto-approve -input=false -lock-timeout=3s 2>&1 || true)"
  if echo "$segundo" | grep -qi "acquiring the state lock"; then
    echo "   OK   el segundo apply fue rechazado por el bloqueo"
  else
    echo "   FALLA el segundo apply no se bloqueó:" >&2; echo "$segundo" | tail -8 >&2; wait "$pid" || true; return 1
  fi
  wait "$pid" || true
  rm -rf "$tmp"
  echo "Estado remoto: funciona con bloqueo."
}

activar() {
  cargar
  cp "$AQUI/tofu/backend_remoto.tf.example" "$AQUI/tofu/backend_override.tf"
  paso "Migrando el estado local a tofu-estado"
  tofu "$AQUI/tofu" init -migrate-state -force-copy -input=false
}

case "${1:-}" in
  iniciar) iniciar ;;
  probar) probar ;;
  activar) activar ;;
  parar) docker stop estado-remoto ;;
  *) echo "Uso: bash infra/estado-remoto.sh <iniciar|probar|activar|parar>" >&2; exit 2 ;;
esac

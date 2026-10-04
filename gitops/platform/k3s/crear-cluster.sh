#!/usr/bin/env bash
# Crea el clúster de desarrollo con k3d (spec 003, T05): k3s fijado en 1.32, puertos 80/443, el
# registro de Gitea por HTTP y `gitea.hub.local` visible desde dentro del nodo.
# En el PC A se instala k3s directamente: ahí basta copiar registries.yaml a /etc/rancher/k3s/ y
# poner gitea.hub.local en el /etc/hosts del nodo.
set -euo pipefail
cd "$(dirname "$0")"

SUBNET=172.30.0.0/24
GATEWAY=172.30.0.1   # el host de Docker, donde están publicados los puertos 80/443

# Red con dirección fija, para poder apuntar gitea.hub.local al host de Docker
docker network inspect k3d-hub >/dev/null 2>&1 || docker network create k3d-hub --subnet "$SUBNET" --gateway "$GATEWAY"

k3d cluster create hub \
  --image rancher/k3s:v1.32.9-k3s1 \
  --network k3d-hub \
  -p "80:80@loadbalancer" -p "443:443@loadbalancer" \
  --registry-config ./registries.yaml \
  --host-alias "$GATEWAY:gitea.hub.local" \
  --kubeconfig-update-default --kubeconfig-switch-context

echo "Listo. Si kubectl no conecta, ajusta el servidor del kubeconfig a 127.0.0.1 (ver gitops/README.md)."

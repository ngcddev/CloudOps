#!/usr/bin/env bash
# Enciende la VM del Hub y espera a que la API de Kubernetes responda (spec 024, T13).
set -euo pipefail
: "${GCP_PROJECT:?Define GCP_PROJECT (ID del proyecto)}"
ZONA="${GCP_ZONE:-us-central1-a}"
gcloud compute instances start hub --zone "$ZONA" --project "$GCP_PROJECT"
IP="$(gcloud compute instances describe hub --zone "$ZONA" --project "$GCP_PROJECT" --format='get(networkInterfaces[0].accessConfigs[0].natIP)')"
echo "VM encendida en $IP; esperando HTTPS…"
for _ in $(seq 1 60); do
  if curl -ksf -o /dev/null "https://${IP//./-}.sslip.io/"; then echo "Hub responde."; exit 0; fi
  sleep 10
done
echo "El Hub no respondió en 10 minutos." >&2
exit 1

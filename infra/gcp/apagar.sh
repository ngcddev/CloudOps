#!/usr/bin/env bash
# Apaga la VM del Hub para no gastar crédito; el disco y la IP estática se conservan (spec 024, T13).
set -euo pipefail
: "${GCP_PROJECT:?Define GCP_PROJECT (ID del proyecto)}"
ZONA="${GCP_ZONE:-us-central1-a}"
gcloud compute instances stop hub --zone "$ZONA" --project "$GCP_PROJECT"
echo "VM apagada. El disco (50 GB) y la IP estática siguen cobrando centavos; para empezar de cero usa tofu destroy."

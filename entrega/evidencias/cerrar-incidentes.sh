#!/usr/bin/env bash
# Cierra por la API los incidentes mitigados que dejó una verificación (cronometro.sh deja los suyos «mitigados» a propósito) para que la siguiente demo pueda abrir uno nuevo del mismo
# servicio: la huella de la alerta es única entre incidentes abiertos. Es el camino normal de la consola (POST /close con la causa raíz). Uso: bash entrega/evidencias/cerrar-incidentes.sh
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"
PW="$(kubectl -n hub get secret hub-auth -o jsonpath='{.data.SEED_USER_PASSWORD}' | base64 -d)"
TOK="$(curl -s -m 10 -H 'Content-Type: application/json' -X POST http://hub.local/api/auth/login -d "{\"email\":\"sofia@forjadigital.test\",\"password\":\"$PW\"}" | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")"
curl -s -m 10 -H "Authorization: Bearer $TOK" http://hub.local/api/incidents | python -c "
import sys,json
for i in json.load(sys.stdin):
    if i.get('status') != 'cerrado': print(i['id'], i.get('status'))" | while read -r id estado; do
  printf '%s -> ' "#$id ($estado)"
  curl -s -m 10 -H "Authorization: Bearer $TOK" -H 'Content-Type: application/json' -X POST "http://hub.local/api/incidents/$id/close" -d '{"root_cause":"Caida provocada a proposito por una verificacion automatica (cronometro); se cierra para dejar la demo limpia."}' | python -c "import sys,json; d=json.load(sys.stdin); print(d.get('status') or d.get('detail'))"
done

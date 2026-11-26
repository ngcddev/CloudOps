#!/usr/bin/env bash
# Deja la demo del clúster lista después de las verificaciones con efecto (fallas provocadas, cambios y reversiones): base del Hub limpia con los datos semilla, las versiones v1, v1.1 y v2 de los
# sitios vueltas a pasar por la puerta de seguridad (la base nueva no las conoce), los tres sitios en su versión base v1, el índice del asistente reconstruido y todo comprobado.
# Uso: KUBECONFIG=... bash demo/dejar-demo-lista.sh        (credenciales de .env.cluster y de los Secret del clúster; no escribe secretos en ningún archivo)
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"
set -a; . ./.env.cluster; set +a
export GITEA_USER="$GITEA_ADMIN_USER" GITEA_PASSWORD="$GITEA_ADMIN_PASSWORD"
fallos=0
ok() { echo "   OK   $1"; }
falla() { echo "   FALLA $1"; fallos=$((fallos + 1)); }

echo "== 1. Reiniciar la demo (base del Hub con los datos semilla)"
bash demo/reiniciar-cluster.sh || falla "reiniciar-cluster.sh terminó con error"

echo "== 2. Volver a pasar v1, v1.1 y v2 de los sitios por la puerta de seguridad"
bash demo/resembrar-puerta.sh || falla "resembrar-puerta.sh terminó con error"
PW="$(kubectl -n hub get secret hub-auth -o jsonpath='{.data.SEED_USER_PASSWORD}' | base64 -d)"
login() { curl -s -m 10 -H 'Content-Type: application/json' -X POST http://hub.local/api/auth/login -d "{\"email\":\"sofia@forjadigital.test\",\"password\":\"$PW\"}" | python -c "import sys,json;print(json.load(sys.stdin).get('access_token',''))"; }
TOK="$(login)"
for _ in $(seq 1 90); do
  r=""; for s in 1 2 3; do n="$(curl -s -m 10 -H "Authorization: Bearer $TOK" "http://hub.local/api/services/$s/security-runs" | python -c "import sys,json; print(sum(1 for r in json.load(sys.stdin) if (r.get('status') or r.get('result'))=='ok'))" 2>/dev/null)"; r="$r ${n:-0}"; done
  [ "$r" = " 2 3 2" ] && break; sleep 10
done
[ "$r" = " 2 3 2" ] && ok "puerta en «ok» (restaurante, ferreteria, consultorio):$r" || falla "la puerta no terminó:$r"

echo "== 3. Sitios en su versión base v1"
for c in ferreteria restaurante consultorio; do bash demo/restaurar-v1.sh "$c" 2>&1 | tail -1; done
for c in restaurante ferreteria consultorio; do
  v="$(curl -s -m 8 "http://$c.hub.local/health" | sed -n 's/.*"version":"\([^"]*\)".*/\1/p')"
  [ "$v" = "v1" ] && ok "$c reporta v1" || falla "$c reporta '${v}'"
done

echo "== 4. Índice del asistente (RAG)"
TOK="$(login)"
curl -s -m 120 -H "Authorization: Bearer $TOK" -X POST http://hub.local/api/assistant/reindex | head -c 300; echo

echo "== 5. Comprobación final"
kubectl get applications -n argocd --no-headers | awk '{print "   "$1,$2,$3}'
[ "$(kubectl get applications -n argocd --no-headers | awk '$2!="Synced" || $3!="Healthy"' | wc -l)" = "0" ] && ok "todas las Applications Synced y Healthy" || falla "hay Applications que no están Synced y Healthy"
curl -s -m 10 -H "Authorization: Bearer $TOK" http://hub.local/api/incidents | python -c "import sys,json; l=json.load(sys.stdin); print('   incidentes en la base:', len(l))"
curl -s -m 10 -H "Authorization: Bearer $TOK" http://hub.local/api/change-requests | python -c "import sys,json; l=json.load(sys.stdin); print('   solicitudes de cambio en la base:', len(l))"
[ -n "$TOK" ] && ok "inicio de sesión en el Hub" || falla "no se pudo iniciar sesión en el Hub"
echo "fallos: $fallos"
exit "$fallos"

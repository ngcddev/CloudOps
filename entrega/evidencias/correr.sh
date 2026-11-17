#!/usr/bin/env bash
# Reproduce el paquete de evidencias de la entrega final (spec 023): corre cada verificación con paso.sh y deja salida, código y duración en entrega/evidencias/<fecha>_<commit>/.
# Uso:  bash entrega/evidencias/correr.sh <nivel...>     (A, B, C, D, E, F; por ejemplo:  correr.sh A B)
# Los niveles C (con efecto) cambian el clúster; al terminar hay que correr  bash demo/reiniciar-cluster.sh  (el nivel F lo hace). Las credenciales salen de .env y .env.cluster.
set -u
# Ojo: NO exportar MSYS_NO_PATHCONV a todo (rompe curl -o /dev/null y git con carpetas temporales en Git Bash); solo se pone en los docker que montan rutas.
cd "$(git rev-parse --show-toplevel)"
# La corrida se fija en entrega/evidencias/CORRIDA (una corrida larga cruza la medianoche UTC); si no existe se crea con la fecha y el commit de hoy
[ -f entrega/evidencias/CORRIDA ] || echo "$(date -u +%Y-%m-%d)_$(git rev-parse --short HEAD)" > entrega/evidencias/CORRIDA
CARPETA=${CARPETA:-entrega/evidencias/$(cat entrega/evidencias/CORRIDA)}
# En Git Bash, kubectl.exe necesita la ruta en formato Windows con barras (C:/Users/...): los scripts que fijan MSYS_NO_PATHCONV no la convierten y kubectl cae a localhost:8080
export KUBECONFIG=${KUBECONFIG:-$(cygpath -m "$HOME/.kube/k3d-hub.yaml" 2>/dev/null || echo "$HOME/.kube/k3d-hub.yaml")}
RAIZ_DOCKER=$(pwd -W 2>/dev/null || pwd)
P="bash entrega/evidencias/paso.sh $CARPETA"
mkdir -p "$CARPETA"

nivel_A() {
  $P A A01-ruff "Lint de Python (ruff 0.14.0, ruff.toml; entrega/ queda fuera: es el borrador sin versionar)" -- env MSYS_NO_PATHCONV=1 docker run --rm -v "$RAIZ_DOCKER:/w" -w /w python:3.12-slim sh -c "pip install -q ruff==0.14.0 2>&1 | tail -1 && ruff check . --exclude entrega"
  $P A A02-frontend "Frontend: npm ci, tsc --noEmit y build (Node 22)" -- env MSYS_NO_PATHCONV=1 docker run --rm -v "$RAIZ_DOCKER/frontend:/src:ro" -v "$RAIZ_DOCKER/seed:/w/seed:ro" node:22 sh -c "mkdir -p /w && cp -r /src /w/frontend && cd /w/frontend && rm -rf node_modules && npm ci --no-audit --no-fund && npx tsc --noEmit && npm run build"
  $P A A03-conteo-pruebas "Conteo real de pruebas del backend (pytest --collect-only)" -- docker compose exec -T api pytest --collect-only -q
  $P A A04-validar-observabilidad "promtool, amtool y kustomize sobre la observabilidad" -- bash observability/pruebas/validar.sh
  $P A A05-grafana "Grafana carga el tablero aprovisionado" -- bash observability/pruebas/grafana.sh
  $P A A06-trazas "Spans de OpenTelemetry llegan a Tempo" -- bash observability/pruebas/trazas.sh
  $P A A07-helm-vs-kustomize "El chart de Helm coincide con Kustomize" -- bash gitops/pruebas/helm-vs-kustomize.sh
  $P A A08-psa-restringido "Los manifiestos del Hub cumplen PSA restricted" -- bash -c "kubectl kustomize gitops/hub | MSYS_NO_PATHCONV=1 docker run -i --rm -v \"$RAIZ_DOCKER/gitops/pruebas:/p:ro\" python:3.12-slim sh -c \"pip install -q pyyaml 2>&1 | tail -1; python /p/psa_restringido.py\""
  $P A A09-sincronizador "Lógica del sincronizador hub-gitops (repositorios falsos)" -- bash gitops/pruebas/sincronizar-prueba.sh
  $P A A10-drift-opentofu "Drift de OpenTofu (plan -detailed-exitcode)" -- bash infra/pruebas/drift.sh
  $P A A11-analisis-estatico "bandit, trivy fs y escaneo de la imagen web" -- bash pipelines/pruebas/analisis-estatico.sh
  $P A A12-hallazgos "Trivy cruzado con hallazgos.yaml y generación del VEX" -- bash pipelines/pruebas/hallazgos.sh
  $P A A13-humo-hub-api "Imagen de producción de la API: sin root, sin pytest, migra y responde" -- bash pipelines/pruebas/humo-hub-api.sh
  $P A A14-smoke-colegio "Smoke del sitio del colegio" -- bash apps/colegio/smoke-test.sh
  $P A A15-smoke-consultorio "Smoke del sitio del consultorio" -- bash apps/consultorio/smoke-test.sh
  $P A A16-smoke-landing "Smoke de la plantilla landing-form" -- bash apps/templates/landing-form/smoke-test.sh
}

nivel_B() {
  mkdir -p "$CARPETA/B"
  $P B B00-reconstruir-api "Reconstruir la imagen dev de la API (incluye las pruebas nuevas) y levantar compose" -- docker compose up -d --build --wait api web db
  $P B B01-pytest-configuracion-real "pytest completo con el modo del .env (ASSISTANT_CONTEXT_MODE del equipo), JUnit guardado" -- env MSYS_NO_PATHCONV=1 bash -c "docker compose exec -T api pytest -q -rs --junitxml=/tmp/junit.xml; rc=\$?; docker compose cp api:/tmp/junit.xml $CARPETA/B/junit-modo-env.xml; exit \$rc"
  $P B B02-pytest-modo-completo "pytest completo forzando ASSISTANT_CONTEXT_MODE=completo (como lo corre el CI)" -- env MSYS_NO_PATHCONV=1 bash -c "docker compose exec -T -e ASSISTANT_CONTEXT_MODE=completo api pytest -q -rs --junitxml=/tmp/junit.xml; rc=\$?; docker compose cp api:/tmp/junit.xml $CARPETA/B/junit-modo-completo.xml; exit \$rc"
  $P B B03-pytest-postgres "Pruebas que necesitan PostgreSQL desechable (concurrencia del índice y menores del backend)" -- bash -c "docker rm -f pg-prueba >/dev/null 2>&1; docker run -d --rm --name pg-prueba --network cw-cloudops_default -e POSTGRES_PASSWORD=prueba -e POSTGRES_DB=prueba postgres:16-alpine >/dev/null && until docker exec pg-prueba pg_isready -U postgres >/dev/null 2>&1; do sleep 1; done; sleep 2; docker compose exec -T -e TEST_POSTGRES_URL=postgresql+psycopg://postgres:prueba@pg-prueba:5432/prueba api pytest -q -rs tests/test_knowledge_concurrente.py tests/test_menores_backend.py; rc=\$?; docker rm -f pg-prueba >/dev/null 2>&1; exit \$rc"
  $P B B04-pytest-ai "Pruebas de ai/ (promoción, registro en MLflow, tutor, medición)" -- env MSYS_NO_PATHCONV=1 docker run --rm -u 0 --entrypoint sh -v "$RAIZ_DOCKER:/w:ro" -w /tmp cw-cloudops-api -c "cp -r /w/ai /w/backend /tmp/ && cd /tmp/ai && pip install -q -r requirements.txt 2>&1 | tail -1; python -m pytest -q -p no:cacheprovider"
  $P B B05-respaldo-restauracion "Respaldo y restauración de PostgreSQL, tabla por tabla" -- bash gitops/pruebas/respaldo.sh
  $P B B06-puerta-de-seguridad "Los 9 escenarios de la puerta de seguridad (secretos, CVE, firma, procedencia SLSA…)" -- bash -c "set -a; . ./.env; set +a; HUB_URL=http://localhost:8000 HUB_PIPELINE_TOKEN=\$PIPELINE_TOKEN bash pipelines/pruebas/simular-puerta.sh todas"
  $P B B07-acceso-y-bitacora "Acceso por rol y bitácora de auditoría (spec 007)" -- bash -c "set -a; . ./.env; set +a; HUB=http://localhost:8000 HUB_PASSWORD=\$SEED_USER_PASSWORD bash gitops/pruebas/demo-007.sh"
}

# Credenciales del clúster: salen de los Secret y de .env.cluster; nunca se escriben en un archivo ni en el registro (paso.sh las tapa)
preparar_clúster() {
  export HUB_PASSWORD="$(kubectl -n hub get secret hub-auth -o jsonpath='{.data.SEED_USER_PASSWORD}' | base64 -d)"
  export PASO_SECRETOS_EXTRA="$HUB_PASSWORD"
  set -a; . ./.env.cluster; set +a
  export GITEA_USER="$GITEA_ADMIN_USER" GITEA_PASSWORD="$GITEA_ADMIN_PASSWORD"
}

# C1: el clúster solo se lee (no cambia nada)
nivel_C1() {
  preparar_clúster
  $P C C01-aplicaciones "Applications de Argo CD: sincronía y salud" -- kubectl get applications -n argocd
  $P C C02-imagenes-desplegadas "Imágenes desplegadas en hub y clientes" -- bash -c "kubectl get deploy,cronjob,statefulset -A -o jsonpath='{range .items[*]}{.metadata.namespace}{\"/\"}{.metadata.name}{\"\t\"}{.spec.template.spec.containers[*].image}{.spec.jobTemplate.spec.template.spec.containers[*].image}{\"\n\"}{end}' | sort"
  $P C C03-pods-y-recursos "Pods, nodos y uso de recursos" -- bash -c "kubectl get nodes -o wide; kubectl get pods -A; kubectl top nodes; kubectl top pods -A"
  $P C C04-sincronia-hub-gitops "hub-gitops coincide con el repositorio principal" -- bash gitops/pruebas/sincronia.sh
  $P C C05-appproject "AppProject de clientes y Pods sin token de la API" -- bash gitops/pruebas/appproject.sh
  $P C C06-pod-security "Pod Security Admission en un cliente" -- bash gitops/pruebas/pod-security.sh
  $P C C07-aislamiento-red "Un cliente no alcanza a otro" -- bash gitops/pruebas/aislamiento-red.sh
  $P C C08-salida-red "Salida de red cerrada de un cliente" -- bash gitops/pruebas/salida-red.sh
  $P C C09-salida-hub "Salida de red del Hub (controles)" -- bash gitops/pruebas/salida-hub.sh
  $P C C10-entrada-gitea "Entrada de red a Gitea" -- bash gitops/pruebas/entrada-gitea.sh
  $P C C11-entrada-mlops "Entrada de red a MLflow" -- bash gitops/pruebas/entrada-mlops.sh
  $P C C12-entrada-observabilidad "Entrada de red a la observabilidad" -- bash observability/pruebas/entrada.sh
  $P C C13-readiness "Readiness de un cliente" -- bash gitops/pruebas/readiness.sh
  $P C C14-admision "Política de admisión de imágenes (en cliente-restaurante)" -- env SITIO=restaurante bash gitops/pruebas/admision.sh
  $P C C15-capacidad "Informe de cuota, uso y margen por cliente" -- bash observability/capacidad.sh
  $P C C16-prometheus-reglas "Reglas y alertas cargadas en Prometheus" -- bash -c "kubectl -n monitoring exec deploy/prometheus -- wget -qO- 'http://localhost:9090/api/v1/rules' | python -c \"import sys,json; d=json.load(sys.stdin)['data']['groups']; print('grupos:',len(d),'reglas:',sum(len(g['rules']) for g in d)); [print(' ',g['name'],len(g['rules']),'reglas') for g in d]\"; kubectl -n monitoring exec deploy/prometheus -- wget -qO- 'http://localhost:9090/api/v1/alerts'"
  $P C C17-demo-003 "Criterios de la spec 003: plataforma del clúster" -- bash gitops/pruebas/demo.sh
}

# C2: pruebas que provocan fallas y cambios reales en el clúster (al final hay que reiniciar la demo: nivel F)
nivel_C2() {
  preparar_clúster
  $P C C20-drift-selfheal "Argo CD corrige un cambio a mano (selfHeal)" -- bash gitops/pruebas/drift.sh
  $P C C21-ciclo-gitops "Cambio de versión por Gitea y revert" -- bash gitops/pruebas/ciclo-gitops.sh
  $P C C22-demo-005 "Aprobación de un cambio hasta el sitio publicado (spec 005)" -- bash gitops/pruebas/demo-005.sh
  $P C C23-demo-006 "Puerta de seguridad en el runner de Gitea (spec 006)" -- env GITEA_ADMIN_USER="$GITEA_ADMIN_USER" GITEA_ADMIN_PASSWORD="$GITEA_ADMIN_PASSWORD" bash gitops/pruebas/demo-006.sh
  $P C C24-demo-010 "Dashboards con Prometheus (spec 010)" -- bash gitops/pruebas/demo-010.sh
  $P C C25-caso-restaurante "P1 del restaurante: incidente, rollback y MTTR" -- bash gitops/pruebas/demo-caso-restaurante.sh
  $P C C26-cronometro "El incidente P1 se abre en 60 s o menos" -- bash observability/pruebas/cronometro.sh
  $P C C27-publicacion-sana "Una publicación sana no abre incidente" -- bash observability/pruebas/publicacion-sana.sh
  $P C C28-simulaciones "Caída de réplica, latencia y saturación" -- env SITIO=restaurante bash gitops/pruebas/simulaciones.sh todas
  $P C C29-respaldo-plataforma "Respaldo de Gitea y Argo CD fuera del nodo" -- env DESTINO="$CARPETA/C/respaldos-plataforma" bash gitops/pruebas/respaldo-plataforma.sh
  $P C C30-crear-cliente "Crear, verificar y eliminar un cliente con OpenTofu" -- bash infra/pruebas/crear-cliente.sh
}

# C3: repetición ordenada de las demos que dependen de un estado de partida (ferreteria en v1) o de un script que había quedado atrás
nivel_C3() {
  preparar_clúster
  export GITEA_TOKEN="$(kubectl -n hub get secret hub-gitops-tokens -o jsonpath='{.data.GITEA_TOKEN}' | base64 -d)"
  export PASO_SECRETOS_EXTRA="$HUB_PASSWORD"$'\n'"$GITEA_TOKEN"
  $P C C18-reiniciar-hub "Reiniciar la demo del clúster: base del Hub limpia (las repeticiones previas dejaron cambios en curso)" -- bash demo/reiniciar-cluster.sh
  $P C C18b-resembrar-puerta "Volver a correr la puerta de seguridad de v1, v1.1 y v2 de los sitios (la base del Hub quedó vacía tras el reinicio)" -- bash entrega/evidencias/resembrar-puerta.sh
  $P C C19a-restaurar-ferreteria "Dejar ferreteria en v1 (estado de partida de las demos)" -- bash entrega/evidencias/restaurar-v1.sh ferreteria
  $P C C21-ciclo-gitops "Cambio de versión por Gitea y revert" -- bash gitops/pruebas/ciclo-gitops.sh
  $P C C22-demo-005 "Aprobación de un cambio hasta el sitio publicado (spec 005)" -- bash gitops/pruebas/demo-005.sh
  $P C C19b-restaurar-ferreteria "Volver ferreteria a v1 tras demo-005" -- bash entrega/evidencias/restaurar-v1.sh ferreteria
  $P C C27-publicacion-sana "Una publicación sana no abre incidente" -- bash observability/pruebas/publicacion-sana.sh
  $P C C19c-restaurar-ferreteria "Volver ferreteria a v1 tras la publicación sana" -- bash entrega/evidencias/restaurar-v1.sh ferreteria
  $P C C26-cronometro "El incidente P1 se abre en 60 s o menos (3 corridas)" -- bash observability/pruebas/cronometro.sh
  $P C C23b-cerrar-incidentes "Cerrar los incidentes mitigados que dejó el cronómetro (la huella es única entre incidentes abiertos)" -- bash entrega/evidencias/cerrar-incidentes.sh
  $P C C24-demo-010 "Dashboards con Prometheus, incluida la caída de Prometheus (spec 010)" -- bash gitops/pruebas/demo-010.sh
  $P C C29b-tofu-init "tofu init del directorio infra/tofu (proveedores)" -- env K3D_BIN="$PWD/entrega/evidencias/shims/k3d" bash infra/tofu.sh tofu init -input=false
  $P C C30-crear-cliente "Crear, verificar y eliminar un cliente con OpenTofu (k3d no instalado: shim que devuelve el kubeconfig del mismo clúster)" -- env PYTHON=python K3D_BIN="$PWD/entrega/evidencias/shims/k3d" bash infra/pruebas/crear-cliente.sh
}

# D: IA, voz y navegador. Los scripts de ai/ escriben sus corridas en ai/eval/runs y ai/tutor/runs; para no tocar el árbol de trabajo (ya hay corridas del 14 y 15 nov versionadas) se ejecutan en un
# contenedor sobre una copia del repositorio y la salida se copia a la carpeta de la corrida. Ollama corre en el equipo (host.docker.internal:11434).
en_contenedor() {   # en_contenedor <subcarpeta-de-salida> <comando dentro de /tmp>
  local salida="$1"; shift
  mkdir -p "$CARPETA/D/$salida"
  env MSYS_NO_PATHCONV=1 docker run --rm -u 0 -e DATABASE_URL=sqlite:///evaluacion.db -e JWT_SECRET="evaluacion-$(python -c 'import secrets;print(secrets.token_hex(24))')" --entrypoint sh -v "$RAIZ_DOCKER:/w:ro" -v "$RAIZ_DOCKER/$CARPETA/D/$salida:/out" -w /tmp cw-cloudops-api \
    -c "cp -r /w/ai /w/backend /tmp/ && rm -rf /tmp/ai/eval/runs/* /tmp/ai/tutor/runs/* 2>/dev/null; mkdir -p /tmp/ai/eval/runs /tmp/ai/tutor/runs; export PYTHONPATH=/tmp/backend; cd /tmp; $*; rc=\$?; cp -r /tmp/ai/eval/runs/. /out/ 2>/dev/null; cp -r /tmp/ai/tutor/runs/. /out/ 2>/dev/null; exit \$rc"
}
export -f en_contenedor; export CARPETA RAIZ_DOCKER   # paso.sh corre cada comando en un bash hijo: necesita ver la función y las variables
OLL="http://host.docker.internal:11434"
nivel_D() {
  preparar_clúster
  $P D D01-digests-modelos "Los digests de los modelos de Ollama y la suma de la compuerta coinciden con sus fichas" -- python ai/verificar_modelos.py
  local modo conj
  for modo in completo rag; do
    for conj in ayuda ayuda_ciegas inyeccion exfiltracion; do
      arch="preguntas_${conj}.jsonl"; [ "$conj" = "ayuda" ] && arch="preguntas_ayuda.jsonl"
      $P D "D02-eval-${modo}-${conj}" "Evaluación del asistente (qwen2.5:7b-instruct, contexto ${modo}, conjunto ${conj})" -- en_contenedor "eval-${modo}-${conj}" "python ai/eval/run_eval.py --modelo qwen2.5:7b-instruct --url $OLL --contexto $modo --archivo ai/eval/$arch"
    done
  done
  $P D D03-borradores "Borradores de incidente: 10 casos, términos prohibidos y órdenes escondidas" -- en_contenedor borradores "python ai/eval/run_eval_borradores.py --url $OLL"
  $P D D04-documento-malicioso "Órdenes escondidas en la ayuda: 5 documentos maliciosos" -- en_contenedor malicioso "python ai/eval/probar_documento_malicioso.py --url $OLL"
  $P D D05-secretos-en-prompt "8 secretos pegados en una pregunta: no llegan al modelo ni a la respuesta" -- en_contenedor secretos "python ai/eval/probar_secretos_en_prompt.py --url $OLL"
  $P D D06-latencia-memoria "Latencia, velocidad y memoria de los modelos de Ollama" -- en_contenedor medicion "python ai/eval/medir_modelos.py --url $OLL"
  $P D D07-tutor "Tutor del módulo 2: matriz de aciertos, omisiones y alucinaciones" -- en_contenedor tutor "python ai/tutor/evaluar.py --url $OLL"
}

nivel_D2() {   # voz y navegador: levanta el servicio de voz de compose y lo apaga al terminar
  $P D D10-voz-arranque "Levantar el servicio de voz (faster-whisper y Piper, CPU)" -- docker compose --profile voz up -d --wait voz
  $P D D11-voz-evaluacion "Error de palabras, latencia y memoria de la voz sin micrófono" -- python ai/eval/evaluar_voz.py --url http://localhost:8100 --contenedor cw-cloudops-voz-1
  $P D D12-voz-navegador "La voz en un navegador real con micrófono falso (Playwright)" -- bash -c "set -a; . ./.env; set +a; SALIDA=\"$PWD/$CARPETA/D/capturas-voz\" HUB_USUARIO=sofia@forjadigital.test HUB_PASSWORD=\"\$SEED_USER_PASSWORD\" bash voz/pruebas/voz-ui.sh"
  $P D D13-voz-apagado "Apagar el servicio de voz (volver al estado inicial)" -- docker compose --profile voz stop voz
}

nivel_D3() {   # Backstage en un navegador real (clúster)
  preparar_clúster
  $P D D14-backstage-navegador "Backstage: plantilla de sitio y TechDocs en un navegador real" -- bash -c "SALIDA=\"$PWD/$CARPETA/D/capturas-backstage\" bash gitops/pruebas/backstage-ui.sh"
}

nivel_F() {
  $P F F01-clon-limpio "Clonar dev de GitHub, levantar con compose y ensayar el runbook (arranque, pruebas, reinicio, degradación, apagado)" -- bash entrega/evidencias/clon-limpio.sh
  $P F F02-repositorio "Ramas, PR, issues, etiquetas, última corrida del CI y archivos de contribución del repositorio" -- bash -c "echo '--- remoto'; git remote -v | head -1; echo '--- ramas remotas'; git branch -r | wc -l; echo '--- últimas corridas del CI en dev'; gh run list --branch dev --limit 5; echo '--- PR (conteo)'; gh pr list --state all --limit 500 --json number | python -c 'import sys,json; print(len(json.load(sys.stdin)))'; echo '--- issues abiertos y cerrados'; gh issue list --state all --limit 500 --json number | python -c 'import sys,json; print(len(json.load(sys.stdin)))'; echo '--- etiquetas'; git tag | wc -l; echo '--- archivos de contribución'; ls LICENSE NOTICE CONTRIBUTING.md CODE_OF_CONDUCT.md 2>&1; echo '--- protección de ramas'; gh api repos/ngcddev/CloudOps/branches/dev/protection 2>&1 | head -3"
  $P F F03-reinicio-hub "Runbook: reinicio de un servicio del Hub en el clúster (rollout restart del web) y tiempo hasta estar sano" -- bash -c "t=\$(date +%s); kubectl -n hub rollout restart deploy/web >/dev/null && kubectl -n hub rollout status deploy/web --timeout=180s && echo \"web reiniciado y sano en \$(( \$(date +%s) - t )) s\"; curl -sk -m 10 -o /dev/null -w 'hub.local/health: %{http_code}\n' https://hub.local/health"
}

nivel_E() {
  preparar_clúster
  mkdir -p "$CARPETA/E/capturas"
  $P E E01-recorrido-ui "Recorrido de la interfaz con un navegador real: Hub (agencia y portal), Argo CD, Grafana, MLflow y Gitea, con capturas" -- env SALIDA="$PWD/$CARPETA/E/capturas" bash entrega/evidencias/recorrido-ui.sh
}

nivel_Z() {
  preparar_clúster
  $P Z Z01-dejar-demo-lista "Dejar la demo del clúster lista: base limpia, puerta de seguridad vuelta a correr, sitios en v1, índice del asistente y comprobación final" -- bash entrega/evidencias/dejar-demo-lista.sh
}

for n in "$@"; do "nivel_$n"; done
echo "Resultados en $CARPETA/resultados.tsv"

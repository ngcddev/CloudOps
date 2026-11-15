# Checklist de verificación pendiente (módulos 2 al 6)

Lo que se construyó pero no se comprobó del todo, con el paso a paso para cerrarlo. Marca cada casilla cuando se cumpla el criterio **«OK si»** y anota la fecha y quién lo hizo.
Cuando algo falle, la corrección va a su spec y se deja en la [bitácora](bitacora.md). Origen de cada punto: la sección «Pendiente y no verificado» de cada módulo en la bitácora.

Convenciones: comandos en Git Bash desde la raíz del repositorio; `Claude` = lo puede hacer el asistente; `Equipo` = necesita a una persona (navegador, micrófono, otro equipo).

## 0 · Preparación (una vez)

- [ ] **Entorno encendido.** Docker Desktop y Ollama arriba; si el nodo reinicia en bucle, seguir [runbooks/reinicio-del-cluster.md](../runbooks/reinicio-del-cluster.md).
  ```bash
  export KUBECONFIG=C:/Users/<usuario>/.kube/k3d-hub.yaml
  kubectl get nodes                                   # k3d-hub-server-0 Ready
  kubectl get applications -n argocd                  # todo Synced y Healthy
  kubectl -n hub get pods                             # api, web, voz, postgres, backstage Ready
  docker compose --profile voz up -d --build voz web api    # entorno de desarrollo con voz
  ```
  **OK si:** nodo `Ready`, Pods del namespace `hub` sin reinicios nuevos y las aplicaciones de Argo CD sanas.
- [ ] **Entrada en `hosts`** (Equipo). Como administrador en PowerShell, agregar la línea de [gitops/README.md](../gitops/README.md#direcciones-hosts) a `C:\Windows\System32\drivers\etc\hosts`.
  **OK si:** `https://hub.local` abre la consola (tras aceptar el certificado una vez) y `http://gitea.hub.local` abre Gitea.
- [ ] **Credenciales a la mano.** Hub: `kubectl -n hub get secret hub-auth -o jsonpath='{.data.SEED_USER_PASSWORD}' | base64 -d`. Gitea y demás: `.env.cluster`. Usuarios del Hub: `sofia@forjadigital.test` y `camilo@forjadigital.test` (agencia).

## 1 · Prioridad alta

### 1.1 Sitios de clientes con sistema de archivos de solo lectura (módulo 3, T06) · Claude

Hoy solo se probó en contenedores sueltos y con `dry-run`; en el clúster los sitios siguen sin `readOnlyRootFilesystem`.

- [ ] Estado inicial: `kubectl -n cliente-restaurante get deploy web -o jsonpath='{.spec.template.spec.containers[0].securityContext.readOnlyRootFilesystem}'` está vacío.
- [ ] Publicar por Git (Argo CD toma `hub-gitops`, nadie despliega a mano):
  ```bash
  set -a; . ./.env.cluster; set +a
  GITEA_USER="$GITEA_ADMIN_USER" GITEA_PASSWORD="$GITEA_ADMIN_PASSWORD" bash gitops/platform/gitea/actualizar-hub-gitops.sh gitops/clients/_base gitops/clients/consultorio
  ```
- [ ] Esperar a Argo CD y comprobar cada cliente:
  ```bash
  kubectl get applications -n argocd
  for c in restaurante ferreteria consultorio; do kubectl -n cliente-$c get pods; done
  kubectl -n cliente-restaurante get deploy web -o jsonpath='{.spec.template.spec.containers[0].securityContext.readOnlyRootFilesystem}'   # true
  ```
- [ ] Salud y escritura: `curl http://restaurante.hub.local/health` (con `hosts` o `CURL_HOME`) devuelve `ok`; en el consultorio, enviar el formulario de citas y ver que se guarda (usa `/tmp`).
- [ ] Revisar eventos: `kubectl get events -A --sort-by=.lastTimestamp | tail -20` sin `Failed` ni `BackOff`.

**OK si:** los tres clientes quedan `Synced/Healthy`, `readOnlyRootFilesystem` es `true`, `/health` responde y el formulario del consultorio funciona. **Si falla:** `git revert` del commit en `hub-gitops` y Argo CD los devuelve.

### 1.2 Segregación de funciones y demos con dos cuentas (módulo 3, T05) · Claude

Los scripts se modificaron (piden con Sofía y aprueban con Camilo) pero solo se les pasó `bash -n`; la regla corre en el clúster desde `hub-api:v1.12` sin probarse allí.

- [ ] En el navegador (`https://hub.local`): entrar como Sofía, abrir una solicitud de tipo cambio, pedir un cambio de versión y pulsar **Aprobar** → debe responder que quien pidió no puede aprobarlo (403).
- [ ] Cerrar sesión, entrar como Camilo y aprobar el mismo cambio (si la puerta de seguridad de esa versión está en `ok`) → se aprueba.
- [ ] En **Bitácora**: aparece «Se le negó (segregación de funciones)» del intento de Sofía.
- [ ] Ejecutar los scripts modificados (cada uno exige su propio contexto, ver su encabezado):
  ```bash
  HUB_PASSWORD='…' bash gitops/pruebas/demo-005.sh
  HUB_PASSWORD='…' GITEA_ADMIN_USER=… GITEA_ADMIN_PASSWORD='…' bash gitops/pruebas/demo-006.sh      # también ejercita el runner (1.9)
  HUB_PASSWORD='…' bash gitops/pruebas/demo-caso-restaurante.sh
  GITEA_USER=… GITEA_PASSWORD=… HUB_PASSWORD='…' bash gitops/staging/promover.sh ferreteria
  ```
**OK si:** el 403 y la aprobación de Camilo se ven en pantalla y en la bitácora, y los cuatro scripts terminan sin error (cada uno deja cosas en Gitea o `hub-gitops`: léase su encabezado para volver atrás).

### 1.3 Licencias de las fichas de modelos (módulo 5, T01) · Claude

El índice dice «se verificaron en la página de cada modelo»; solo las de Whisper y Piper se leyeron. Las de Qwen y `nomic-embed-text` están puestas de memoria.

- [ ] Abrir y leer la licencia en: la página de `qwen2.5` en Ollama; Hugging Face `Qwen/Qwen2.5-7B-Instruct` (se espera Apache 2.0) y `Qwen/Qwen2.5-3B-Instruct` (se espera licencia de investigación de Qwen); la página de `nomic-embed-text` en Ollama y `nomic-ai/nomic-embed-text-v1.5` (se espera Apache 2.0).
- [ ] Verificar la licencia de `piper-tts` en la versión instalada: `docker run --rm hub-voz:dev pip show piper-tts` y su página en PyPI (puede ser GPL-3.0).
- [ ] Corregir `docs/modelos/*.md` y la sección «Licencias» de `docs/modelos/README.md` con lo que se lea, y la frase «se verificaron…».

**OK si:** cada ficha cita la licencia leída en su fuente con su dirección y la frase del índice es verdadera.

### 1.4 Voz con una persona real (módulo 6) · Equipo

Todas las cifras son con voz sintetizada; la prueba en navegador usó un micrófono falso.

- [ ] Abrir `https://hub.local` (o `http://localhost:5173`) → **Asistente** → **Hablar**. Dictar, con el micrófono del portátil y con ruido de fondo normal, estas cinco frases y anotar lo que transcribe:
  1. «¿Cómo apruebo un cambio de versión?»
  2. «¿Qué botones tiene un incidente?»
  3. «¿Qué significa la prioridad P1?»
  4. «¿Cómo hago un rollback?»
  5. «¿Qué es el MTTR?»
- [ ] Anotar: ¿cuántas se entendieron sin corregir?, segundos entre soltar «Detener» y ver el texto, y entre «Preguntar» y empezar a oír la respuesta.
- [ ] Repetir con `WHISPER=base` (`docker compose --profile voz up -d --build voz` con la variable) si `small` fue lento o pesado.
- [ ] Probar el permiso: negar el micrófono en el navegador y ver el mensaje; abrir `http://hub.local` por HTTP y ver el aviso de conexión segura.

**OK si:** al menos 4 de 5 frases se entienden sin corregir, la vuelta completa se siente usable (anótese el tiempo) y los avisos de permiso aparecen. **Si no:** considerar `small` fijo, mejorar la pista de vocabulario o la fase 2.

## 2 · Módulo 6: voz

- [ ] **Pronunciación de siglas y palabras en inglés** (Equipo): pedir al asistente algo que mencione «rollback», «SLA», «MTTR» y «Argo CD» y escuchar la respuesta. **OK si:** se entiende; si no, anotar qué palabras y decidir si se sustituyen en `limpiar_para_voz` (`voz/app/main.py`) por una forma fonética.
- [ ] **Turno ocupado** (Claude): dos transcripciones a la vez. `curl` en paralelo a `/api/assistant/voice/transcribe` → una responde 429 y la pantalla muestra «Ya hay una transcripción en curso». **OK si:** no se cae el servicio y el mensaje es claro.
- [ ] **Estabilidad del servicio** (Claude): tras 24 h, `kubectl -n hub get pod -l app=voz` con 0 reinicios y `kubectl -n hub top pod` por debajo de 1,5 GiB.
- [ ] **Fase 2** (decisión del equipo): memoria de la charla y voz frase por frase. Decidir si entra antes del 30 nov.

## 3 · Módulo 5: MLOps y seguridad de la IA

- [ ] **Redacción de secretos con formatos reales** (Claude): ejecutar `redaccion.redactar` sobre una lista de 20 secretos de formatos distintos (tokens de Gitea, claves de Azure, claves SSH, `kubeconfig`, URLs con contraseña) y sobre las 56 preguntas del asistente. **OK si:** cada secreto se tapa o se anota como no cubierto, y **ninguna** de las 56 preguntas legítimas cambia.
- [ ] **Guarda del contexto con órdenes redactadas distinto** (Claude): escribir 10 variantes de órdenes escondidas (en inglés, con otras palabras) y pasarlas por `assistant_context.sospechosa`. **OK si:** se anota qué porcentaje detecta y cuáles pasan; las que pasen se agregan a los patrones o se documentan.
- [ ] **`promover.py` contra el servidor MLflow real** (Claude): con `ai/servidor-mlflow` arriba, `python ai/classifier/train.py --version v2` (con datos de ajuste distintos), luego `python ai/classifier/promover.py --version 2` (debe comparar) y `--rollback`. **OK si:** el candidato peor no se promueve (código 3) y el rollback devuelve la versión anterior en MLflow y en `clasificador.json`.
- [ ] **Deriva en la pantalla** (Equipo): en **Asistente**, hacer 20 preguntas y marcar «No era del Hub» en al menos 3 de 10 que tengan opinión. **OK si:** aparece el aviso «La gente corrigió el … % de las decisiones».
- [ ] **Digests al arrancar** (decisión): hoy se verifican al correr `python ai/verificar_modelos.py`. Correrlo y decidir si se agrega a la demo o al arranque.
  ```bash
  docker run --rm --add-host=host.docker.internal:host-gateway -v "$(pwd -W):/w" -w /w python:3.12-slim python ai/verificar_modelos.py --url http://host.docker.internal:11434
  ```
- [ ] **Conjuntos de evaluación pequeños** (aceptado): 40 y 16 preguntas para el asistente, 24 para la compuerta. Si hay tiempo, ampliarlos antes de la sustentación.

## 4 · Módulo 4: observabilidad, SRE e IaC

- [ ] **Runbooks ejecutados de punta a punta** (Equipo + Claude): seguir cada runbook como lo haría alguien nuevo.
  - `caida-del-sitio` y `rollback`: `bash gitops/pruebas/demo-caso-restaurante.sh` (v2 rota → alerta → incidente → rollback) y revisar que cada paso del runbook coincide con lo que se ve.
  - `respaldo-y-restauracion`: `bash gitops/pruebas/respaldo.sh` y `bash gitops/pruebas/respaldo-plataforma.sh`.
  - `saturacion` y `latencia`: `KUBECONFIG=... bash gitops/pruebas/simulaciones.sh todas`.
  - `reinicio-del-cluster`: solo si se reinicia el PC; anotar si el orden de arranque funcionó.
  **OK si:** ningún comando del runbook falla ni está desactualizado; lo que esté mal se corrige en `runbooks/`.
- [ ] **Tablero RED y USE en el Grafana del clúster** (Equipo): abrir `http://grafana.hub.local` (usuario `admin`, contraseña en `kubectl -n monitoring get secret grafana-admin -o jsonpath='{.data.admin-password}' | base64 -d`) → «RED y USE · sitios y Pods». **OK si:** las 8 gráficas muestran datos (RED necesita tráfico: abrir un sitio unas veces).
- [ ] **Diagnóstico con IA con un incidente real** (Equipo): después de `demo-caso-restaurante.sh`, abrir el incidente en la consola → «Diagnóstico con IA» → «Pedir hipótesis». **OK si:** la respuesta cita evidencia `[E1]…` y no propone cambios a mano. Para ver la evidencia reunida (métricas de Prometheus y líneas de Loki), pedirlo con Ollama apagado: el texto base la lista.
- [ ] **`capacidad.sh --estricto` con un cliente sin margen** (Claude): comprobar el código de salida 1 con un caso forzado (por ejemplo, con una cuota de prueba) y 0 con los clientes actuales.
- [ ] **Alloy tras 24 h** (Claude): `kubectl -n monitoring get pod -l app=alloy` con 0 reinicios. Hoy lleva más de dos horas sin reiniciar.
- [ ] **`drift.sh` y OpenTofu real** (decisión): `infra/pruebas/drift.sh` prueba el mecanismo con un recurso local; la pila real no tiene estado propio. Decidir si se documenta así o si se importa el estado de un cliente.

## 5 · Módulo 3: DevSecOps

- [ ] **Registro de hallazgos como artefacto del CI** (Claude): en GitHub → Actions → última corrida → job «Análisis estático y de composición» → artefacto `registro-de-hallazgos`. **OK si:** trae `hallazgos.md`, `hallazgos.json` y `vex.openvex.json`.
- [ ] **Dependabot** (Equipo): solo actúa en la rama predeterminada (`main`). Tras mezclar `dev` a `main`, mirar en GitHub → Insights → Dependency graph → Dependabot. **OK si:** aparecen las actualizaciones semanales sin errores de configuración.
- [ ] **Excepción KSV-0014 de la plataforma** (registro): vence el 2027-03-31; revisarla antes y cerrar workload por workload. Kyverno o `policy-controller` para verificar la firma en la admisión sigue como mejora.

## 6 · Módulo 2: Kubernetes, GitOps y plataforma

- [ ] **TechDocs** (Claude): `KUBECONFIG=... bash gitops/platform/backstage/publicar-docs.sh` y abrir la documentación en `https://backstage.hub.local`. Decidir si se engancha al CI.
- [ ] **Tutor del módulo 2** (Claude): correr dos veces `python ai/tutor/evaluar.py` y comparar la matriz; anotar la variación entre corridas.
- [ ] **`monitoring` en el proyecto `default` de Argo CD** (decisión): crear su propio AppProject o dejarlo documentado.
- [ ] **DaemonSet de Alloy con más de un nodo** (no verificable en este equipo): anotar como límite del laboratorio.

## 7 · Tandas anteriores (revisar si siguen vigentes)

- [ ] **Flujo del runner de Gitea Actions** (Claude): subir una etiqueta a un repo de sitio y ver correr el workflow en Gitea → Actions. `bash pipelines/sembrar-repos-sitios.sh` crea los repos; `demo-006.sh` lo ejercita. **OK si:** la puerta pasa o falla con su motivo y el Hub la refleja.
- [ ] **Claves de Cosign rotadas:** las versiones firmadas con la clave anterior ya no se verifican. Revisar qué versiones publicadas quedaron así y volver a pasarlas por la puerta (`simular-puerta.sh limpia`) o documentarlo.
- [ ] **Kit offline completo** (Claude): `bash infra/kit-offline.sh exportar kit-offline`, luego `verificar` y `restaurar` en otra carpeta o equipo (pesa varios GB; hay 212 GB libres).
- [ ] **Medir en el PC B de 6 GB** (Equipo): Qwen 7B (5 GB) más embeddings (0,3 GB) y la voz en CPU. En ese equipo: `ollama run qwen2.5:7b-instruct`, `nvidia-smi`, y `python ai/eval/medir_modelos.py`. Mover MLflow allí si se decide.
- [ ] **Revisión de Industrial:** formato del reporte operativo, lenguaje del ejecutivo y textos al cliente. Enviar un PDF de cada tipo y el glosario.
- [ ] **Spans de SQL en las trazas:** siguen fuera por la incompatibilidad con SQLAlchemy 2.1; revisar si hay versión compatible.
- [ ] **Ensayo del guion de 15 minutos** (Equipo): cronometrar la demo completa; la puerta del colegio tarda ≈ 2 min y se lanza en otra terminal.
- [ ] **Pantallas probadas solo por API** (Equipo): recorrer en el navegador los borradores del incidente, los reportes y la deriva.

## 8 · Cierre

- [ ] **Pruebas completas** (Claude):
  ```bash
  docker compose exec -T -e ASSISTANT_CONTEXT_MODE=completo -e OLLAMA_URL= api pytest -q        # backend (845 o más)
  docker run --rm -v "$(pwd -W):/w" -w /w/ai python:3.12-slim sh -c "pip install -q -r requirements.txt pytest && pytest -q"
  bash observability/pruebas/validar.sh && bash pipelines/pruebas/analisis-estatico.sh todo
  (cd frontend && npx tsc --noEmit)
  ```
- [ ] **PR 178** mezclado con el CI en verde, y `dev` mezclado a `main` cuando el equipo lo decida (activa Dependabot).
- [ ] **`docker-compose.dokploy.yml`:** decidir el borrado que está sin commitear.
- [ ] **Bitácora y cumplimiento al día:** marcar aquí lo verificado y mover a la bitácora lo que se corrija.
- [ ] **Plan de producción en la nube y fase 2 de la voz:** decisiones del equipo después de la sustentación o antes del 30 nov.

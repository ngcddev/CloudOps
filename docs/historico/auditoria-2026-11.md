> **Documento histórico** (auditoría técnica del 15 nov 2026; varios hallazgos ya se corrigieron). Se conserva como registro y **no describe el estado actual**. Las cifras vigentes están en el paquete de evidencias de la entrega final (`entrega/evidencias/`).

<!-- Auditoría estática de rendimiento y buenas prácticas del CloudOps Client Hub (15 nov 2026). Solo informa: no corrige nada. -->
# Auditoría de rendimiento y buenas prácticas (15 nov 2026)

> Rama `feat/021-cierre-modulo-6`. Auditoría **estática y de solo lectura**: se leyó el código y los manifiestos; no se levantó
> la aplicación, no se tocó el clúster y no se midió nada en vivo. Lo que habría exigido ejecutar algo está marcado como
> «no verificado». Este documento no corrige nada: cada corrección es una tarea de `tasks.md` que se pide aparte.

## Resumen ejecutivo

| Severidad | Hallazgos | Qué significa |
|---|---|---|
| **Crítico** | 3 | Explotable o con caída posible sin carga especial. Conviene corregirlo antes de la demo. |
| **Medio** | 29 | Degrada rendimiento, mantenimiento o seguridad de forma medible. |
| **Leve** | 52 | Estilo, redundancia o mejora defensiva. |

Cifras tras deduplicar: los tres revisores reportaron 89 hallazgos y cinco eran el mismo problema visto desde distintos lados
(se fusionaron, ver «Fusiones»). Los detalles completos, con archivo, línea y evidencia, están en los anexos:
[BD y backend](auditoria-2026-11/anexo-bd-backend.md) · [frontend y contenedores](auditoria-2026-11/anexo-frontend-contenedores.md) ·
[plataforma](auditoria-2026-11/anexo-plataforma.md).

**Lo más importante en una frase:** el producto está bien construido en control de acceso, contenedores y manifiestos (sin root,
con límites, con sondas), pero tiene tres puntos concretos que arreglar ya y un conjunto de brechas de rendimiento y observabilidad
que hoy no duelen porque los volúmenes son pequeños.

## Rúbrica de severidad
- **Crítico:** pérdida de datos, fallo de seguridad explotable o caída bajo uso normal.
- **Medio:** degrada rendimiento o mantenimiento de forma medible, sin romper nada hoy.
- **Leve:** estilo, redundancia o mejora defensiva.

## Método y límites
- Tres revisiones en paralelo (BD y backend · frontend y contenedores · Kubernetes, observabilidad e IaC) con las skills
  `supabase-postgres-best-practices`, `fastapi`, `python-performance-optimization`, `vercel-react-best-practices`, `web-perf`,
  `web-quality-audit`, `docker-compose-patterns`, `kubernetes-specialist`, `monitoring-expert` y `terraform-skill`; más una pasada de
  seguridad sobre el control de acceso hecha aparte.
- Las skills son guías genéricas de terceros; la severidad final se ajustó al contexto del proyecto (nodo único de 16 GB, demo local).
- La skill `web-design-guidelines` se descarga por URL y no se descargó: sus reglas de interfaz se aplicaron de memoria.
- Los tres hallazgos críticos y el control de acceso se **comprobaron leyendo el código** después del informe de cada revisor.
  Los medios y leves se reportan tal como los dejó el revisor, con su evidencia, sin segunda verificación.

## Críticos

| ID | Dónde | Qué pasa | Estado de la verificación |
|---|---|---|---|
| **CT-01** | `docker-compose.yml:16,80` | Postgres (5432) y la API (8000) se publican sin `127.0.0.1`, es decir, en todas las interfaces. El `.env` local conserva `JWT_SECRET` y `POSTGRES_PASSWORD` iguales a los de `.env.example`, que está en el repo. Quien esté en la misma red puede entrar a la base de datos y firmar un JWT válido. | **Verificado:** los puertos se publican sin IP de enlace y los dos secretos coinciden con el ejemplo (comparado sin mostrar valores). Falta saber si el firewall de Windows lo bloquea. |
| **K8-01** (incluye BE-06) | `backend/app/services/provisioning.py:73-111`, `schemas/client.py:79-96` | `host` y `name` solo se recortan; se incrustan por f-string en el `kustomization.yaml` que el Hub commitea y Argo CD aplica. Un `host` con salto de línea puede inyectar parches nuevos. El AppProject `clientes` permite `Namespace` y `Deployment`, así que un parche podría cambiar la etiqueta de Pod Security del namespace. Lo puede provocar solo un usuario con rol agencia. | **Verificado en el código** (sin validación de formato; el AppProject permite esos recursos). **No ejecutado:** falta confirmar con `kustomize build` sobre un `host` con `\n`. |
| **BE-01** (incluye K8-07) | `backend/app/routers/assistant.py:93-101`, `voz/app/main.py:90-113`, `gitops/hub/api.yaml:99-106` | `voice_transcribe` es `async def` y llama a una función síncrona con timeout de 60 s: congela el bucle de eventos, incluido `/health`. La liveness no declara `timeoutSeconds` (1 s) y tolera tres fallos de 15 s. El servicio `voz` repite el patrón con `async def stt`. | **Verificado** que la ruta es `async` y llama código síncrono. **Matiz:** una transcripción normal (segundos) congela la API pero no reinicia el Pod; el reinicio solo ocurre si el servicio de voz se cuelga cerca de los 60 s. Con ese matiz es medio-alto. |

## Medios

### Base de datos
- **BD-01** Faltan índices en casi todas las claves foráneas (tickets, ticket_events, work_logs, change_requests, deployments, services, projects, users). El vigilante de Argo CD consulta `change_requests` y `deployments` cada 15 s.
- **BD-02** «Un solo cambio en curso por servicio» y «control ya registrado» se validan con SELECT y luego INSERT, sin restricción en la base: dos peticiones simultáneas crean duplicados.
- **BD-03** `has_report` carga el JSON de Trivy/SBOM de cada control solo para devolver un booleano.

### Backend
- **BE-02** `get_db` mantiene la transacción abierta durante llamadas a Ollama, Prometheus, Loki y Gitea; con el pool por defecto, unas 15 consultas de IA simultáneas agotan las conexiones.
- **BE-03** El tablero de agencia y el reporte operativo repiten consultas por cliente (unas 12 más 2 por ticket, con N+1 en `work_logs`).
- **BE-04** Casi ningún listado tiene paginación; `list_reports` trae el JSON completo.
- **BE-05** Textos sin `max_length` y `request.body()` sin tope, con 256 Mi de límite y el Ingress directo al Pod: un usuario autenticado puede provocar OOM.
- **BE-07** Reindexar el RAG en medio de una pregunta tiene una carrera que devuelve 500 en lugar de la recuperación léxica.

### Frontend
- **FE-01** Un fallo pasajero de la primera petición deja toda la sesión en modo mock, con un usuario de agencia falso y sin «Cerrar sesión».
- **FE-02** Todo el mock (`api.ts`, 1.949 líneas) viaja en el bundle de producción (287 KB, 86 KB comprimido, un solo archivo).
- **FE-03** 17 páginas importadas sin `lazy`: el portal de cliente descarga también la consola de agencia.
- **FE-04** No hay `ErrorBoundary`: una excepción de render deja la pantalla en blanco.
- **FE-05 / FE-06** Cascadas N+1 en Incidentes y Cambios (esta última con sondeo cada 5 s).

### Contenedores
- **CT-02** La API de desarrollo monta toda la raíz del repo, incluidos `.env` y `.env.cluster`.
- **CT-03** El runner corre como root con `docker.sock` (excepción ya documentada en `pipelines/README.md`; va contra la regla «sin root»).
- **CT-04 y K8-14** MLflow (5000) y el modelo-compuerta (5001) escuchan en todas las interfaces sin autenticación; quien llegue puede mover el alias `production` del clasificador. En el clúster, MLflow tiene Ingress sin autenticación.
- **CT-05** `nginx.conf` no activa gzip; si nada más comprime, cada carga fría transfiere unos 197 KB de más.

### Kubernetes y GitOps
- **K8-02** El aislamiento de red es solo de entrada: un Pod de cliente comprometido puede leer Loki, Prometheus y MLflow, o enviar alertas falsas a Alertmanager, que reenvía al Hub.
- **K8-03** Liveness y readiness usan el mismo `/health`, que depende de la base: si Postgres se reinicia, la API entra en CrashLoopBackOff. Sin `startupProbe`.
- **K8-04, CT-06 y BE-14** El HPA permite 2 réplicas aunque el propio manifiesto dice que las tareas en segundo plano se repetirían; el watcher no tiene lock y cada Pod ejecuta `alembic upgrade head`.
- **K8-05** `hub-bot` escribe en todo `hub-gitops`, incluido `observability/`, que se aplica con el proyecto `default` (sin restricciones): camino a cluster-admin que rodea el AppProject `clientes`.
- **K8-06** El Hub y los componentes de plataforma se aplican a mano (`kubectl apply -k`), contra el principio 3.

### Observabilidad
- **OB-01** El Hub no tiene sondeo ni alerta, y el único receptor de Alertmanager es el propio Hub (sin Watchdog).
- **OB-02** Si Blackbox cae, `SitioCaido` no se dispara (falta `up == 0` o `absent`).
- **OB-03** Sin alertas de OOM, reinicios, disco/PVC ni respaldo fallido.
- **OB-04** Los logs del Hub no llegan a Loki, el logging de la API no está configurado y no hay id de petición.
- **OB-05** Las alertas de presupuesto con etiqueta `critical` van a un receptor vacío.

### IaC
- **IA-01** El módulo OpenTofu crea las Applications en el proyecto `default` y choca con el ApplicationSet; un `tofu apply` rebajaría el confinamiento de un cliente.
- **IA-04** *(leve en el anexo; lo subo a vigilar)* el repo vive en `OneDrive\Desktop`, que puede sincronizar `.env`, `.env.cluster` y `infra/state` a la nube. No se verificó si esa carpeta se sincroniza.

## Leves
52 hallazgos de estilo, redundancia o mejora defensiva. Los más útiles de arreglar junto con los medios:
validación de entradas (`hours`, correo), lecturas de disco repetidas por petición (`lru_cache`), `JSON` en vez de `jsonb`,
columnas sin `NOT NULL`/`CHECK`, accesibilidad (tablas sin `caption`, `th` vacío, estados de carga sin `role="status"`),
contraste del gráfico en tema oscuro, `readOnlyRootFilesystem` en `hub`, etiquetas de imagen sin digest, herramientas con
`latest` en scripts de apoyo y cabeceras de seguridad ausentes en `nginx.conf`. La lista completa está en los anexos.

## Lo que está bien (verificado)
- **Control de acceso:** de los 61 endpoints, el único sin autenticación es `POST /api/auth/login`. Los 16 que a primera vista
  parecían sin protección heredan la dependencia a nivel de router (`require_agency` o `current_user`). Los de objeto propio
  (`tickets`, `clients`, `dashboard`, `reports`) comprueban que el cliente solo vea lo suyo y responden 404 (no 403) para no
  revelar que existe. Los webhooks de Alertmanager y del pipeline comparan con `hmac.compare_digest` y rechazan el token vacío.
  *Límite:* es una revisión dirigida, no un análisis completo de autorización de cada ruta.
- **Contenedores:** todos terminan con usuario no root salvo el runner; no hay `latest` ni secretos en `ENV`/`ARG`; el servicio
  `voz` publica solo en `127.0.0.1` con `read_only` y `cap_drop: ALL`.
- **Kubernetes:** Pods sin root, `drop: [ALL]`, `seccomp`, requests y limits en todo, sondas en todo, Pod Security `restricted`
  en `hub` y clientes, AppProject con lista blanca, admisión de imágenes, sin secretos en el repo, pruebas de aislamiento y drift.
- **Base de datos:** todas las fechas son `timestamptz`; 14 migraciones con `downgrade`; timeouts presentes en todas las
  integraciones; sin `requests` ni `time.sleep` en la app; el RAG con coseno en Python no es problema con 31 secciones.
- **Frontend:** fuentes autoalojadas, caché de `/assets/` de un año, contexto de sesión memoizado, sin `innerHTML`, fechas en
  America/Bogota, `prefers-reduced-motion`, estados con texto e ícono.

## Fusiones (cómo se pasó de 89 a 84)
| Quedó como | Absorbió | Motivo |
|---|---|---|
| K8-01 (crítico) | BE-06 (medio) | Misma inyección de YAML vista desde backend y desde Kubernetes. |
| BE-01 (crítico) | K8-07 (medio) | Mismo patrón `async def` con E/S bloqueante, en la API y en `voz`. |
| K8-04 (medio) | CT-06 (medio), BE-14 (leve) | Migraciones al arrancar con más de una réplica. |
| CT-04 (medio) | K8-14 (leve) | MLflow sin autenticación y expuesto. |

## Orden de corrección propuesto
Esfuerzo estimado para mí trabajando solo. «Tu parte» marca lo que no puedo cerrar sin ti.

| Orden | Qué | Hallazgos | Esfuerzo | Tu parte |
|---|---|---|---|---|
| 1 | Puertos en loopback, exigir un `JWT_SECRET` fuerte al arrancar, rotar secretos del `.env` local | CT-01, CT-02 | 20–30 min | Rotar el `.env` local (o autorizarme a hacerlo) |
| 2 | Validar `host`/`name` y generar el YAML con `yaml.safe_dump`; prueba con `host="a\nb"`; confirmar con `kustomize build` | K8-01 | 45–60 min | Ninguna |
| 3 | `def` o `to_thread` en voz; `/livez`, `startupProbe` y `timeoutSeconds` | BE-01, K8-03 | 40–60 min | Aplicar el cambio de manifiestos en el clúster |
| 4 | Migración con índices de FK y únicos parciales | BD-01, BD-02 | 45–60 min | Ninguna (probar en el clúster es tuyo) |
| 5 | Pool, timeouts, `max_length`, tope de cuerpo | BE-02, BE-05 | 60–90 min | Ninguna |
| 6 | `maxReplicas: 1` o lock del watcher; migración como Job | K8-04 | 30–45 min | Aplicar en el clúster |
| 7 | Alertas (`HubCaido`, Watchdog, `up == 0`, OOM, reinicios, respaldo) | OB-01…OB-03 | 60–90 min | Aplicar en el clúster |
| 8 | Frontend: mock solo en dev, `lazy`, `ErrorBoundary`, gzip | FE-01…FE-04, CT-05 | 90–120 min | Ninguna |
| 9 | Paginación y consultas agregadas del tablero | BE-03, BE-04, BD-03 | 90–120 min | Ninguna |
| 10 | NetworkPolicy de salida y separación de permisos de `hub-bot` | K8-02, K8-05 | 60–90 min | Decisión sobre ramas protegidas en Gitea |

## No verificado
- Core Web Vitals, Lighthouse, tamaño real del bundle de la última versión de `src/` (el `dist/` medido es del 14 nov).
- Estado real del clúster: `kubectl top`, reinicios, NetworkPolicy efectiva con el CNI de k3s, `tofu plan`.
- Planes de ejecución (`EXPLAIN`) y volumen real de las tablas; agotamiento del pool y OOM bajo carga.
- Que `kustomize build` acepte el parche inyectado (K8-01).
- Si el firewall de Windows bloquea los puertos publicados (CT-01, CT-04) y si OneDrive sincroniza `Desktop` (IA-04).
- La línea base: **no se ejecutaron `ruff check .` ni `docker compose exec api pytest`**; `ruff` no está instalado en esta máquina y
  las pruebas exigen el entorno levantado. Esta auditoría no parte de un estado verde comprobado.

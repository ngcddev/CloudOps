# Plan 008 · Monitoreo e incidente automático

> Cómo se construye [la spec](spec.md). Dos carriles que se juntan en el webhook: el **producto**
> (incidentes manuales, SLA, pantallas) puede empezar ya y no necesita el clúster; la **plataforma**
> (Prometheus y compañía) entra con el módulo 4 y se despliega por Argo CD, como todo lo demás.

## Punto de partida (lo que ya existe)

| Pieza | Estado | Dónde |
|---|---|---|
| Sesión, roles y bitácora | Hecho (007) | `deps.py`, `services/audit.py` (`incident` ya está reservado en la tabla de acciones) |
| Reloj del SLA por plan y prioridad | Hecho (004) | `services/sla.py`: `due_dates`, `sla_state` |
| Versión activa, estable y salud de Argo CD | Hecho (005) | `services.current_version`, `stable_version`, `deploy_watch.py` |
| Última puerta de seguridad por versión | Hecho (006) | `security_gate.py` (la v2 rota pasa los controles a propósito) |
| Namespace `monitoring` y `NetworkPolicy` que deja entrar a `monitoring` | Hecho (003) | `gitops/platform/namespaces.yaml`, `gitops/clients/_base/networkpolicy.yaml` |
| `services.status` (`operativo`/`caido`) | Existe, nadie lo cambia | `models/service.py` |
| Menú «Incidentes» | Deshabilitado | `frontend/src/components/AgencyLayout.tsx` |

## Decisión 1: la v2 rota tiene que tumbar el sitio

Los sitios tienen 1 réplica y la estrategia por defecto (`RollingUpdate`): al publicar la v2, Kubernetes
deja vivo el Pod v1 mientras el v2 no pase la *readiness probe*, así que el sitio **nunca se cae** y no
hay incidente que mostrar. Se cambia `gitops/clients/_base/deployment.yaml` a `strategy: Recreate`: al
publicar, se apaga la v1; la v2 no queda `Ready` y el `Service` se queda sin endpoints. La readiness
probe sigue haciendo su trabajo (no entra tráfico a un Pod que responde 500, criterio de la 003) pero la
falla se ve y se mide.

Costo: toda publicación, incluso la sana, deja el sitio sin respuesta unos segundos (apagar la v1 y
arrancar la v2; la readiness probe revisa cada 5 s). Por eso la alerta espera 30 s (decisión 3) y existe
el criterio CA-9: una publicación sana **no** abre incidente.

Alternativa descartada: dejar `RollingUpdate` y alertar por «publicación atascada». El sitio seguiría
arriba, no habría P1 ni MTTR de una caída real y el caso del restaurante perdería sentido.

## Decisión 2: qué se sondea y cómo se descubre

Blackbox Exporter sondea el `/health` de cada sitio **por su Service dentro del clúster**
(`http://web.cliente-<c>.svc.cluster.local/health`), sin depender de que el nodo resuelva `*.hub.local`.
Prometheus descubre los sitios solo con `kubernetes_sd_configs: role: service` y una anotación
`hub/probe: "true"` en el `Service` de `gitops/clients/_base/service.yaml`. Un cliente nuevo (spec 011)
queda monitoreado sin tocar Prometheus. El nombre del cliente sale del namespace (`cliente-<c>`).

```yaml
- job_name: sitios
  metrics_path: /probe
  params: { module: [http_2xx] }
  scrape_interval: 5s
  scrape_timeout: 4s
  kubernetes_sd_configs: [{ role: service }]
  relabel_configs:
    - { source_labels: [__meta_kubernetes_service_annotation_hub_probe], regex: "true", action: keep }
    - { source_labels: [__meta_kubernetes_service_name, __meta_kubernetes_namespace], regex: "(.+);(.+)",
        replacement: "http://$1.$2.svc.cluster.local/health", target_label: __param_target }
    - { source_labels: [__param_target], target_label: instance }
    - { source_labels: [__meta_kubernetes_namespace], target_label: namespace }
    - { source_labels: [__meta_kubernetes_namespace], regex: "cliente-(.+)", target_label: client }
    - { target_label: __address__, replacement: "blackbox.monitoring.svc:9115" }
```

El consultorio tiene dos Services (`web` y `backend`); solo `web` lleva la anotación: el sitio completo
se sondea por donde entra el visitante.

## Decisión 3: tiempos de detección (RNF-07)

| Pieza | Valor | Aporta al peor caso |
|---|---|---|
| `scrape_interval` del sondeo | 5 s | 5 s hasta el primer sondeo fallido |
| `evaluation_interval` de las reglas | 5 s | 5 s |
| `for` de la alerta `SitioCaido` | 30 s | 30 s (descarta el reinicio normal de una publicación) |
| `group_wait` de Alertmanager | 5 s | 5 s |
| **Peor caso** | | **≈ 45 s** (≤ 60 s) |

```yaml
- alert: SitioCaido
  expr: probe_success{job="sitios"} == 0
  for: 30s
  labels: { severity: critical, priority: P1 }
  annotations: { summary: "El sitio de {{ $labels.client }} no responde" }
```

Prometheus envía la alerta cuando termina el `for`, no cuando empezó la caída: el Hub fija
`started_at = startsAt − ALERT_CONFIRM_SECONDS` (30, el mismo valor del `for`, en `config.py`, con un
comentario que lo ata a la regla). Así la hora de inicio es la real, con la precisión del sondeo (5 s).
La recuperación sí es real: el `endsAt` del aviso `resolved` es el primer sondeo sano.

## Pila de observabilidad

Manifiestos en `observability/` (raíz del repo, como dice la constitución), con `kustomize` y sin Helm:
menos piezas y todo revisable en un PR. Se despliegan en el namespace `monitoring` por una `Application`
de Argo CD (`gitops/platform/argocd/applications/monitoring.yaml`, camino `observability` de `hub-gitops`).

| Componente | Función | Memoria (request / límite) | Datos |
|---|---|---|---|
| Blackbox Exporter | Sondea `/health` | 32Mi / 64Mi | — |
| Prometheus | Guarda `probe_*` y evalúa la regla | 256Mi / 512Mi | PVC 2Gi, retención 30 d y tope 1GB |
| Alertmanager | Avisa al Hub por webhook | 32Mi / 64Mi | — |
| Loki | Registros de los sitios | 128Mi / 256Mi | PVC 2Gi, retención 3 d |
| Grafana Alloy | Recoge los logs de los Pods de clientes (reemplaza a Promtail, en fin de vida) | 64Mi / 128Mi | — |
| Grafana | Explorar logs y métricas; los dashboards son de la 010 | 128Mi / 256Mi | PVC 500Mi |
| **Total** | | **≈ 640Mi / 1280Mi** | |

El Docker del laboratorio tiene 8 GB y el nodo ya usa ~2,4 GiB (Argo CD, Gitea, Backstage, Hub). La pila
cabe, pero las compilaciones de la puerta de seguridad comparten esa memoria: si algo se reinicia por
falta de RAM, apagar primero Backstage (`replicas: 0`) y Loki (el incidente manual y el automático no
dependen de ellos).

Permisos: Prometheus necesita listar `services` (ClusterRole de solo lectura) y Alloy listar `pods` y
leer `pods/log`. Es lectura dentro del clúster por componentes de plataforma, no el Hub hablando con
Kubernetes (principio 5).

Métricas de Traefik (para la 010): un `Service` `traefik-metrics` en `kube-system` apunta al puerto 9100
que ya expone Traefik (`--metrics.prometheus=true`), y Prometheus lo recoge con un job estático.

Direcciones: Grafana en `grafana.hub.local` (se agrega a [nombres canónicos](../../constitution/canonical-names.md)
con un commit `docs(constitution)` propio y a la línea de `hosts` de `gitops/README.md`).

## Modelo de datos (migración `0008`)

| Tabla | Campos |
|---|---|
| `incidents` | `id` · `service_id` FK · `priority` · `status` (`abierto` / `mitigado` / `cerrado`) · `source` (`alerta` / `manual`) · `fingerprint` (nulo en los manuales) · `title` · `started_at` · `acknowledged_at` · `mitigated_at` · `closed_at` · `response_due_at` · `resolution_due_at` · `assignee_id` FK users · `created_by_id` FK users (nulo si lo abrió el sistema) · `root_cause` · `created_at` |
| `incident_events` | `id` · `incident_id` FK · `type` (`detectado`, `tomado`, `nota`, `recuperado`, `cerrado`) · `message` · `actor_id` (nulo = Sistema) · `created_at` |

Índice único parcial en `fingerprint` donde `status = 'abierto'`: dos avisos simultáneos no pueden crear
dos incidentes (CA-3). La 009 agrega los campos del rollback con su propia migración.

## Reglas de negocio (`backend/app/services/`)

- `incident_flow.py`: `abierto → mitigado → cerrado`. Cerrar exige `root_cause`. Mitigar a mano solo vale
  para incidentes `manual`: los de alerta los mitiga el `resolved`, con la hora real de la sonda.
  «Tomar» no es un estado: fija `acknowledged_at` y el responsable (solo una vez; la segunda vez es 409).
- `sla.py`: se generaliza a `clock_state(start, due, done_at, now)` → `a_tiempo` | `en_riesgo` (≥ 80 %
  del plazo) | `vencido` | `cumplido`; `sla_state` de los tickets pasa a usarla sin cambiar su resultado.
  Para un incidente P1, `due_dates(started_at, "P1", plan)` es siempre 24/7. Con el incidente mitigado el
  reloj se detiene.

## Webhook de Alertmanager

`POST /api/alerts/alertmanager` con `Authorization: Bearer <ALERTMANAGER_TOKEN>` (token propio, distinto
al de las sesiones y al de la puerta de seguridad; sin token o con otro → 401, igual que
`/api/pipeline-events`). Por cada alerta del payload (v4):

- `firing` → ubica el servicio por la etiqueta `namespace`; si hay un incidente `abierto` con el mismo
  `fingerprint`, no hace nada; si no, lo crea con la prioridad de la etiqueta, `started_at` como en la
  decisión 3, SLA con `sla.py`, evento `detectado` y servicio en `caido`.
- `resolved` → `mitigated_at = endsAt`, estado `mitigado`, evento `recuperado` y servicio `operativo`.
- Un `firing` que llega después de un `mitigado` abre un incidente nuevo: reabrir falsearía el MTTR.
- Servicio inexistente o `resolved` de un fingerprint desconocido → 200 con aviso en el log (Alertmanager
  no debe reintentar sin fin).
- Todo se hace en una transacción con su `audit.record(db, None, …)` («Sistema»).

## API y pantallas

| Método | Ruta | Rol | Qué hace |
|---|---|---|---|
| POST | `/api/alerts/alertmanager` | token de Alertmanager | Recibe `firing` y `resolved` |
| GET | `/api/incidents?status=&client_id=&priority=` | agencia | Lista con estado del SLA |
| POST | `/api/incidents` | agencia | Incidente manual (servicio, prioridad, título) |
| GET | `/api/incidents/{id}` | agencia | Detalle + línea de tiempo + enlaces |
| POST | `/api/incidents/{id}/acknowledge` | agencia | Tomar |
| POST | `/api/incidents/{id}/notes` | agencia | Nota en la línea de tiempo |
| POST | `/api/incidents/{id}/mitigate` | agencia | Mitigar a mano (solo `manual`) |
| POST | `/api/incidents/{id}/close` | agencia | Cerrar con causa raíz |

`/api/services/status` suma `service_status` (`operativo` / `caido`) para que la consola de servicios lo
muestre. El cliente **no** ve incidentes en esta spec: su vista simplificada es de la 010.

Enlaces del detalle (`services/incident_links.py`):

- **Registros del sitio:** Grafana Explore con la fuente `loki` y `{namespace="cliente-<c>"}`, desde 5 min
  antes del inicio hasta la mitigación (o ahora). Usa `GRAFANA_URL`, la dirección que ve el navegador.
- **Último cambio:** el último `Deployment` y el último `ChangeRequest` del servicio, con enlace al commit
  en Gitea (`GITEA_PUBLIC_URL`, que no es la `GITEA_URL` interna del clúster).

| Pantalla | Ruta | Qué muestra |
|---|---|---|
| Incidentes | `/agencia/incidentes` | Lista con prioridad, cliente, estado y reloj; «Nuevo incidente» |
| Detalle | `/agencia/incidentes/:id` | Reloj, línea de tiempo, enlaces, tomar, nota, mitigar (manual), cerrar |

`components/SlaClock.tsx` cuenta cada segundo en el navegador con las fechas límite que manda la API; el
estado va con texto e ícono (✓ / ! / ✗), sin color.

## Secretos y configuración

- `ALERTMANAGER_TOKEN`: Secret `hub-alertmanager` (clave `token`) en los namespaces `hub` y `monitoring`,
  con el mismo valor, creado por `gitops/hub/crear-secretos.sh`. Alertmanager lo lee de un archivo montado
  (`authorization.credentials_file`); la API, de una variable opcional (sin Secret arranca y no acepta
  avisos). Nunca en el repo (RNF-06); en `.env.example` va un valor de desarrollo.
- `GRAFANA_URL`, `GITEA_PUBLIC_URL`: valores normales en `gitops/hub/api.yaml` y `.env.example`.
- Alertmanager llama al Hub por dentro del clúster: `http://api.hub.svc:8000/api/alerts/alertmanager`.

## Cómo llega la pila a `hub-gitops`

`hub-gitops` se sembró desde `gitops/` y `sembrar-hub-gitops.sh` no vuelve a sembrar un repo con commits.
Se agrega `gitops/platform/gitea/actualizar-hub-gitops.sh`, que copia carpetas elegidas del monorepo
(`observability`, y más adelante lo que cambie) en un commit nuevo, y se usa también para
`clients/_base`. Después se aplica la `Application` `monitoring` con `kubectl apply`.

## Contratos con otras specs

- Recibe de **002/003**: `/health`, la v2 rota y la política de red que deja entrar a `monitoring`. De
  **004**: `sla.py`. De **005**: `deployments`, Argo CD y el flujo para publicar por Git. De **007**:
  `require_role` y `audit.record`.
- Entrega a **009**: el incidente `abierto` y `incident_events` sobre los que actúa el rollback; el
  `resolved` fija la hora real de mitigación.
- Entrega a **010 / 013**: `started_at`, `mitigated_at`, `source`, `priority` para MTTR y cumplimiento;
  Prometheus con `probe_success` y `probe_duration_seconds` etiquetados `client` y `namespace`; Grafana
  con sus fuentes de datos.
- Entrega a **012**: el incidente y su línea de tiempo para el resumen.
- Entrega a **011**: la anotación `hub/probe` hace que un cliente nuevo quede monitoreado solo.

## Riesgos

| Riesgo | Respuesta |
|---|---|
| Una publicación sana abre un P1 falso (CA-9) | `for: 30s` y una prueba que publica una versión sana y exige cero incidentes |
| La pila le quita memoria al nodo | Límites de la tabla; apagar Backstage y Loki primero |
| Alertas duplicadas o simultáneas | Deduplicar por `fingerprint` + índice único parcial |
| La hora de inicio queda 30 s tarde | `started_at = startsAt − ALERT_CONFIRM_SECONDS`, con prueba |
| `hub-gitops` desactualizado | `actualizar-hub-gitops.sh`; Argo CD muestra `OutOfSync` si falta algo |
| Prometheus pierde los datos al reiniciarse | PVC (el dato del mes alimenta la 010) |

## Cómo se verifica

- `pytest` del webhook con payloads reales de Alertmanager guardados en `backend/tests/fixtures/`
  (`firing`, repetido, `resolved`, servicio desconocido, token errado).
- `observability/pruebas/validar.sh`: `promtool check config` y `check rules` en contenedor, y
  `kubectl kustomize observability`.
- `observability/pruebas/cronometro.sh`: aprueba la v2 de La Sazón por la API del Hub, mide hasta que el
  incidente aparece y vuelve a v1; tres corridas, todas ≤ 60 s.
- `observability/pruebas/publicacion-sana.sh`: publica una versión sana y comprueba que no hay incidentes.
- Demo de [spec.md](spec.md#demo-de-cierre).

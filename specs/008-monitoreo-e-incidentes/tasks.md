# Tareas 008 · Monitoreo e incidente automático

> Cada tarea: una acción con verbo · se comprueba en minutos · menos de un día · se integra sola.
> Rama por tarea: `feat/008-tNN-slug`. Poner el nombre de quien la toma entre corchetes.
>
> Fechas: módulo 4 del 24 oct al 3 nov (sustentación). El caso del restaurante sin IA debe estar listo el
> 31 oct (008 + 009); el 1 y 2 de nov solo se ensaya. Meta de esta spec: **28 oct**.

## Cómo repartirlo

| Carril | Tareas | Necesita el clúster | Puede empezar |
|---|---|---|---|
| Backend | T01–T08, T09–T13 | No (usa `pytest` y `docker compose`) | Ya |
| Frontend | T14–T18 | No (datos de prueba hasta que la API responda, como en la 001) | Ya, con T14 |
| Plataforma | T19–T29 | Sí | Ya; T22 espera a T21 y T28 a T21–T27 |
| Integración | T30–T33 | Sí | Cuando cierren los tres carriles |

Es spec de producto y de plataforma a la vez: el backend y el frontend **no esperan** a la plataforma
(regla de desacople). El webhook (T09–T13) se prueba con payloads guardados; T09 se rehace con los reales
cuando T24 deje Alertmanager funcionando.

## Backend · incidentes manuales

- [x] T01 · Crear las tablas `incidents` e `incident_events` con migración `0008` (índice único parcial en `fingerprint` para los `abierto`) — **Verifica:** `alembic upgrade head` y `alembic downgrade -1` sin errores; insertar dos incidentes abiertos con el mismo `fingerprint` falla y con distinto no. [sebastian-debug]
- [x] T02 · Escribir `services/incident_flow.py` con `abierto → mitigado → cerrado`, causa raíz obligatoria al cerrar y mitigación a mano solo para `manual` — **Verifica:** `pytest` acepta las transiciones válidas y rechaza `abierto → cerrado`, cerrar sin causa raíz y mitigar a mano uno de alerta. [sebastian-debug]
- [x] T03 · Generalizar `sla_state` de `services/sla.py` en `clock_state(start, due, done_at, now)` con `a_tiempo`, `en_riesgo` (≥ 80 %), `vencido` y `cumplido`, y dejar que el de los tickets la use — **Verifica:** las pruebas de la 004 siguen en verde y nuevas cubren un incidente tomado a los 10 min (respuesta `cumplido`) y mitigado a las 5 h (solución `vencido`). [sebastian-debug]
- [x] T04 · Crear `POST /api/incidents` (manual: servicio, prioridad y título) y `GET /api/incidents` con filtros y estado del SLA — **Verifica:** `pytest`: un P1 de La Sazón abierto a las 14:00 vence respuesta 14:15 y solución 18:00 (24/7), queda el evento `detectado` y una fila en la bitácora; como cliente → 403. [sebastian-debug]
- [x] T05 · Crear `GET /api/incidents/{id}` con la línea de tiempo, `acknowledge` y `notes` — **Verifica:** tomar a los 5 min deja la respuesta en `cumplido` y la línea de tiempo muestra «tomado» con el usuario; tomar dos veces → 409. [sebastian-debug]
- [x] T06 · Crear `mitigate` (manual) y `close` con causa raíz, ambos con `audit.record` — **Verifica:** `pytest`: el ciclo manual completo deja `mitigated_at`, `closed_at`, `root_cause` y 4 filas en `audit_logs` (crear, tomar, mitigar, cerrar); una transición inválida no deja fila. [sebastian-debug]
- [x] T07 · Escribir `services/incident_links.py` con el enlace a Grafana Explore (`{namespace="cliente-<c>"}` desde 5 min antes del inicio) y al último cambio (commit en Gitea), y agregar `GRAFANA_URL` y `GITEA_PUBLIC_URL` a `config.py`, `.env.example`, `docker-compose.yml` y `gitops/hub/api.yaml` — **Verifica:** `pytest` compara las URL generadas para un incidente de La Sazón con un cambio publicado. [sebastian-debug]
- [x] T08 · Sumar `service_status` a `GET /api/services/status` — **Verifica:** `pytest`: un servicio con incidente de alerta abierto responde `caido` y uno sin incidentes, `operativo`. [sebastian-debug]

## Backend · webhook de Alertmanager

- [ ] T09 · Guardar en `backend/tests/fixtures/` payloads de Alertmanager (v4) de `SitioCaido`: `firing`, `firing` repetido y `resolved` — **Verifica:** son JSON válidos con `status`, `alerts[].labels.namespace`, `startsAt`, `endsAt` y `fingerprint`. [ ]
- [ ] T10 · Crear `POST /api/alerts/alertmanager` con `ALERTMANAGER_TOKEN` (en `config.py` y `.env.example`) que abre el incidente P1 con `started_at = startsAt − ALERT_CONFIRM_SECONDS`, evento `detectado` y servicio `caido` — **Verifica:** `pytest` con el payload `firing`: un incidente `alerta` P1 de La Sazón con su hora de inicio 30 s antes de `startsAt`; sin token o con otro → 401. [ ]
- [ ] T11 · Deduplicar por `fingerprint`: un `firing` repetido no crea otro incidente; uno que llega después de un `mitigado` sí — **Verifica:** `pytest` envía el mismo `firing` 3 veces y queda 1 incidente; tras el `resolved`, un `firing` nuevo crea el segundo. [ ]
- [ ] T12 · Procesar `resolved`: `mitigated_at = endsAt`, estado `mitigado`, evento `recuperado` y servicio `operativo`; servicio o fingerprint desconocido responde 200 con aviso en el log — **Verifica:** `pytest` con los payloads de T09 y uno con `namespace` inexistente. [ ]
- [ ] T13 · Agregar la prueba punta a punta del ciclo de alerta (firing → incidente → tomar → resolved → cerrar) y comprobar que la prueba de rutas protegidas sigue en verde con la ruta nueva — **Verifica:** `docker compose exec api pytest` en verde. [ ]

## Frontend

- [ ] T14 · Agregar a `frontend/src/api.ts` los tipos y llamadas de incidentes, con datos de prueba si la API no responde — **Verifica:** `tsc` sin errores. [ ]
- [ ] T15 · Crear `components/SlaClock.tsx`, que cuenta cada segundo hasta la fecha límite activa y muestra «a tiempo», «en riesgo», «vencido» o «cumplido» con texto e ícono — **Verifica:** con un incidente de prueba que vence en 1 min, el texto cambia sin recargar. [ ]
- [ ] T16 · Crear `/agencia/incidentes` con la lista, filtros y «Nuevo incidente», y habilitar «Incidentes» en el menú de la consola — **Verifica:** crear un P2 manual de El Tornillo lo muestra en la lista con su reloj. [ ]
- [ ] T17 · Crear `/agencia/incidentes/:id` con reloj, línea de tiempo, enlaces y los botones tomar, nota, mitigar (solo manual) y cerrar (pide causa raíz) — **Verifica:** el ciclo manual completo se hace desde la pantalla y la línea de tiempo se actualiza sin recargar (CA-8). [ ]
- [ ] T18 · Mostrar «No disponible» y «Operativo» en `/agencia/servicios` con texto e ícono — **Verifica:** un servicio con incidente abierto aparece «✗ No disponible». [ ]

## Plataforma

- [ ] T19 · Cambiar `gitops/clients/_base/deployment.yaml` a `strategy: Recreate` explicando por qué y agregar a `_base/service.yaml` la anotación `hub/probe: "true"` — **Verifica:** `bash gitops/pruebas/readiness.sh` sigue pasando (003 CA-6) y al aplicar la v2 de un cliente, `kubectl get endpoints web -n cliente-<c>` queda sin direcciones. [ ]
- [ ] T20 · Escribir `gitops/platform/gitea/actualizar-hub-gitops.sh`, que copia carpetas elegidas del monorepo a `hub-gitops` en un commit nuevo, y usarlo para subir el cambio de T19 — **Verifica:** Argo CD sincroniza los 3 clientes con la estrategia nueva y siguen `Synced` y `Healthy`. [ ]
- [ ] T21 · Crear `observability/` con su `kustomization.yaml` e instalar Blackbox Exporter con el módulo `http_2xx` (timeout 4 s) — **Verifica:** desde un Pod en `monitoring`, `curl 'blackbox:9115/probe?target=http://web.cliente-restaurante.svc.cluster.local/health&module=http_2xx'` devuelve `probe_success 1`. [ ]
- [ ] T22 · Instalar Prometheus (retención 30 días con tope de 1GB, PVC de 2Gi, `ClusterRole` de solo lectura sobre `services`) con el job `sitios` de la decisión 2 — **Verifica:** `probe_success` muestra una serie por cliente con las etiquetas `client` y `namespace`, sondeadas cada 5 s (CA-1); apagar y encender el Pod conserva los datos. [ ]
- [ ] T23 · Agregar la regla `SitioCaido` (`for: 30s`, `priority: P1`) y `observability/pruebas/validar.sh` (`promtool check config` y `check rules` en contenedor) — **Verifica:** `validar.sh` termina en verde y, con la v2 aplicada, la alerta pasa a `firing` en Prometheus en menos de 45 s. [ ]
- [ ] T24 · Instalar Alertmanager con el webhook al Hub (token desde archivo, `group_wait: 5s`, `send_resolved: true`) y crear el Secret `hub-alertmanager` en `hub` y `monitoring` desde `gitops/hub/crear-secretos.sh`, pasándolo a la API en `gitops/hub/api.yaml` — **Verifica:** un `POST` con el token desde un Pod de `monitoring` responde 200 y sin token, 401; `git grep` no encuentra el valor. [ ]
- [ ] T25 · Instalar Loki (retención 3 días, PVC de 2Gi) y Grafana Alloy recogiendo los logs de los Pods de los namespaces `cliente-*` con su `ClusterRole` de lectura — **Verifica:** `{namespace="cliente-restaurante"}` en Grafana Explore muestra las peticiones de Nginx. [ ]
- [ ] T26 · Instalar Grafana con las fuentes `prometheus` y `loki` provisionadas, expuesto en `grafana.hub.local` (entrada en `hosts` de `gitops/README.md`) — **Verifica:** abre con el administrador de su Secret y las dos fuentes responden «OK». [ ]
- [ ] T27 · Proponer `grafana.hub.local` en [nombres canónicos](../../constitution/canonical-names.md) con un commit `docs(constitution)` propio y exponer el puerto 9100 de Traefik con un Service `traefik-metrics` en `kube-system` — **Verifica:** PR de la constitución aprobado por el equipo, y la métrica `traefik_service_requests_total` aparece en Prometheus. [ ]
- [ ] T28 · Crear `gitops/platform/argocd/applications/monitoring.yaml`, subir `observability/` con `actualizar-hub-gitops.sh` y aplicarla — **Verifica:** Argo CD muestra `monitoring` `Synced` y `Healthy`, y un cambio en `observability/` llega al clúster por Git. [ ]
- [ ] T29 · Medir la memoria de la pila con `kubectl top pods -n monitoring` tras 1 h encendida y anotarla en `observability/README.md` — **Verifica:** ningún Pod reinició y el total queda bajo los límites del plan. [ ]

## Integración

- [ ] T30 · Publicar el Hub con la 008 (imágenes `hub-api` y `hub-web` con etiqueta nueva, variables nuevas en `gitops/hub/api.yaml`) y escribir `observability/pruebas/cronometro.sh`, que aprueba la v2 de La Sazón por la API, mide hasta que aparece el incidente y vuelve a v1 — **Verifica:** tres corridas seguidas, todas ≤ 60 s, con el incidente en `mitigado` al volver a v1 (CA-2, CA-5, CA-6). [ ]
- [ ] T31 · Escribir `observability/pruebas/publicacion-sana.sh`, que publica `v1.1` de El Tornillo y vigila 2 minutos — **Verifica:** no se crea ningún incidente y el servicio nunca queda `caido` (CA-9). [ ]
- [ ] T32 · (Opcional, no bloquea el cierre) Contar formularios recibidos y fallidos con OpenTelemetry en `consultorio-api`, publicar `v1.1` por la puerta y recogerla en Prometheus — **Verifica:** enviar el formulario sube la serie en Prometheus. [ ]

## Cierre

- [ ] T33 · Demo: la v2 de La Sazón abre el P1 en ≤ 1 min con el reloj corriendo, se toma, se abren registros y último cambio, el `git revert` lo deja `mitigado`, se cierra con causa raíz y una versión sana no abre incidente — **Verifica:** todos los criterios de [spec.md](spec.md#criterios-de-aceptación). [ ]

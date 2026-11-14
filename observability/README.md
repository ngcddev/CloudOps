# Observabilidad (spec 008)

Pila que vigila los sitios de los clientes y avisa al Hub cuando uno se cae. Va en el namespace
`monitoring` y Argo CD la reconcilia desde la carpeta `observability` de `hub-gitops` (Application
`monitoring`). Sin Helm: cada componente es un `kustomization.yaml` con sus manifiestos.

```
sitio (/health) ← Blackbox ← Prometheus ──SitioCaido──> Alertmanager ──webhook──> Hub (incidente P1)
Pods cliente-* ──registros──> Alloy ──> Loki ──> Grafana (Explore) <── enlace «Registros del sitio» del Hub
```

| Carpeta | Qué hace |
|---|---|
| `blackbox/` | Sondea `/health` de cada sitio (módulo `http_2xx`, 4 s de timeout) |
| `prometheus/` | Descubre los sitios por la anotación `hub/probe` de su Service, los sondea cada 5 s y evalúa `SitioCaido`. El job `apps` recoge `/metrics` de los Services con la anotación `hub/metrics` (hoy, `consultorio-api`: `contact_forms_received_total` y `contact_forms_failed_total`, con OpenTelemetry; spec 008, T32) |
| `alertmanager/` | Avisa al Hub en `http://api.hub.svc:8000/api/alerts/alertmanager` con el token del Secret `hub-alertmanager` |
| `loki/` | Guarda 3 días de registros de los sitios |
| `alloy/` | Lee por la API de Kubernetes los registros de los Pods de `cliente-*` y los manda a Loki |
| `grafana/` | `http://grafana.hub.local`, con las fuentes `prometheus` y `loki` ya configuradas |
| `traefik/` | Service `traefik-metrics` en `kube-system` para las métricas de Traefik (spec 010) |
| `tempo/` | Recibe las trazas OTLP del Hub (puerto 4318), 24 horas en un volumen efímero; Grafana lo lee con la fuente `tempo` |
| `grafana/dashboards/` | Tablero «Servicio de los sitios · SLI y SLO»: disponibilidad frente al SLO de cada plan, presupuesto de error, latencia p95, errores 5xx, formularios y registros |
| `pruebas/` | `validar.sh`, pruebas de la regla, `tablero_test.yml`, `grafana.sh`, `trazas.sh`, `cronometro.sh` y `publicacion-sana.sh` |

## Tiempos de detección

| Pieza | Valor | Dónde |
|---|---|---|
| Sondeo de cada sitio | 5 s | `prometheus/prometheus.yml`, job `sitios` |
| Evaluación de la regla | 5 s | `prometheus/reglas/sitios.yml` |
| `for` de `SitioCaido` | 30 s | `prometheus/reglas/sitios.yml` y `ALERT_CONFIRM_SECONDS` del Hub (van juntos) |
| `group_wait` de Alertmanager | 5 s | `alertmanager/alertmanager.yml` |
| **Peor caso** | **≈ 45 s** | CA-2 pide ≤ 60 s |

El Hub fija el inicio del incidente en `startsAt − 30 s` (la hora real de la caída) y la mitigación en el
`endsAt` del aviso `resolved` (el primer sondeo sano).

## Instalar

1. Secrets (una sola vez; no se cambian si ya existen): `bash gitops/hub/crear-secretos.sh`
   (crea `hub-alertmanager` en `hub` y `monitoring`, y `grafana-admin` en `monitoring`).
2. Subir la carpeta a `hub-gitops`: `bash gitops/platform/gitea/actualizar-hub-gitops.sh observability`
   (lo mismo con `gitops/clients/_base` para la estrategia `Recreate` y la anotación `hub/probe`).
3. Aplicar la Application: `kubectl apply -f gitops/platform/argocd/applications/monitoring.yaml`.
4. Agregar `grafana.hub.local` a la línea de `hosts` (ver `gitops/README.md`).

Contraseña de Grafana (usuario `admin`):
`kubectl -n monitoring get secret grafana-admin -o jsonpath='{.data.admin-password}' | base64 -d`

## Validar sin el clúster

```bash
bash observability/pruebas/validar.sh   # promtool check config/rules, promtool test rules, amtool, kustomize
```

`pruebas/reglas_test.yml` comprueba que `SitioCaido` dispara a los 30 s de caída y que un reinicio de
20 s (una publicación sana) no la dispara.

## Memoria

Límites del plan por componente (request / límite). El nodo del laboratorio ya usa ~2,4 GiB; si algo se
reinicia por falta de RAM, apagar primero Backstage (`replicas: 0`) y después Loki y Alloy: los
incidentes, manuales o automáticos, no dependen de ellos.

| Componente | Plan (request / límite) | Medido tras 1 h (`kubectl top pods -n monitoring`) |
|---|---|---|
| Blackbox Exporter | 32Mi / 64Mi | pendiente (T29) |
| Prometheus | 256Mi / 512Mi | pendiente (T29) |
| Alertmanager | 32Mi / 64Mi | pendiente (T29) |
| Loki | 128Mi / 256Mi | pendiente (T29) |
| Grafana Alloy | 64Mi / 128Mi | pendiente (T29) |
| Grafana | 128Mi / 256Mi | pendiente (T29) |
| Tempo | 96Mi / 256Mi | pendiente (el nodo ya estaba justo: si falta RAM, `replicas: 0` en Tempo antes que en Prometheus) |
| **Total** | **≈ 640Mi / 1280Mi** | pendiente (T29) |

## Versiones

Imágenes fijadas en los manifiestos: `prom/prometheus:v3.5.0`, `prom/alertmanager:v0.28.1`,
`prom/blackbox-exporter:v0.27.0`, `grafana/loki:3.5.3`, `grafana/alloy:v1.10.2`, `grafana/grafana:12.1.1` y `grafana/tempo:2.8.2`.
Cambiar una versión es un cambio deliberado en su `deployment.yaml` (y en `validar.sh` para promtool y amtool).

## Tablero de Grafana y trazas

El tablero `servicio-sitios` se carga solo al arrancar Grafana (ConfigMap `grafana-dashboards`, no editable desde la interfaz: el cambio va por Git).
Sus cuentas se prueban sin Prometheus real:

```bash
bash observability/pruebas/validar.sh   # además: cuentas del SLI y del presupuesto de error (tablero_test.yml) y sintaxis de cada consulta
bash observability/pruebas/grafana.sh   # levanta Grafana 12.1.1 con los mismos archivos y comprueba el tablero (13 paneles) y las fuentes prometheus, loki y tempo
bash observability/pruebas/trazas.sh    # Tempo real + API de producción: llegan los spans de la API y del asistente, /health no genera trazas
                                        # y ninguna traza lleva el texto de las preguntas
```

Las trazas del Hub se activan con `OTEL_EXPORTER_OTLP_ENDPOINT` (ya puesta en `gitops/hub/api.yaml`). Los spans llevan tiempos, estados y contadores;
**nunca** el texto de las preguntas, de las respuestas ni de los cuerpos de las peticiones. No hay spans de SQL: la instrumentación de SQLAlchemy de
OpenTelemetry soporta hasta la 2.0 y el Hub usa la 2.1. `validar.sh` pasa también en Windows (se corrigieron el comodín de las reglas, la variable `TMP` y la ruta de `kubectl`).

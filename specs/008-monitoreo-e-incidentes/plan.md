# Plan 008 · Monitoreo e incidente automático

> Cómo se construye [la spec](spec.md).

## Stack (módulo 4)

| Pieza | Herramienta |
|---|---|
| Sondeo | Blackbox Exporter (`http_2xx` sobre `https?://<cliente>.hub.local/health`) |
| Métricas | Prometheus (retención corta: 7 días) |
| Alertas | Alertmanager → webhook del Hub |
| Logs | Loki + Promtail (retención 3 días) |
| Métricas de app | OpenTelemetry en el backend del consultorio (formularios recibidos/fallidos) |

Todo en el namespace `monitoring` con límites de memoria; manifiestos en `observability/` y
sincronizados por Argo CD.

## Regla de alerta

```yaml
- alert: SitioCaido
  expr: probe_success{job="blackbox"} == 0
  for: 30s
  labels: { severity: critical, priority: P1 }
  annotations: { client: "{{ $labels.client }}", service: "{{ $labels.service }}" }
```

`scrape_interval: 15s` + `for: 30s` + `group_wait: 10s` ≈ 55 s en el peor caso (RNF-07).
Alertmanager envía también el `resolved`.

## Modelo de datos

| Tabla | Campos |
|---|---|
| `incidents` | `id` · `service_id` FK · `priority` · `status` (`abierto`/`mitigado`/`cerrado`) · `source` (`alerta`/`manual`) · `fingerprint` · `title` · `started_at` · `acknowledged_at` · `mitigated_at` · `closed_at` · `response_due_at` · `resolution_due_at` · `assignee_id` · `root_cause` · `created_at` |
| `incident_events` | `id` · `incident_id` FK · `type` · `message` · `actor_id` · `created_at` |

## Webhook

`POST /api/alerts/alertmanager` (token en cabecera):
- `firing` → busca incidente `abierto` con el mismo `fingerprint`; si no existe, lo crea con
  `started_at = startsAt` de la alerta, prioridad de la etiqueta y SLA con `services/sla.py` (spec 004).
- `resolved` → `mitigated_at = endsAt`, estado `mitigado`, servicio `operativo`.

## API y pantallas

| Método | Ruta | Qué hace |
|---|---|---|
| GET | `/api/incidents` | Lista con reloj de SLA |
| POST | `/api/incidents` | Incidente manual |
| GET | `/api/incidents/{id}` | Detalle + línea de tiempo + enlaces a Grafana/Loki y último despliegue |
| POST | `/api/incidents/{id}/acknowledge` | Tomar (fija `acknowledged_at`) |
| POST | `/api/incidents/{id}/close` | Cerrar con causa raíz |

Pantallas: `/agencia/incidentes` (lista con reloj) y `/agencia/incidentes/:id`.

## Contratos con otras specs

- Recibe de **002**: `/health` y v2 rota. De **003**: hosts. De **004**: `sla.py`.
- Entrega a **009**: incidente abierto sobre el que actúa el rollback.
- Entrega a **010 / 013**: `started_at`, `mitigated_at` para MTTR y disponibilidad.
- Entrega a **012**: datos del incidente para el resumen.

## Riesgos

| Riesgo | Respuesta |
|---|---|
| PC A sin RAM con Prometheus + Loki | Retención corta y límites; Grafana con 1 réplica |
| Alertas duplicadas | Deduplicar por `fingerprint` |

## Cómo se verifica

- `pytest` del webhook con payloads reales de Alertmanager (firing, repetido, resolved).
- Cronometrar la demo de [spec.md](spec.md#demo-de-cierre) tres veces: siempre ≤ 60 s.

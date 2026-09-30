# Plan 010 · Dashboards y métricas del servicio

> Cómo se construye [la spec](spec.md).

## Stack

Hub (FastAPI + React) para KPI de negocio; Prometheus HTTP API para disponibilidad y latencia;
Grafana para el detalle técnico (enlazado, no embebido en el portal del cliente).

## Cálculos (`backend/app/services/kpi.py`)

| KPI | Cálculo | Fuente |
|---|---|---|
| Disponibilidad del mes | `avg_over_time(probe_success{client="<c>"}[<mes>])` | Prometheus |
| Latencia p95 | `histogram_quantile(0.95, ...)` de Traefik | Prometheus |
| Cumplimiento SLA | tickets + incidentes resueltos antes de `resolution_due_at` ÷ total | Hub |
| MTTR | promedio de `mttr_minutes` del mes | Hub |
| Carga por técnico | Σ `work_logs.hours` ÷ horas disponibles del mes | Hub |
| Costo por cliente | Σ horas × costo hora (de la spec 000) | Hub |

`integrations/prometheus.py`: `query(promql, time)` con timeout corto; si Prometheus no responde, la
tarjeta muestra "sin datos" y el resto del dashboard funciona (regla de desacople).

## API

| Método | Ruta | Rol |
|---|---|---|
| GET | `/api/dashboard/agency?month=` | agencia |
| GET | `/api/dashboard/client/{id}?month=` | agencia, cliente dueño |

## Pantallas

| Pantalla | Ruta | Contenido |
|---|---|---|
| Consola | `/agencia` | Tabla por cliente + tarjetas de KPI + carga por técnico |
| Portal | `/portal` | Estado actual, disponibilidad vs. objetivo, incidentes y solicitudes del mes |
| Grafana | enlace | Dashboard "Sitios de clientes" (disponibilidad, latencia, 4xx/5xx) |

Diseño en blanco y negro: el estado se comunica con texto e ícono (✓ / ! / ✗), no con color.
Textos del portal desde un único módulo `frontend/src/texts/cliente.ts` alineado con el glosario.

## Riesgos

| Riesgo | Respuesta |
|---|---|
| Consultas lentas a Prometheus | Cachear 60 s en el Hub |
| Jerga que se cuela en el portal | Revisión del PR contra el glosario |

## Cómo se verifica

- `pytest` de `kpi.py` con datos semilla conocidos (resultado esperado a mano).
- Prueba con 3 personas no técnicas (CA-5), anotada en `context.md`.

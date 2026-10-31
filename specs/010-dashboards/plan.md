# Plan 010 · Dashboards y métricas del servicio

> Cómo se construye [la spec](spec.md). No agrega servicios: lee del Hub y de Prometheus (que ya instala la 008).

## Punto de partida

| Pieza | Estado | Dónde |
|---|---|---|
| Tickets, SLA y `work_logs` (horas por técnico) | Hecho (004) | `models/ticket.py`, `models/work_log.py`, `services/sla.py` |
| Planes con `slo_availability` | Hecho (000/003) | `seed/plans.json`, `models/plan.py` |
| Sesión, rol y alcance por cliente | Hecho (007) | `require_agency`, `client_scope` |
| Estado del servicio y versiones | Hecho (005) | `routers/services.py`, `deployments` |
| Sondas, `probe_success`, Grafana | Se construye en la 008 | `observability/` |
| Incidentes y MTTR | 008 y 009 | `incidents`, `mttr_minutes` |
| Pantallas de la consola y del portal | Parcial | `pages/agencia/*`, `pages/portal/TicketList.tsx` (no hay `/agencia` de inicio con KPI ni portal de inicio) |
| `docs/kpi.md` | **No existe** (tarea T10 de la 000, abierta) | ver «KPI provisionales» |

## KPI provisionales

La spec 000 aún no cierra las fórmulas ni los precios. Para no bloquear, esta spec crea `docs/kpi.md` en su
primera tarea con las fórmulas de abajo marcadas **«provisional, validan Industrial»**. Cuando la 000 cierre
su T10, solo cambia ese archivo y `seed/kpi_params.json`; el código no cambia.

`seed/kpi_params.json` (nuevo, leído por `kpi.py`):

```json
{ "hourly_cost": 25000, "technician_monthly_hours": 120, "currency": "COP", "at_risk_ratio": 0.8 }
```

Son valores de trabajo, no del modelo de negocio; se documentan como supuestos en `docs/kpi.md`.

## Cálculos (`backend/app/services/kpi.py`)

El mes se toma en America/Bogota (de 00:00 del día 1 al inicio del mes siguiente) y se convierte a UTC para
consultar. Todas las funciones reciben `(db, client_id, month)` y devuelven valores simples.

| KPI | Cálculo | Fuente |
|---|---|---|
| Disponibilidad del mes | `avg_over_time(probe_success{client="<c>"}[<mes>])` × 100; si Prometheus no responde o no hay serie, `None` («sin datos») | Prometheus |
| Cumple el objetivo | disponibilidad ≥ `plans.slo_availability` del cliente | Hub + Prometheus |
| Latencia p95 | `histogram_quantile(0.95, sum by (le) (rate(traefik_service_request_duration_seconds_bucket{service=~"cliente-<c>-.*"}[5m])))` | Prometheus (métrica de Traefik de la 008) |
| Cumplimiento de SLA | (solicitudes + incidentes cerrados o mitigados dentro de su plazo de solución) ÷ (los terminados del mes); `None` si no hay ninguno | Hub |
| MTTR | promedio de `mttr_minutes` de los incidentes `mitigado`/`cerrado` del mes; `None` si no hay | Hub (009) |
| Solicitudes abiertas / cerradas | conteo por estado canónico | Hub |
| Horas por cliente | Σ `work_logs.hours` de sus solicitudes en el mes | Hub |
| Costo por cliente | horas × `hourly_cost` | Hub + `seed/kpi_params.json` |
| Carga por técnico | Σ `work_logs.hours` del usuario en el mes ÷ `technician_monthly_hours` | Hub |

`integrations/prometheus.py`: `query(promql, at)` con timeout de 2 s, usando `PROMETHEUS_URL` (variable nueva en
`config.py`, `.env.example`, `docker-compose.yml` y `gitops/hub/api.yaml`). Si falla, devuelve `None` y no
lanza. Caché en memoria de 60 s por consulta y mes.

## API

| Método | Ruta | Rol | Qué devuelve |
|---|---|---|---|
| GET | `/api/dashboard/agency?month=YYYY-MM` | agencia | KPI por cliente, totales y carga por técnico |
| GET | `/api/dashboard/client/{id}?month=YYYY-MM` | agencia, cliente dueño | Estado, disponibilidad vs. objetivo, incidentes y solicitudes del mes (sin costo ni horas) |
| GET | `/api/dashboard/client/{id}/incidents?month=YYYY-MM` | agencia, cliente dueño | Fallas del mes del portal: título, estado y fecha de inicio, sin técnicos ni datos internos |
| GET | `/api/dashboard/client/{id}/series?month=YYYY-MM` | agencia | Puntos de disponibilidad y latencia cada 5 min para las gráficas |

`month` por omisión es el mes actual. El cliente de otro cliente → 404 (spec 007). La respuesta del portal no
trae costo, horas ni nombres de técnicos.

## Pantallas

| Pantalla | Ruta | Contenido |
|---|---|---|
| Panel de la agencia | `/agencia` | Tabla por cliente + tarjetas de KPI + carga por técnico; enlace al detalle técnico |
| Detalle técnico | `/agencia/clientes/:id/metricas` | Gráficas simples de disponibilidad y latencia (SVG propio, sin librería), p95, enlace a Grafana |
| Inicio del portal | `/portal` | Estado actual, disponibilidad vs. objetivo, incidentes y solicitudes del mes |

Diseño en blanco y negro: el estado se comunica con texto e ícono (✓ / ! / ✗), no con color. Los textos del
portal viven en un único módulo `frontend/src/texts/cliente.ts` tomado del glosario. Las gráficas son
SVG escritos a mano (no se agrega librería de gráficos: pocas series, sin dependencias nuevas).

## Riesgos

| Riesgo | Respuesta |
|---|---|
| Prometheus lento o apagado | Timeout de 2 s, caché de 60 s y «sin datos» (CA-8) |
| Fórmulas que cambian al cerrar la 000 | `docs/kpi.md` y `seed/kpi_params.json` son la fuente; el código solo las lee |
| Jerga que se cuela en el portal | Todos los textos salen de `texts/cliente.ts` y se revisan contra el glosario en el PR |
| Disponibilidad del mes con pocos datos (monitoreo recién encendido) | Se muestra el periodo cubierto («desde el 24 oct») en vez de un % del mes completo |
| Cliente ve datos de otro | `client_scope` en cada ruta y prueba explícita |

## Cómo se verifica

- `pytest` de `kpi.py` con datos semilla de resultado calculado a mano (horas, tickets, incidentes con MTTR
  conocido) y con `integrations/prometheus.py` simulado (respuesta, vacío y error).
- Prueba de las rutas protegidas: cliente ajeno → 404; el portal no trae costo.
- Prueba con 3 personas no técnicas (CA-5), anotada en `context.md` de esta carpeta.

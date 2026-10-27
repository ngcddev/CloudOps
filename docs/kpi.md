# KPIs del servicio

> Fórmulas de los indicadores que muestran la consola de la agencia y el portal del cliente. Entrega a las
> specs **010** (dashboards y métricas) y **013** (reportes operativo y ejecutivo).
> *Revisado y aprobado por Industrial (26 oct 2026).*

## Regla

Cada KPI tiene tres partes: **fórmula**, **fuente de datos** y **meta** medible. Si la fuente todavía no
existe (por ejemplo, Prometheus no responde), el KPI se calcula como `null` y la pantalla muestra «sin
datos», nunca un valor inventado.

## Parámetros de trabajo

Valores de trabajo que las fórmulas necesitan. Se guardan en `seed/kpi_params.json` (leído por
`backend/app/services/kpi.py`) y se documentan como supuestos; **ninguno se hardcodea en el código**.

| Parámetro | Valor aprobado | Unidad |
|---|---|---|
| `hourly_cost` | 25000 | COP / hora de soporte |
| `technician_monthly_hours` | 120 | horas de soporte por técnico al mes |
| `at_risk_ratio` | 0.8 | proporción de carga que considera riesgo |
| `currency` | COP | moneda de los costos |

## KPIs del mes (America/Bogota: del día 1 de 00:00 al inicio del mes siguiente)

| # | KPI | Fórmula | Fuente | Meta |
|---|---|---|---|---|
| 1 | **Disponibilidad del mes** | `avg_over_time(probe_success{client="<c>"}[<mes>]) × 100` | Prometheus (Blackbox Exporter, job `sitios`; spec 008) | Disponibilidad del plan del cliente: 99,0 % (Básico), 99,5 % (Estándar), 99,9 % (Premium) |
| 2 | **Cumple el objetivo** | Disponibilidad del mes ≥ `plans.slo_availability` del cliente | Hub (plan) + Prometheus | Sí / No por cliente |
| 3 | **Latencia p95** | `histogram_quantile(0.95, sum by (le) (rate(traefik_service_request_duration_seconds_bucket{service=~"cliente-<c>-.*"}[5m])))` | Prometheus + métrica de Traefik de la spec 008 | Medir p95 por sitio; latencia elevada inicia mejora |
| 4 | **Cumplimiento de SLA** | (casos resueltos dentro del plazo ÷ casos terminados del mes) × 100; sin terminados → `null` | Hub: tickets con cierre (004) | 100 % dentro del plazo de respuesta y solución |
| 5 | **MTTR** | Promedio de (`mitigación − inicio`) en minutos de los incidentes del mes con estado `mitigado`/`cerrado`; sin incidentes → `null` | Hub: incidentes (008, 009) | Medir; con cero incidentes → «sin incidentes este mes», no 0 |
| 6 | **Solicitudes abiertas / cerradas** | Conteo por estado canónico (`abierto → en_progreso → en_espera → resuelto → cerrado`) del mes | Hub: tickets (004) | — |
| 7 | **Horas por cliente** | Σ `work_logs.hours` de las solicitudes del cliente en el mes | Hub: `work_logs` (004) | Horas incluidas del plan |
| 8 | **Costo por cliente** | Horas por cliente × `hourly_cost` | Hub (horas) + `seed/kpi_params.json` (`hourly_cost`) | — |
| 9 | **Carga por técnico** | Σ `work_logs.hours` del técnico en el mes ÷ `technician_monthly_hours`; carga > `at_risk_ratio` (0,8) del técnico → señal de riesgo | Hub (horas) + `seed/kpi_params.json` (`technician_monthly_hours`, `at_risk_ratio`) | ≤ `technician_monthly_hours` |

## KPIs de CA-2 · Consola: carga por técnico

La carga se reporta por técnico de la agencia (rol `agencia`): horas registradas en el mes frente a las
horas disponibles del plan de soporte. Se considera **riesgo** cuando la carga supera el `at_risk_ratio`
(0,8) de `technician_monthly_hours`.

## KPIs de CA-4 · Portal del cliente

El portal no muestra costo, horas ni nombres de técnicos (CA-7): solo estado actual, disponibilidad del
mes frente al objetivo, incidentes y solicitudes del mes, con los textos del glosario.

## Verificación

- El JSON de `seed/kpi_params.json` debe ser válido y cada KPI de CA-1 y CA-2 debe tener fórmula, fuente y
  meta en esta tabla.
- La implementación (`backend/app/services/kpi.py`) usa exactamente estas fórmulas; si la 000 cierra la T10,
  el cambio se hace primero en este documento y en el JSON.

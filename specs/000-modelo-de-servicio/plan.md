# Plan 000 · Modelo de servicio

> Cómo se produce [la spec](spec.md). Es trabajo de proceso: el resultado son documentos y archivos
> semilla, no código.

## Entregables

| Entregable | Formato | Ruta |
|---|---|---|
| Entrevistas (2–3) | Notas con preguntas y hallazgos | `specs/000-modelo-de-servicio/context.md` |
| Fichas de persona | Tabla por actor | `docs/personas.md` |
| Proceso AS-IS / TO-BE | Diagrama (Mermaid en Markdown) | `docs/proceso.md` |
| Planes | JSON | `seed/plans.json` |
| Matriz P1–P4 y SLA | JSON | `seed/priority_matrix.json`, `seed/sla_policies.json` |
| Escalamiento | Tabla en Markdown | `docs/proceso.md#escalamiento` |
| KPI | Tabla con fórmula, fuente y meta | `docs/kpi.md` |

## Propuesta de partida (de la constitución)

| Plan | SLO mensual | Atención | CPU / RAM | Precio (COP/mes, ficticio) | Horas incluidas |
|---|---|---|---|---|---|
| Básico | 99,0 % | Lun–Vie 8:00–18:00 | 250m / 256Mi | a definir | a definir |
| Estándar | 99,5 % | Lun–Sáb 7:00–20:00 | 500m / 512Mi | a definir | a definir |
| Premium | 99,9 % | 24/7 | 1000m / 1Gi | a definir | a definir |

| Prioridad | Respuesta | Solución |
|---|---|---|
| P1 | 15 min | 4 h |
| P2 | 1 h | 8 h |
| P3 | 4 h | 24 h |
| P4 | 8 h | 72 h |

Decisión abierta: si el reloj de P1 corre 24/7 en todos los planes (recomendado: sí, una caída total
siempre es crítica) y P2–P4 solo en horario del plan.

## Formato de los archivos semilla

```jsonc
// seed/plans.json
[{ "code": "basico", "name": "Básico", "slo_availability": 99.0,
   "support_hours": "lun-vie 08:00-18:00", "cpu_quota": "250m", "memory_quota": "256Mi",
   "monthly_price": 0, "included_hours": 0 }]
```

```jsonc
// seed/sla_policies.json
[{ "priority": "P1", "response_minutes": 15, "resolution_minutes": 240, "clock": "24x7" }]
```

```jsonc
// seed/priority_matrix.json
{ "impact": ["alto", "medio", "bajo"], "urgency": ["alta", "media", "baja"],
  "matrix": { "alto": { "alta": "P1", "media": "P2", "baja": "P3" } } }
```

## KPI (borrador de fórmulas)

| KPI | Fórmula | Fuente |
|---|---|---|
| Cumplimiento de SLA | casos resueltos dentro del SLA ÷ casos resueltos | tickets e incidentes (004, 008) |
| MTTR | promedio(hora de mitigación − hora de inicio) de incidentes | incidentes (008, 009) |
| Disponibilidad | 1 − minutos caído ÷ minutos del mes | Prometheus (008, 010) |
| Tickets por cliente | conteo de tickets del mes por cliente | tickets (004) |
| Carga por técnico | horas registradas ÷ horas disponibles | tickets con horas (004, 010) |
| Costo por plan | horas × costo hora ÷ clientes del plan | tickets + planes (010) |

## Contratos con otras specs

- Entrega a **001**: `seed/plans.json`.
- Entrega a **003**: cuota de CPU/RAM por plan (ResourceQuota).
- Entrega a **004** y **008**: `seed/priority_matrix.json`, `seed/sla_policies.json`, reglas de escalamiento.
- Entrega a **010** y **013**: `docs/kpi.md`.

## Riesgos

| Riesgo | Respuesta |
|---|---|
| No se consiguen entrevistas antes del 2 oct | Usar la propuesta de la constitución y validar después |
| KPI que el Hub no puede medir | Cada KPI debe nombrar su fuente de datos; si no tiene, se descarta |

## Cómo se verifica

- Revisión del equipo: cada KPI tiene fuente y cada prioridad tiene ejemplo.
- La spec 001 carga `seed/plans.json` sin cambios.

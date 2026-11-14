# KPI del servicio

> Cada KPI tiene fórmula, fuente del dato, meta y frecuencia. Las metas de SLA y SLO salen de
> `seed/sla_policies.json` y `seed/plans.json`; donde dice "propuesta" falta confirmarla con el equipo.
> Principio 8: lo que llega al portal o a los reportes del cliente usa la columna "Cómo lo ve el
> cliente" del [glosario](glosario.md). La consola de la agencia usa los términos técnicos.

**Reloj del SLA.** Cada prioridad mide sus tiempos con el `clock` de `sla_policies`: P1 corre 24x7;
P2, P3 y P4 corren solo dentro del horario de atención del plan.

## Servicio al cliente (SLA y SLO)

| KPI | Fórmula | Fuente | Meta | Frecuencia | Cómo lo ve el cliente |
|---|---|---|---|---|---|
| Disponibilidad | (min del periodo − min en estado `caido`) / min del periodo × 100 | Blackbox Exporter → Prometheus | SLO del plan: Básico 99,0 % · Estándar 99,5 % · Premium 99,9 % | Mensual | "Su sitio se mantuvo disponible dentro del objetivo acordado." |
| Cumplimiento de respuesta | casos con respuesta ≤ `response_minutes` de su prioridad / casos totales × 100 (respuesta = paso a `en_progreso`) | Hub (tickets e incidentes) + `sla_policies` | ≥ 95 % (propuesta) | Mensual | — |
| Cumplimiento de solución | casos con solución ≤ `resolution_minutes` / casos totales × 100 (solución = `resuelto` en ticket, `mitigado` en incidente) | Hub (tickets e incidentes) + `sla_policies` | ≥ 90 % (propuesta) | Mensual | — |
| MTTA (tiempo medio de respuesta) | promedio de (hora de `en_progreso` − hora de apertura) | Hub | P1 ≤ 15 min · P2 ≤ 60 · P3 ≤ 240 · P4 ≤ 480 | Por caso y mensual | — |
| MTTR (tiempo medio de recuperación) | promedio de (hora de `mitigado` − hora de inicio del incidente) | Hub (incidentes) | P1 ≤ 240 min | Por incidente y mensual | "Tiempo que tardamos en recuperar su sitio." |

Tolerancia de caída por 30 días: Básico 432 min (7,2 h) · Estándar 216 min (3,6 h) · Premium 43 min.
Solo el estado `caido` cuenta como indisponible; `degradado` no (propuesta).

## Cambios y despliegues

| KPI | Fórmula | Fuente | Meta | Frecuencia | Cómo lo ve el cliente |
|---|---|---|---|---|---|
| Tasa de cambios fallidos | cambios `desplegada` que terminaron en rollback / cambios `desplegada` × 100 | Argo CD + historial de Git | ≤ 10 % (propuesta) | Mensual | — |
| Tiempo de ciclo del cambio | fecha de `desplegada` − fecha de `aprobada` | Hub (solicitudes de cambio) + Argo CD | ≤ 1 día hábil (propuesta) | Mensual | — |
| Cambios detenidos por seguridad | solicitudes `rechazada` por la puerta de seguridad / solicitudes enviadas × 100 | Gitea Actions + Hub | Informativo (se busca que baje) | Mensual | "Una actualización fue detenida antes de publicarse por controles de seguridad." |

## Calidad técnica

| KPI | Fórmula | Fuente | Meta | Frecuencia |
|---|---|---|---|---|
| Latencia p95 | percentil 95 del tiempo de respuesta del sitio | Traefik → Prometheus | < 800 ms (propuesta) | Semanal |
| Tasa de errores 5xx | respuestas 5xx / respuestas totales × 100 | Logs de Nginx → Loki | < 1 % (propuesta) | Semanal |
| Formularios fallidos | formularios con error / formularios recibidos × 100 | Métrica del backend (OpenTelemetry) | < 2 % (propuesta) | Mensual |

Los formularios solo aplican a la plantilla "Landing + formulario" (Dental Popayán).

## Costo y capacidad

| KPI | Fórmula | Fuente | Meta | Frecuencia |
|---|---|---|---|---|
| Horas consumidas vs. incluidas | horas de soporte usadas / `included_hours` del plan × 100 | Hub (registro de horas) | ≤ 100 % del plan | Mensual |
| Costo de atención por cliente | horas usadas × costo por hora | Hub + tarifa de la agencia | Menor al precio mensual del plan | Mensual |
| Margen por cliente | (`monthly_price` − costo de atención) / `monthly_price` × 100 | Hub + `plans.json` | ≥ 30 % (propuesta) | Mensual |

## Pendientes

- [ ] Confirmar las metas marcadas como "propuesta".
- [x] Precio y horas de los 3 planes cerrados (propuesta; confirmar con el equipo).
- [x] Tarifa por hora de la agencia: 40.000 COP (propuesta; las entrevistas no traen cifras).
- [ ] Verificar que cada fuente exista cuando llegue su módulo (Prometheus, Loki, OpenTelemetry).
## Supuestos de costo (propuesta del equipo)

Las entrevistas de `context.md` no registran precios ni tarifas, así que estas cifras son supuestos
para la demo y deben validarse con la agencia o el docente.

| Plan | Precio mensual | Horas incluidas | Costo de atención (40.000 × horas) | Margen si se usan todas |
|---|---|---|---|---|
| Básico | 180.000 COP | 2 | 80.000 COP | 56 % |
| Estándar | 350.000 COP | 6 | 240.000 COP | 31 % |
| Premium | 700.000 COP | 12 | 480.000 COP | 31 % |

Estándar y Premium quedan justo sobre la meta de margen (≥ 30 %); si suben las horas incluidas o baja el precio, el margen se pierde.
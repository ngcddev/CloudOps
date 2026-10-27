# Tareas 010 · Dashboards y métricas del servicio

> Cada tarea: una acción con verbo · se comprueba en minutos · menos de un día · se integra sola.
> Rama por tarea: `feat/010-tNN-slug`. Poner el nombre de quien la toma entre corchetes.
>
> Fechas: módulo 4 del 24 oct al 3 nov (sustentación). Meta de esta spec: **1 nov** (sin IA no es parte del
> caso del 31 oct; la prueba con personas y la demo son el 2 de nov).

## Cómo repartirlo

| Carril | Tareas | Necesita el clúster | Puede empezar |
|---|---|---|---|
| Definición (Industrial) | T01–T02 | No | Ya |
| Backend con datos del Hub | T03–T08 | No | Ya (004 y 007 están hechas); MTTR real llega con la 009 |
| Backend con Prometheus | T09–T11 | Sí | Cuando la 008 tenga Prometheus (T22) |
| Frontend | T12–T17 | No (datos de prueba hasta que la API responda) | Ya, con T12 |
| Validación | T18–T19 | Sí (T18) | Cuando cierren los carriles anteriores |

## Definición

- [x] T01 · Crear `docs/kpi.md` con las fórmulas de la tabla del plan marcadas «provisional, valida Industrial» y `seed/kpi_params.json` con `hourly_cost`, `technician_monthly_hours` y `at_risk_ratio` — **Verifica:** el JSON es válido y cada KPI de CA-1 y CA-2 tiene fórmula, fuente y meta en el documento. [Andres]
- [ ] T02 · Revisar con Industrial las fórmulas provisionales y registrar los cambios en `docs/kpi.md` — **Verifica:** el documento queda sin la marca «provisional» o con los cambios pedidos anotados. [ ]

## Backend · datos del Hub

- [x] T03 · Escribir `services/kpi.py` con el mes en America/Bogota y las funciones de solicitudes abiertas/cerradas y cumplimiento de SLA — **Verifica:** `pytest` con tickets semilla: 4 cerrados dentro del plazo y 1 fuera dan 80 %; sin terminados da `None`. [Andres]
- [x] T04 · Agregar horas y costo por cliente (Σ `work_logs.hours` × `hourly_cost`) — **Verifica:** `pytest`: 3 horas + 2 horas en solicitudes de La Sazón a 25 000 por hora dan 125 000. [Andres]
- [x] T05 · Agregar la carga por técnico (horas del mes ÷ `technician_monthly_hours`) — **Verifica:** `pytest`: 30 h registradas con 120 disponibles dan 25 %. [Andres]
- [x] T06 · Agregar el MTTR del mes desde los incidentes `mitigado`/`cerrado` — **Verifica:** `pytest`: incidentes de 6 y 10 min dan 8 min; sin incidentes da `None` (CA-9). [Andres]
- [x] T07 · Crear `GET /api/dashboard/agency?month=` — **Verifica:** `pytest`: devuelve los 3 clientes con sus KPI y la carga de los técnicos; como cliente → 403. [Andres]
- [x] T08 · Crear `GET /api/dashboard/client/{id}?month=` sin costo, horas ni nombres de técnicos — **Verifica:** `pytest`: La Sazón ve lo suyo, pedir el de El Tornillo → 404, y la respuesta no contiene `cost` ni `hours` (CA-7). [Andres]

## Backend · Prometheus

- [x] T09 · Escribir `integrations/prometheus.py` con `query` (timeout 2 s, caché de 60 s, `None` si falla) y agregar `PROMETHEUS_URL` a `config.py`, `.env.example`, `docker-compose.yml` y `gitops/hub/api.yaml` — **Verifica:** `pytest` con respuesta simulada, vacía y con error: devuelve valor, `None` y `None` sin lanzar. [Andres]
- [x] T10 · Sumar disponibilidad del mes, «cumple el objetivo» y latencia p95 a `kpi.py` y a los dos dashboards — **Verifica:** `pytest` con Prometheus simulado: 99,2 % contra un SLO de 99,0 cumple y contra 99,5 no; con Prometheus caído el dashboard responde 200 con `null` (CA-8). [Andres]
- [x] T11 · Crear `GET /api/dashboard/client/{id}/series?month=` con puntos de disponibilidad y latencia cada 5 min — **Verifica:** en el clúster con la 008, la serie de La Sazón muestra el hueco de la caída de la demo. [Andres]

## Frontend

- [x] T12 · Agregar a `frontend/src/api.ts` los tipos y llamadas de dashboards, con datos de prueba si la API no responde — **Verifica:** `tsc` sin errores. [Andres]
- [ ] T13 · Crear `frontend/src/texts/cliente.ts` con los textos del portal tomados del glosario (disponibilidad dentro y por debajo del objetivo, sitio caído, sin datos, sin incidentes) — **Verifica:** cada frase coincide con una fila de [`docs/glosario.md`](../../docs/glosario.md). [ ]
- [ ] T14 · Crear el panel de la agencia en `/agencia` con la tabla por cliente, las tarjetas de KPI y la carga por técnico, con texto e ícono para el estado — **Verifica:** con datos de prueba aparecen los 3 clientes y «sin datos» cuando un valor es nulo (CA-1, CA-2, CA-8). [ ]
- [ ] T15 · Crear `/agencia/clientes/:id/metricas` con las gráficas SVG de disponibilidad y latencia y el enlace a Grafana — **Verifica:** la gráfica con datos de prueba muestra el hueco de una caída y el enlace abre `grafana.hub.local` (CA-6). [ ]
- [ ] T16 · Crear el inicio de `/portal` con estado actual, disponibilidad vs. objetivo, incidentes y solicitudes del mes, solo con `texts/cliente.ts` — **Verifica:** `git grep -nEi "P1|MTTR|Prometheus|rollback|deploy" frontend/src/pages/portal` no encuentra jerga (CA-4). [ ]
- [ ] T17 · Habilitar «Inicio» en los menús de la consola y del portal — **Verifica:** entrar como Sofía lleva a `/agencia` y como Marta a `/portal`, cada una con lo suyo. [ ]

## Validación

- [ ] T18 · Conectar todo en el clúster y repetir la caída de la demo de la 009 — **Verifica:** la consola y el portal de La Sazón muestran el incidente, su MTTR y la disponibilidad por debajo o dentro del objetivo según corresponda; apagar Prometheus deja «sin datos» sin errores (CA-1, CA-4, CA-8). [ ]
- [ ] T19 · Hacer la prueba con 3 personas no técnicas y anotarla en `context.md` de esta carpeta — **Verifica:** al menos 2 explican correctamente el estado de su sitio (CA-5). [ ]

## Cierre

- [ ] T20 · Demo: consola, carga y costo, detalle técnico, portal de La Sazón y Prometheus apagado — **Verifica:** todos los criterios de [spec.md](spec.md#criterios-de-aceptación). [ ]

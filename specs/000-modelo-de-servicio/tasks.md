# Tareas 000 · Modelo de servicio

> Cada tarea: una acción con verbo · se comprueba en minutos · menos de un día · se integra sola.
> Rama por tarea: `docs/000-tNN-slug`. Poner el nombre de quien la toma entre corchetes.

## Levantamiento

- [X] T01 · Preparar la guía de entrevista (10 preguntas) — **Verifica:** guía en `context.md`. [andrea]
- [X] T02 · Entrevistar a 2–3 agencias o freelancers de Popayán — **Verifica:** notas por entrevista en `context.md`. [andrea ]
- [X] T03 · Escribir las fichas de persona de los 3 actores humanos — **Verifica:** `docs/personas.md`. [ andrea]

## Proceso

- [X] T04 · Dibujar el proceso AS-IS de solicitud y de falla — **Verifica:** diagrama en `docs/proceso.md`. [andrea ]
- [X] T05 · Dibujar el proceso TO-BE con estados canónicos — **Verifica:** usa los estados de la constitución. [andrea ]
- [X] T06 · Definir reglas de escalamiento al 50/80/100 % del SLA — **Verifica:** tabla en `docs/proceso.md`. [andrea]

## Reglas del servicio

- [x] T07 · Cerrar la matriz P1–P4 con un ejemplo por cliente — **Verifica:** `seed/priority_matrix.json` válido. Hecho el 31 oct 2026: la matriz es válida y `docs/prioridades.md` trae 4 ejemplos por cada uno de los 3 clientes (12), todos coherentes con la matriz. Redactado por Sistemas, sin revisión de Industrial.
- [x] T08 · Cerrar tiempos de SLA y reloj por prioridad — **Verifica:** `seed/sla_policies.json` válido. Hecho el 31 oct 2026: `seed/sla_policies.json` es válido y coincide con la propuesta del plan (P1 15 min / 4 h en 24x7; P2, P3 y P4 en el horario del plan). Cerrado por Sistemas, sin revisión de Industrial.
- [x] T09 · Cerrar los 3 planes con precio, cuota y horas — **Verifica:** `seed/plans.json` válido. Hecho el 31 oct 2026: `seed/plans.json` es válido, con precio mensual ficticio y horas incluidas por plan (Básico 150.000 y 4 h, Estándar 350.000 y 10 h, Premium 700.000 y 20 h). Cerrado por Sistemas, sin revisión de Industrial.
- [x] T10 · Escribir la tabla de KPI con fórmula, fuente y meta — **Verifica:** `docs/kpi.md`. Verificado el 31 oct 2026: `docs/kpi.md` tiene los 9 KPI con fórmula, fuente y meta, aprobado por Industrial el 26 oct.

## Cierre

- [ ] T11 · Demo: clasificar 3 casos en vivo y mostrar planes y KPI — **Verifica:** todos los criterios de [spec.md](spec.md#criterios-de-aceptación). [ ]

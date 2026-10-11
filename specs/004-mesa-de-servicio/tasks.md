# Tareas 004 · Mesa de servicio: tickets y prioridad

> Cada tarea: una acción con verbo · se comprueba en minutos · menos de un día · se integra sola.
> Rama por tarea: `feat/004-tNN-slug`. Poner el nombre de quien la toma entre corchetes.
>
> Es spec de producto: corre en `docker compose`, sin herramientas de plataforma nuevas. El frontend puede
> empezar con datos de prueba mientras la API no responde, como en la 001.
> La matriz P1–P4 la cierra el industrial en 000-T07; T01 deja una versión que el backend puede usar ya.

## Insumos de la spec 000

- [x] T01 · Dejar `seed/priority_matrix.json` con las 9 combinaciones impacto × urgencia (propuesta si 000-T07 aún no cierra) — **Verifica:** el JSON tiene `impact`, `urgency` y `matrix` completos y `pytest` lo carga sin error. [ERIC]

## Modelo de datos

- [x] T02 · Crear la tabla `users` con migración y `seed/users.json` (un técnico de la agencia y uno por cliente, sin contraseña) — **Verifica:** `alembic upgrade head` sin errores y la tabla queda con 4 usuarios al arrancar de cero. [ANDRES]
- [x] T03 · Crear las tablas `tickets`, `ticket_events` y `work_logs` con migración — **Verifica:** `alembic upgrade head` y `alembic downgrade -1` sin errores. [ANDRES]

## Reglas de negocio (`backend/app/services/`)

- [x] T04 · Escribir `priority.py` con `classify(impact, urgency)` leyendo la matriz — **Verifica:** `pytest` cubre las 9 combinaciones y rechaza valores inválidos. [ANDRES]
- [x] T05 · Escribir `ticket_flow.py` con las transiciones válidas de `abierto → en_progreso → en_espera → resuelto → cerrado` — **Verifica:** `pytest` acepta las válidas, rechaza los saltos (por ejemplo `abierto → resuelto`) y fija `first_response_at` al pasar a `en_progreso`. [ ]
- [x] T06 · Escribir `sla.py` con `due_dates` para el reloj 24/7 de P1 — **Verifica:** `pytest`: un P1 creado a las 14:00 vence respuesta 14:15 y solución 18:00. [ANDRES]
- [x] T07 · Extender `due_dates` al horario del plan (America/Bogota, guardando UTC) — **Verifica:** `pytest` con casos de viernes tarde, fin de semana y fuera de horario en cada plan. [ANDRES]
- [x] T08 · Escribir `sla_state(ticket, now)` con `a_tiempo`, `en_riesgo` (≥ 80 % del plazo) y `vencido` — **Verifica:** `pytest` cubre los tres estados y el borde exacto del 80 %. [ANDRES]

## API

- [x] T09 · Crear `POST /api/tickets`, `GET /api/tickets` (filtros por cliente, estado y prioridad) y `GET /api/tickets/{id}` con historial — **Verifica:** desde `/docs` se crea un ticket y aparece en la lista con su detalle. [ANDRES]
- [ ] T10 · Crear `POST /api/tickets/{id}/classify` que asigna la prioridad, calcula las horas límite y permite corregirla dejando el motivo — **Verifica:** impacto alto + urgencia media da P2 con sus fechas, y la corrección sin motivo responde 422. [ ]
- [ ] T11 · Crear `POST /api/tickets/{id}/assign` y `POST /api/tickets/{id}/transition` registrando cada cambio en `ticket_events` — **Verifica:** un salto inválido responde 409 y el historial muestra hora (UTC) y usuario de cada cambio. [ ]
- [ ] T12 · Crear `POST /api/tickets/{id}/work-logs` — **Verifica:** registrar 1,5 h suma 1,5 en el detalle; horas negativas dan 422. [ ]
- [ ] T13 · Ocultar al cliente las notas internas y devolver los estados en el lenguaje del [glosario](../../docs/glosario.md) — **Verifica:** la misma solicitud, consultada como cliente, no trae eventos con `internal = true`. [ ]
- [ ] T14 · Agregar pruebas de punta a punta del ciclo del ticket con pytest — **Verifica:** `docker compose exec api pytest` en verde. [ ]

## Pantallas

- [ ] T15 · Agregar a `frontend/src/api.ts` los tipos y llamadas de tickets (con datos de prueba si la API no responde) — **Verifica:** `tsc` sin errores. [ ]
- [ ] T16 · Crear la bandeja `/agencia/tickets` con filtros por cliente, prioridad, estado y SLA — **Verifica:** filtrar por P2 deja solo los P2 y cada fila muestra "a tiempo", "en riesgo" o "vencido" con texto e ícono. [ ]
- [ ] T17 · Crear el detalle `/agencia/tickets/:id` para clasificar, asignar, cambiar estado, registrar horas y ver el historial — **Verifica:** clasificar y pasar a `en_progreso` actualiza el historial sin recargar. [ ]
- [ ] T18 · Crear `/portal/solicitudes` con la lista y "Nueva solicitud" usando el selector de cliente de desarrollo — **Verifica:** La Sazón crea una solicitud y solo ve las suyas, en lenguaje simple. [ ]

## Datos semilla

- [ ] T19 · Agregar 3 tickets semilla en distintos estados y prioridades — **Verifica:** `docker compose down -v && docker compose up --build` deja la bandeja con 3 tickets y ninguno es el de la demo. [ ]

## Cierre

- [ ] T20 · Demo: "El menú del domingo no aparece" de La Sazón pasa a P2, se asigna, se resuelve con 1,5 h y el cliente ve "Resuelto" — **Verifica:** todos los criterios de [spec.md](spec.md#criterios-de-aceptación). [ ]

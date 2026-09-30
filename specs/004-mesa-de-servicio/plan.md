# Plan 004 · Mesa de servicio

> Cómo se construye [la spec](spec.md) sobre el esqueleto de la [spec 001](../001-clientes-y-planes/plan.md).

## Stack

FastAPI + PostgreSQL + React (sin herramientas de plataforma nuevas).

## Modelo de datos

| Tabla | Campos |
|---|---|
| `tickets` | `id` · `service_id` FK · `created_by_id` FK users (nullable hasta 007) · `assignee_id` FK users · `title` · `description` · `impact` · `urgency` · `priority` (P1–P4) · `status` · `kind` (`solicitud` / `cambio`) · `response_due_at` · `resolution_due_at` · `first_response_at` · `resolved_at` · `closed_at` · `created_at` |
| `ticket_events` | `id` · `ticket_id` FK · `actor_id` · `type` (`estado`, `prioridad`, `asignacion`, `comentario`) · `from_value` · `to_value` · `note` · `internal` bool · `created_at` |
| `work_logs` | `id` · `ticket_id` FK · `user_id` · `hours` numeric · `note` · `created_at` |
| `users` | `id` · `name` · `email` · `role` · `client_id` (nullable) — se crea aquí sin contraseña; la spec 007 agrega el login |

## Reglas de negocio (`backend/app/services/`)

- `priority.py`: `classify(impact, urgency) -> "P1".."P4"` con `seed/priority_matrix.json`.
- `sla.py`: `due_dates(created_at, priority, plan)`, `sla_state(ticket, now) -> a_tiempo | en_riesgo | vencido`.
  Respeta el reloj de la spec 000 (24/7 o horario del plan).
- `ticket_flow.py`: transiciones válidas; `first_response_at` se fija al pasar a `en_progreso`.

## API

| Método | Ruta | Qué hace |
|---|---|---|
| GET | `/api/tickets?client_id=&status=&priority=` | Lista con estado de SLA |
| POST | `/api/tickets` | Crea (cliente o agencia) |
| GET | `/api/tickets/{id}` | Detalle + historial |
| POST | `/api/tickets/{id}/classify` | Impacto + urgencia → prioridad |
| POST | `/api/tickets/{id}/assign` | Asigna responsable |
| POST | `/api/tickets/{id}/transition` | Cambia estado |
| POST | `/api/tickets/{id}/work-logs` | Registra horas |

## Pantallas

| Pantalla | Ruta | Rol |
|---|---|---|
| Bandeja de tickets | `/agencia/tickets` | agencia: filtros por cliente, prioridad, estado, SLA |
| Detalle del ticket | `/agencia/tickets/:id` | agencia: clasificar, asignar, estados, horas, historial |
| Mis solicitudes | `/portal/solicitudes` | cliente: lista + "Nueva solicitud" |

Mientras no exista la spec 007, el portal usa un selector de cliente de desarrollo.

## Contratos con otras specs

- Entrega a **005**: `kind = cambio` para solicitudes de cambio.
- Entrega a **008**: `sla.py` reutilizado por incidentes.
- Entrega a **010 / 013**: `work_logs` y tiempos para carga, costo y cumplimiento.

## Riesgos

| Riesgo | Respuesta |
|---|---|
| Cálculo de SLA en horario hábil es complejo | Pruebas unitarias con casos fin de semana y fuera de horario |
| Zonas horarias | Guardar UTC, mostrar America/Bogota |

## Cómo se verifica

- `pytest`: matriz de prioridad, transiciones válidas/inválidas, fechas límite por plan.
- Demo de [spec.md](spec.md#demo-de-cierre).

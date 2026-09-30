# seed/ — Datos semilla

Datos ficticios con los que arranca el Hub. El backend los carga (`backend/app/seed.py`) solo si la
base está vacía, así que la demo siempre empieza igual (RNF-11).

Estos archivos son **el contrato** entre la spec 000 (qué datos existen) y la spec 001 (cómo se
guardan y se muestran). Backend y frontend trabajan contra esta forma desde el primer día; si hay
que cambiar un campo, se cambia aquí en un PR que revisan el industrial y el backend.

| Archivo | Qué contiene | Quién decide el contenido | Spec |
|---|---|---|---|
| `plans.json` | Los 3 planes: SLO, horario, cuota CPU/RAM, precio, horas incluidas | Industrial (000-T09) | 000 → 001 |
| `sla_policies.json` | Tiempos de respuesta y solución por prioridad, y cuándo corre el reloj | Industrial (000-T08) | 000 → 001, 004, 008 |
| `clients.json` | La agencia Forja Digital y los 3 clientes con su proyecto y servicio | Backend, con los nombres canónicos | 001 |
| `priority_matrix.json` | Matriz impacto × urgencia → P1–P4 (aún no existe) | Industrial (000-T07) | 000 → 004, 008 |

## Estado actual: propuesta

Los valores vienen de la propuesta de la [constitución](../constitution.md#planes-propuesta-la-spec-000-los-confirma).
El industrial los confirma o ajusta en las tareas de la spec 000. Mientras tanto:

- `monthly_price` e `included_hours` valen `null`, que significa **a definir**. El backend los acepta
  como opcionales y el frontend muestra "Por definir".
- `clock`: P1 corre `24x7` en todos los planes; P2–P4 corren en `horario_plan` (el horario del plan
  del servicio). Es la recomendación del [plan 000](../specs/000-modelo-de-servicio/plan.md); falta
  confirmarla.

## Reglas de los campos

- `plans[].code`: identificador estable (`basico`, `estandar`, `premium`); los demás archivos se
  refieren al plan por este código, nunca por el nombre ni por el `id`.
- `slo_availability`: porcentaje mensual como número (`99.9`, no `"99,9 %"`).
- `support_hours`: `"lun-vie 08:00-18:00"`, `"lun-sab 07:00-20:00"` o `"24x7"`, en hora de Colombia.
- `response_minutes` / `resolution_minutes`: siempre en minutos (4 h = `240`).
- `services[].template`: `landing` o `landing_form` (spec 002).
- `services[].plan_code`: debe existir en `plans.json`.
- Correos con dominio `.test` y teléfonos `+57 300 000 000N`: todo es ficticio.

# Plan 007 · Acceso por roles y auditoría

> Cómo se construye [la spec](spec.md) sobre la API y las pantallas de las specs 001, 004 y 005.
> Sin sobre-diseñar: dos roles, usuarios sembrados, una bitácora de solo inserción.

## Stack

FastAPI + PostgreSQL + React (sin herramientas de plataforma nuevas).

| Pieza | Librería | Por qué |
|---|---|---|
| Hash de contraseñas | `bcrypt` | Directo, sin `passlib` (sin mantenimiento y roto con `bcrypt` ≥ 4.1) |
| Token de sesión | `PyJWT` (HS256) | Reemplaza a `python-jose`, que dejó de mantenerse |
| Sesión en el frontend | Contexto de React + `sessionStorage` | Se borra al cerrar la pestaña |

El login recibe JSON (`email`, `password`), no formulario: así no hace falta `python-multipart`.

## Punto de partida (lo que cambia)

| Hoy | Dónde | Con la 007 |
|---|---|---|
| `viewer_role` y `client_id` en la query deciden qué ve quien llama | `routers/tickets.py` | Salen del token |
| `actor_id`, `created_by_id`, `user_id` en el cuerpo | `schemas/ticket.py` | Los fija la sesión; se quitan |
| `requested_by_id` y `actor_id` en el cuerpo; `require_user` y el chequeo de rol a mano en `approve` | `schemas/change_request.py`, `routers/change_requests.py` | Los fija la sesión; `require_role("agencia")` |
| `CURRENT_USER_ID = 1` y `actor_id: 1` | `frontend/src/api.ts`, `pages/agencia/TicketDetail.tsx`, `pages/agencia/ChangeList.tsx` | Se quitan |
| Selector de cliente de desarrollo | `pages/portal/TicketList.tsx` | El portal muestra el cliente del usuario |
| Cualquiera crea y edita clientes y lee el estado técnico | `routers/clients.py`, `routers/services.py` | Solo `agencia` |

## Modelo de datos

| Tabla | Cambio |
|---|---|
| `users` (existe desde 004) | suma `password_hash` · `is_active` (default `true`) · `last_login_at` |
| `audit_logs` (nueva) | `id` · `user_id` FK (nullable: "Sistema") · `action` · `entity` · `entity_id` · `details` JSON · `ip` · `created_at` |

`audit_logs` es de solo inserción: no hay endpoints de edición ni borrado, y en PostgreSQL la
migración crea un trigger que rechaza `UPDATE` y `DELETE` (en SQLite de pruebas no aplica).

Valores de `action` (se muestran con su etiqueta en la bitácora):

| `entity` | `action` | Dónde se registra |
|---|---|---|
| `ticket` | `cambiar_prioridad` · `asignar` · `cambiar_estado` | `routers/tickets.py` |
| `client` | `crear` · `editar` | `routers/clients.py` |
| `change_request` | `crear` · `aprobar` · `rechazar` | `routers/change_requests.py` |
| `change_request` | `desplegar` · `fallar` (usuario nulo = "Sistema") | `services/deploy_watch.py` |

Una spec nueva suma sus filas a esta tabla con sus propios valores de `entity` y `action`.

## Autenticación y autorización (`backend/app/`)

- `services/auth.py`: `hash_password`, `verify_password`, `create_token(user)`, `decode_token`.
- `deps.py`: `current_user` (lee `Authorization: Bearer`, 401 si falta, venció o el usuario está
  inactivo), `require_role("agencia")` (403) y `client_scope(user)` → `None` para agencia o el
  `client_id` del cliente.
- Token de 60 min con `sub` (id), `role` y `client_id`. Clave en `JWT_SECRET`; si falta, la API no
  arranca.
- Un recurso de otro cliente responde **404** (no se confirma que existe); una acción de agencia
  pedida por un cliente responde **403**.

| Método | Ruta | Rol | Qué hace |
|---|---|---|---|
| POST | `/api/auth/login` | público | Correo + contraseña → token; actualiza `last_login_at` |
| GET | `/api/auth/me` | cualquiera con sesión | Usuario, rol y cliente |

### Permisos por endpoint existente

| Endpoint | `agencia` | `cliente` |
|---|---|---|
| `GET /api/plans`, `GET /api/sla-policies` | sí | sí |
| `GET /api/clients`, `GET /api/clients/{id}` | todos | solo el suyo (otro → 404) |
| `POST/PATCH /api/clients`, proyectos y servicios | sí | 403 |
| `POST /api/tickets` | sí | solo sobre sus servicios (otro → 404) |
| `GET /api/tickets`, `GET /api/tickets/{id}` | todos | solo los suyos, sin notas internas y con estados del glosario (incluidos los eventos de cambio) |
| `classify`, `assign`, `transition`, `work-logs` | sí | 403 |
| `/api/change-requests` (listar, crear, aprobar, rechazar) | sí | 403 (el cliente sigue su cambio en los eventos de su solicitud) |
| `GET /api/services/status`, `GET /api/services/{id}/deployments` | sí | 403 |

## Auditoría

`services/audit.py: record(db, user, action, entity, entity_id, details=None, ip=None)` agrega la
fila a la misma sesión de la acción: si la acción falla (409, 502 de Gitea), no queda registro, y
viceversa. `deploy_watch.check_cycle` la llama con `user=None` en el mismo `commit` que deja el
cambio `desplegada` o `fallida`.

| Método | Ruta | Rol |
|---|---|---|
| GET | `/api/audit-logs?user_id=&entity=&action=&from=&to=` | agencia (más recientes primero, máx. 200) |

## Pantallas

| Pantalla | Ruta | Qué hace |
|---|---|---|
| Inicio de sesión | `/login` | Correo + contraseña; lleva a `/agencia` o a `/portal` según el rol |
| Bitácora | `/agencia/bitacora` | Tabla filtrable por usuario, objeto, acción y fechas (hora de Colombia) |
| Consola y portal | existentes | Nombre del usuario y "Cerrar sesión"; sin sesión → `/login`; con el rol equivocado → su inicio |

`frontend/src/auth.tsx`: contexto con el usuario y el token (en `sessionStorage`); `api.ts` envía
`Authorization` en cada llamada y ante un 401 borra la sesión y vuelve a `/login`.

## Datos semilla y secretos

- `seed/users.json` suma un segundo usuario de agencia (ficticio).
- Las contraseñas no van en el JSON: el seed aplica a todos el valor de `SEED_USER_PASSWORD`
  (hash con `bcrypt`). En `.env.example` va un valor de desarrollo; en k3s, un `Secret` `hub-auth`
  con `JWT_SECRET` y `SEED_USER_PASSWORD` creado por `gitops/hub/crear-secretos.sh`, nunca en el repo.
- El token de Gitea y de Argo CD de la 005 (`hub-gitops-tokens`) no cambia.

## Contratos con otras specs

- Entrega a las specs siguientes: `current_user`, `require_role`, `client_scope` y `audit.record`.
  Cada acción sensible nueva llama a `audit.record` en el mismo commit de la base, y cada endpoint
  nuevo declara su rol (la prueba de T14 falla si no).
- Cierra la nota de la 005 sobre `approve`: el actor sale de la sesión.

## Riesgos

| Riesgo | Respuesta |
|---|---|
| Olvidar el filtro por cliente en un endpoint nuevo | Prueba que recorre las rutas de la app y exige 401 sin token; prueba con usuario de otro cliente por recurso |
| Las pruebas existentes de 001, 004 y 005 se rompen al exigir sesión | Fixtures `as_agency` / `as_client` en `conftest.py` antes de proteger los routers |
| `deploy_watch` corre sin petición ni usuario | `audit.record` acepta `user=None` ("Sistema") |
| Romper las demos de la 004 y la 005 | Se repiten con login al cerrar la spec |

## Cómo se verifica

- `pytest`: 401 sin token o con token vencido, 403 cliente en acción de agencia, 404 al pedir datos
  de otro cliente, una fila en `audit_logs` por cada acción listada y ninguna si la acción falla.
- Demo de [spec.md](spec.md#demo-de-cierre) y demos de la 004 y la 005 con login.

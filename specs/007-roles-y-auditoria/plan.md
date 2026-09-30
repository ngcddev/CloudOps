# Plan 007 · Acceso por roles y auditoría

> Cómo se construye [la spec](spec.md). Sin sobre-diseñar: dos roles, usuarios sembrados.

## Stack

FastAPI (OAuth2 password flow + JWT), `passlib[bcrypt]`, `python-jose`; React con contexto de sesión.

## Modelo de datos

| Tabla | Campos |
|---|---|
| `users` (existe desde 004) | suma `password_hash` · `is_active` · `last_login_at` |
| `audit_logs` | `id` · `user_id` · `action` · `entity` · `entity_id` · `details` jsonb · `ip` · `created_at` |

`audit_logs` solo recibe `INSERT` (sin endpoints de edición; opcional: `REVOKE UPDATE, DELETE` al
usuario de la aplicación).

## Autenticación y autorización

- `POST /api/auth/login` → JWT (60 min) con `sub`, `role`, `client_id`.
- `GET /api/auth/me`.
- Dependencias: `current_user`, `require_role("agencia")`, `scope_to_client(query, user)` aplicada
  en **todas** las consultas de clientes, servicios, tickets, incidentes y reportes.
- Clave de firma del JWT en variable de entorno `JWT_SECRET`.
- Frontend: token en memoria + `sessionStorage`; rutas `/agencia/*` y `/portal/*` protegidas por rol.

## Auditoría

`services/audit.py: record(user, action, entity, entity_id, details)` llamado desde los routers de
aprobación, rechazo, despliegue, rollback, prioridad y textos de IA.

| Método | Ruta | Rol |
|---|---|---|
| GET | `/api/audit-logs?user=&action=&from=&to=` | agencia |

Pantalla `/agencia/bitacora`: tabla filtrable.

## Datos semilla

`seed/users.json` con contraseñas de desarrollo documentadas en `.env.example` (nunca reales).

## Riesgos

| Riesgo | Respuesta |
|---|---|
| Olvidar el filtro por cliente en una consulta nueva | Prueba automática por endpoint con usuario cliente ajeno |

## Cómo se verifica

- `pytest`: 401 sin token, 403 cliente en acción de agencia, 404 al pedir datos de otro cliente,
  registro en bitácora por cada acción listada.
- Demo de [spec.md](spec.md#demo-de-cierre).

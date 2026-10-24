# Tareas 007 · Acceso por roles y auditoría

> Cada tarea: una acción con verbo · se comprueba en minutos · menos de un día · se integra sola.
> Rama por tarea: `feat/007-tNN-slug`. Poner el nombre de quien la toma entre corchetes.
>
> Es spec de producto: corre en `docker compose`, sin herramientas de plataforma nuevas.
> Orden: primero el login, las fixtures de prueba y la bitácora (T01–T07); después se protege cada
> router (T08–T15), así ninguna tarea deja las pruebas de 001, 004 y 005 en rojo.

## Usuarios y contraseñas

- [x] T01 · Sumar a `users` los campos `password_hash`, `is_active` y `last_login_at` con migración — **Verifica:** `alembic upgrade head` y `alembic downgrade -1` sin errores. [ngcddev]
- [x] T02 · Agregar un segundo usuario de agencia a `seed/users.json` y hacer que el seed guarde el hash de `SEED_USER_PASSWORD` (nuevo en `.env.example`) para todos — **Verifica:** arrancar de cero deja 5 usuarios con `password_hash` empezando por `$2b$` y `git grep` no encuentra contraseñas en claro fuera de `.env.example`. [ngcddev]
- [x] T03 · Escribir `services/auth.py` con `hash_password`, `verify_password`, `create_token` y `decode_token` (`PyJWT` y `bcrypt` con versión fija; `JWT_SECRET` obligatorio en `config.py`, `.env.example` y `docker-compose.yml`) — **Verifica:** `pytest`: la contraseña correcta valida, la incorrecta no, y un token vencido o firmado con otra clave se rechaza. [ngcddev]

## Sesión en la API

- [x] T04 · Crear `POST /api/auth/login` y `GET /api/auth/me` — **Verifica:** desde `/docs`, el correo de La Sazón con la contraseña de desarrollo devuelve un token y `me` responde rol `cliente` y su `client_id`; contraseña errada o usuario inactivo → 401. [ngcddev]
- [x] T05 · Escribir `deps.py` con `current_user`, `require_role` y `client_scope` — **Verifica:** `pytest` con una ruta de prueba: sin token 401, cliente en ruta de agencia 403, agencia pasa. [ngcddev]
- [x] T06 · Agregar a `conftest.py` las fixtures `as_agency` y `as_client` (cliente HTTP con token) y pasar las pruebas existentes a usarlas — **Verifica:** `docker compose exec api pytest` sigue en verde. [ngcddev]

## Bitácora

- [x] T07 · Crear la tabla `audit_logs` con migración (`user_id` nullable; trigger que rechaza `UPDATE` y `DELETE` en PostgreSQL) y `services/audit.py` con `record(...)` — **Verifica:** `alembic upgrade head` sin errores y un `UPDATE audit_logs ...` en `psql` falla con el mensaje del trigger. [ngcddev]

## Proteger lo que ya existe

- [x] T08 · Proteger `catalog` y `clients`: lectura con sesión y alcance por cliente, escritura solo agencia, y registrar `crear` / `editar` cliente — **Verifica:** `pytest`: La Sazón ve solo su cliente, pedir El Tornillo → 404, crear cliente como cliente → 403, y crear como agencia deja una fila en `audit_logs`. [ngcddev]
- [x] T09 · Proteger la lectura y la creación de `tickets`: rol y cliente salen del token, se quita `viewer_role` y `client_id` queda solo como filtro de la agencia — **Verifica:** `pytest`: el cliente lista solo sus solicitudes sin notas internas y con los estados de cambio del glosario, crear sobre un servicio ajeno → 404, y `?viewer_role=agencia` ya no cambia nada. [ngcddev]
- [ ] T10 · Fijar el actor desde la sesión en `classify`, `assign`, `transition` y `work-logs` (se quitan `actor_id`, `created_by_id` y `user_id` de los esquemas), exigir rol agencia y registrar cada acción en la bitácora — **Verifica:** `pytest`: el historial y `audit_logs` muestran al usuario del token aunque el cuerpo traiga otro id, y una transición inválida (409) no deja fila. [ ]
- [ ] T11 · Proteger `change_requests`: rol agencia, actor desde la sesión (se quitan `requested_by_id` y `actor_id` de los esquemas y `require_user` del router) y registrar `crear`, `aprobar` y `rechazar` — **Verifica:** `pytest` con Gitea simulado (`tests/fake_gitea.py`): aprobar como cliente → 403 sin commit en Gitea; como agencia, `approved_by_id` es el usuario del token y queda la fila; un 502 de Gitea no deja fila (cierra la nota de la 005). [ ]
- [ ] T12 · Dejar `GET /api/services/status` y `GET /api/services/{id}/deployments` solo para agencia — **Verifica:** `pytest`: como cliente → 403; como agencia responden igual que antes. [ ]
- [ ] T13 · Registrar `desplegar` y `fallar` desde `services/deploy_watch.py` con usuario "Sistema", en el mismo commit que cambia el estado — **Verifica:** `pytest` con Argo CD simulado (`tests/fake_argocd.py`): un cambio que queda `desplegada` y otro `fallida` dejan una fila cada uno con `user_id` nulo. [ ]
- [ ] T14 · Agregar la prueba que recorre todas las rutas de la app y exige 401 sin token (salvo `/health` y `/api/auth/login`) — **Verifica:** `pytest` en verde; una ruta nueva sin protección la hace fallar. [ ]
- [ ] T15 · Crear `GET /api/audit-logs` con filtros por usuario, objeto, acción y fechas — **Verifica:** como agencia lista las acciones más recientes primero con "Sistema" donde no hay usuario; como cliente → 403. [ ]

## Pantallas

- [ ] T16 · Crear `frontend/src/auth.tsx` (contexto de sesión en `sessionStorage`) y enviar `Authorization` desde `api.ts`, quitando `CURRENT_USER_ID`, `viewer_role`, `client_id` y los ids de actor de las llamadas (`TicketDetail.tsx`, `ChangeList.tsx`) — **Verifica:** `tsc` sin errores y `git grep CURRENT_USER_ID frontend/` sin resultados. [ ]
- [ ] T17 · Crear `/login` y proteger las rutas: sin sesión → `/login`, cliente en `/agencia/*` → `/portal`, agencia en `/portal/*` → `/agencia`, y un 401 de la API cierra la sesión — **Verifica:** abrir `/agencia/cambios` sin sesión lleva a `/login`; entrar como agencia vuelve a la bandeja. [ ]
- [ ] T18 · Mostrar el usuario y "Cerrar sesión" en la consola y el portal, y quitar el selector de cliente de `/portal/solicitudes` — **Verifica:** como La Sazón el portal muestra solo sus solicitudes y servicios; cerrar sesión vuelve a `/login`. [ ]
- [ ] T19 · Crear `/agencia/bitacora` con filtros y habilitar "Bitácora" en el menú de la consola — **Verifica:** aprobar un cambio y abrir la bitácora muestra la fila con usuario, acción, objeto y hora de Colombia. [ ]

## Despliegue en k3s

- [ ] T20 · Crear el `Secret` `hub-auth` (`JWT_SECRET` y `SEED_USER_PASSWORD` al azar) desde `gitops/hub/crear-secretos.sh`, pasarlo a la API en `gitops/hub/api.yaml` y publicar las imágenes nuevas de `hub-api` y `hub-web` — **Verifica:** `http://hub.local` pide entrar y acepta al usuario de La Sazón con la contraseña del `Secret`; `git grep` no encuentra los valores en el repo. [ ]

## Cierre

- [ ] T21 · Demo: La Sazón entra y ve solo lo suyo, pedir El Tornillo da "no encontrado", la agencia aprueba un cambio de El Tornillo y la bitácora muestra la aprobación y la publicación a nombre de "Sistema"; se repiten las demos de la 004 y la 005 con login — **Verifica:** todos los criterios de [spec.md](spec.md#criterios-de-aceptación). [ ]

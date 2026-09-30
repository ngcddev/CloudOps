# Plan 001 · Clientes y planes

> Cómo se construye [la spec](spec.md). Además fija el **esqueleto del Hub** que reutilizan todas
> las specs de producto.

## Stack (módulo 1)

| Pieza | Herramienta |
|---|---|
| API | Python 3.12, FastAPI, SQLAlchemy 2, Alembic, Pydantic v2, pytest |
| Base de datos | PostgreSQL 16 (`timestamptz`, UTC) |
| Frontend | React + Vite + TypeScript, react-router-dom, CSS propio en blanco y negro |
| Entorno | Docker multi-stage (usuario no root), `docker compose` |

## Esqueleto del Hub

```
backend/
├── Dockerfile
├── requirements.txt
├── alembic.ini
├── alembic/versions/
├── app/
│   ├── main.py          # crea la app, registra routers, GET /health
│   ├── config.py        # lee variables de entorno (DATABASE_URL, ...)
│   ├── db.py            # engine, SessionLocal, Base, get_db()
│   ├── models/          # un archivo por entidad
│   ├── schemas/         # Pydantic de entrada/salida
│   ├── routers/         # un archivo por recurso
│   ├── services/        # reglas de negocio (SLA, prioridad, KPI)
│   └── seed.py          # carga seed/*.json si la base está vacía
└── tests/
frontend/
├── Dockerfile           # build con Node → nginx-unprivileged
├── src/
│   ├── main.tsx, App.tsx, api.ts, styles.css
│   ├── pages/agencia/   # pantallas de la consola
│   └── components/
seed/                    # JSON de la spec 000 y de esta spec
docker-compose.yml       # db, api, web
.env.example
```

## Modelo de datos

| Tabla | Campos |
|---|---|
| `agencies` | `id` · `name` · `created_at` |
| `plans` | `id` · `code` (único) · `name` · `slo_availability` numeric · `support_hours` · `cpu_quota` · `memory_quota` · `monthly_price` · `included_hours` |
| `sla_policies` | `id` · `priority` (P1–P4, único) · `response_minutes` · `resolution_minutes` · `clock` |
| `clients` | `id` · `agency_id` FK · `name` · `contact_name` · `email` · `phone` · `created_at` · `updated_at` |
| `projects` | `id` · `client_id` FK · `name` · `description` · `created_at` |
| `services` | `id` · `project_id` FK · `plan_id` FK · `name` · `host` · `template` (`landing` / `landing_form`) · `namespace` · `status` (`operativo` por defecto) · `created_at` |

`sla_policies` se crea aquí porque el detalle del cliente muestra el SLA; las specs 004 y 008 la usan.

## API

| Método | Ruta | Qué hace |
|---|---|---|
| GET | `/health` | `{"status":"ok"}` y verifica la conexión a la base |
| GET | `/api/plans` | Lista planes |
| GET | `/api/sla-policies` | Lista tiempos por prioridad |
| GET | `/api/clients` | Lista clientes con su plan principal |
| POST | `/api/clients` | Crea cliente |
| GET | `/api/clients/{id}` | Detalle con proyectos, servicios, plan y SLA |
| PATCH | `/api/clients/{id}` | Edita cliente |
| POST | `/api/clients/{id}/projects` | Crea proyecto |
| POST | `/api/projects/{id}/services` | Crea servicio con plan |

Errores: 404 si no existe, 422 con mensaje en español si falta un campo.

## Pantallas

| Pantalla | Ruta | Contenido |
|---|---|---|
| Lista de clientes | `/agencia/clientes` | Tabla: cliente, servicio, plan, estado; botón "Registrar cliente" |
| Registrar cliente | `/agencia/clientes/nuevo` | Formulario cliente + proyecto + servicio + plan |
| Detalle del cliente | `/agencia/clientes/:id` | Datos, proyecto, servicio, plan, SLO y tabla SLA P1–P4 |

## Datos semilla

- `seed/plans.json`, `seed/sla_policies.json` (de la spec 000).
- `seed/clients.json`: Forja Digital y los 3 clientes con su proyecto y servicio, usando los nombres,
  hosts, namespaces y plantillas canónicos de la constitución.

## Contratos con otras specs

- Entrega a **004, 007, 008, 010**: tablas `clients`, `services`, `plans`, `sla_policies` y el esqueleto.
- Entrega a **003 / 005**: `services.namespace` y `services.host` enlazan el Hub con el clúster.

## Riesgos

| Riesgo | Respuesta |
|---|---|
| Diferencias Windows/Linux en el equipo | Todo corre en contenedores; `.gitattributes` fuerza LF |
| Migraciones en conflicto entre ramas | Una migración por PR; rebase antes de merge |

## Cómo se verifica

- `pytest`: crear/listar/ver/editar cliente, validación de campos, detalle con SLA.
- Demo de [spec.md](spec.md#demo-de-cierre) desde `docker compose up` en una máquina limpia.

# Tareas 001 · Clientes y planes

> Cada tarea: una acción con verbo · se comprueba en minutos · menos de un día · se integra sola.
> Rama por tarea: `feat/001-tNN-slug`. Poner el nombre de quien la toma entre corchetes.

## Base del proyecto

- [x] T01 · Crear las carpetas `backend/`, `frontend/` y `seed/` con su README — **Verifica:** estructura igual a la del [plan](plan.md#esqueleto-del-hub). [ngcddev]
- [x] T02 · Escribir `docker-compose.yml` con PostgreSQL, API y frontend, y `.env.example` — **Verifica:** `docker compose up` levanta los tres. [ngcddev]
- [x] T03 · Crear el esqueleto de FastAPI con `/health` y conexión a PostgreSQL — **Verifica:** `curl localhost:8000/health` → `{"status":"ok"}`. [ngcddev]

## Modelo de datos

- [ ] T04 · Crear las tablas agencia, plan, SLA, cliente, proyecto y servicio con migración de Alembic — **Verifica:** `alembic upgrade head` sin errores. [ ]
- [ ] T05 · Cargar datos semilla: la agencia, los 3 planes de la spec 000 y los 3 clientes — **Verifica:** `GET /api/clients` devuelve 3. [ ]

## API

- [x] T06 · Crear el CRUD de clientes (crear, listar, ver, editar) — **Verifica:** prueba manual con `/docs`. [ngcddev]
- [x] T07 · Crear proyecto y servicio de un cliente, asignando un plan — **Verifica:** el detalle muestra el servicio con su plan. [Andres-Duqu]
- [ ] T08 · Agregar pruebas automáticas de los endpoints con pytest — **Verifica:** `pytest` en verde. [ ]

## Pantallas

- [x] T09 · Crear el esqueleto de React + Vite con la navegación de la consola de agencia — **Verifica:** `localhost:5173` muestra el menú. [sebastian-debug]
- [x] T10 · Crear la lista de clientes y el formulario de registro (blanco y negro) — **Verifica:** registrar un cliente lo muestra en la lista. [sebastian-debug]
- [x] T11 · Crear el detalle del cliente con su proyecto, servicio, plan y SLA — **Verifica:** La Sazón muestra Premium y P1 15 min / 4 h. [sebastian-debug]

## Cierre

- [ ] T12 · Demo: desde cero con `docker compose up` se registran los 3 clientes y se ve su plan y SLA — **Verifica:** todos los criterios de [spec.md](spec.md#criterios-de-aceptación). [ ]

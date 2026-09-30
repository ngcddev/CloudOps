# backend/ — API del Hub

API en Python 3.12 + FastAPI con PostgreSQL 16. Ver el
[esqueleto del plan 001](../specs/001-clientes-y-planes/plan.md#esqueleto-del-hub).

**Responsable en el módulo 1:** Sistemas 2 (Backend). El `Dockerfile` lo escribe Sistemas 3
(DevSecOps) junto con el servicio `api` de `docker-compose.yml`.

## Estructura esperada

```
backend/
├── Dockerfile           # multi-stage, usuario no root
├── requirements.txt
├── alembic.ini
├── alembic/versions/    # una migración por PR
├── app/
│   ├── main.py          # crea la app, registra routers, GET /health
│   ├── config.py        # lee variables de entorno (DATABASE_URL, ...)
│   ├── db.py            # engine, SessionLocal, Base, get_db()
│   ├── models/          # un archivo por entidad
│   ├── schemas/         # Pydantic de entrada/salida
│   ├── routers/         # un archivo por recurso
│   ├── services/        # reglas de negocio (SLA, prioridad, KPI)
│   └── seed.py          # carga ../seed/*.json si la base está vacía
└── tests/
```

## Variables de entorno

Se leen de `.env` (copiado de [`.env.example`](../.env.example)). La principal es `DATABASE_URL`.

## Comandos

| Qué | Comando |
|---|---|
| Pruebas | `docker compose exec api pytest` |
| Migraciones | `docker compose exec api alembic upgrade head` |

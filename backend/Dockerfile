# Imagen de la API del Hub: multi-stage y sin root (constitución, stack de producto). Dos destinos:
#   dev  → lleva pytest y las pruebas, para `docker compose exec api pytest` (docker-compose.yml la elige con `target: dev`)
#   prod → solo lo que la API necesita para correr; es la etapa final, así que `docker build` sin --target la construye a ella
#          y es la que se publica por la puerta de seguridad y se despliega en el clúster.
# Construir producción:  docker build --build-context seed=./seed -t hub-api:vX backend
# Construir desarrollo:  docker build --target dev --build-context seed=./seed -t hub-api:dev backend

# ---------- Dependencias ----------
FROM python:3.12-slim AS deps-prod
WORKDIR /build
COPY requirements.txt ./
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim AS deps-dev
WORKDIR /build
# Se instalan también las dependencias de pruebas para poder correr: docker compose exec api pytest
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir --prefix=/install -r requirements-dev.txt

# ---------- Base común ----------
FROM python:3.12-slim AS base
# SEED_DIR: carpeta con los datos semilla (docker compose la entrega como contexto "seed")
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 SEED_DIR=/app/seed
RUN useradd --system --uid 10001 --no-create-home hub
WORKDIR /app

# ---------- Desarrollo (con pruebas) ----------
FROM base AS dev
COPY --from=deps-dev /install /usr/local
COPY alembic.ini pytest.ini ./
COPY alembic ./alembic
COPY app ./app
COPY tests ./tests
COPY --from=seed . ./seed
USER 10001
EXPOSE 8000
# Primero se aplican las migraciones y después arranca la API.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]

# ---------- Producción (etapa final: la que se construye por defecto) ----------
FROM base AS prod
COPY --from=deps-prod /install /usr/local
COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app
COPY --from=seed . ./seed
USER 10001
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]

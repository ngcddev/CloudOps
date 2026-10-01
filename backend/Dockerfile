# Imagen de la API del Hub: multi-stage y sin root (constitución, stack de producto).

FROM python:3.12-slim AS build
WORKDIR /build
# Se instalan también las dependencias de pruebas para poder correr: docker compose exec api pytest
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir --prefix=/install -r requirements-dev.txt

FROM python:3.12-slim
# SEED_DIR: carpeta con los datos semilla (docker compose la entrega como contexto "seed")
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 SEED_DIR=/app/seed
RUN useradd --system --uid 10001 --no-create-home hub
COPY --from=build /install /usr/local
WORKDIR /app
COPY alembic.ini pytest.ini ./
COPY alembic ./alembic
COPY app ./app
COPY tests ./tests
COPY --from=seed . ./seed
USER 10001
EXPOSE 8000
# Primero se aplican las migraciones y después arranca la API.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]

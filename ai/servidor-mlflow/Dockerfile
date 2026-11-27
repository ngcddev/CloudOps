# Imagen del servidor MLflow del laboratorio (spec 012, T08): versión fija, sin root (UID 10001) y con datos en /mlflow.
# Construir:  docker build -t hub/mlflow:3.18.0 ai/servidor-mlflow
FROM python:3.12-slim
# Sin ejecución de trabajos en segundo plano (huey): no se usan aquí y lanzan decenas de procesos y ~1,8 GB de RAM.
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 MLFLOW_SERVER_ENABLE_JOB_EXECUTION=false
RUN pip install --no-cache-dir mlflow==3.18.0 \
    && useradd --system --uid 10001 --home-dir /mlflow --create-home mlflow
USER 10001
WORKDIR /mlflow
EXPOSE 5000
# Un solo proceso (--workers 1): con varios, el servidor se pasa del límite de memoria del laboratorio.
# El almacén de artefactos lo sirve el propio servidor (--serve-artifacts): los clientes suben por HTTP y no
# necesitan montar el volumen. Los hosts permitidos se pasan por MLFLOW_ALLOWED_HOSTS (ver docker-compose.yml).
CMD ["sh", "-c", "mlflow server --host 0.0.0.0 --port 5000 --backend-store-uri sqlite:////mlflow/mlflow.db --artifacts-destination /mlflow/artifacts --serve-artifacts --workers 1 --allowed-hosts \"${MLFLOW_ALLOWED_HOSTS:-localhost:5000,127.0.0.1:5000}\""]

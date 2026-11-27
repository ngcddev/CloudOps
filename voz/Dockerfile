# Imagen del servicio de voz (spec 021): CPU, sin root, con los modelos dentro (descargados con su suma SHA-256 verificada).
# Construir desde la raíz:  docker build -f voz/Dockerfile --build-context vocab=./ai/classifier/data -t hub-voz:dev voz
#   --build-arg WHISPER=base  para el modelo de 145 MB (menos memoria y más rápido, pero se equivoca más con la jerga del Hub; ver docs/modelos)

# ---------- Modelos ----------
FROM python:3.12-slim AS modelos
ARG WHISPER=small
WORKDIR /w
COPY descargar_modelos.py .
RUN python descargar_modelos.py /modelos --whisper "${WHISPER}"

# ---------- Dependencias ----------
FROM python:3.12-slim AS deps
WORKDIR /build
COPY requirements.txt ./
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------- Imagen final ----------
FROM python:3.12-slim
# Paquetes del sistema con arreglo ya publicado (mismo criterio que las demás imágenes de Python, spec 018)
RUN apt-get update && apt-get install -y --no-install-recommends --only-upgrade zlib1g libzstd1 && rm -rf /var/lib/apt/lists/*
ARG WHISPER=small
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 VOZ_MODELOS=/modelos WHISPER_MODELO=${WHISPER} VOZ_VOCABULARIO=/app/vocabulario.txt
RUN useradd --system --uid 10001 --no-create-home voz
COPY --from=deps /install /usr/local
COPY --from=modelos /modelos /modelos
WORKDIR /app
COPY app ./app
# El vocabulario del Hub sesga el reconocimiento hacia sus términos
COPY --from=vocab vocabulario_app.txt /app/vocabulario.txt
USER 10001
EXPOSE 8100
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8100/health', timeout=4)"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8100"]

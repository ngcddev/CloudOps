# Imagen del sitio de El Tornillo (copia de la plantilla landing): Nginx sin root (UID 101) en el puerto 8080.
# Construir desde esta carpeta: docker build --build-arg APP_VERSION=v1 -t hub/ferreteria:v1 .
# Al arrancar, la imagen reemplaza ${APP_VERSION} en la plantilla de nginx.conf.

FROM nginxinc/nginx-unprivileged:1.30-alpine
# Parche de seguridad: la imagen base trae paquetes de Alpine con vulnerabilidades que ya tienen arreglo (brotli-libs crítica; curl, expat, libxslt, musl y zlib altas).
# La puerta de seguridad (Trivy) bloquea la imagen mientras haya críticas corregibles; se actualizan todos los paquetes (spec 018, T02).
USER root
RUN apk upgrade --no-cache
ARG APP_VERSION=v1
ENV APP_VERSION=${APP_VERSION}
COPY nginx.conf /etc/nginx/templates/default.conf.template
COPY src/ /usr/share/nginx/html/
USER 101
EXPOSE 8080

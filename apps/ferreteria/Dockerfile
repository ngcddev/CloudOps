# Imagen del sitio de El Tornillo (copia de la plantilla landing): Nginx sin root (UID 101) en el puerto 8080.
# Construir desde esta carpeta: docker build --build-arg APP_VERSION=v1 -t hub/ferreteria:v1 .
# Al arrancar, la imagen reemplaza ${APP_VERSION} en la plantilla de nginx.conf.

FROM nginxinc/nginx-unprivileged:1.27-alpine
ARG APP_VERSION=v1
ENV APP_VERSION=${APP_VERSION}
COPY nginx.conf /etc/nginx/templates/default.conf.template
COPY src/ /usr/share/nginx/html/
USER 101
EXPOSE 8080

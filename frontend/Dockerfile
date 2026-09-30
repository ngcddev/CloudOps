# Imagen del frontend: nginx sin root en el puerto 8080.
# Por ahora sirve una página provisional; la T09 la convierte en build con Node → nginx.
FROM nginxinc/nginx-unprivileged:1.27-alpine
COPY public/ /usr/share/nginx/html/
EXPOSE 8080

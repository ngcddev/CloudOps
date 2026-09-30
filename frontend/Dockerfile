# Imagen del frontend en dos etapas: build con Node y servicio con nginx sin root en el puerto 8080.

# ---------- Etapa 1: compilar la SPA ----------
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# ---------- Etapa 2: servir con nginx (usuario no root) ----------
FROM nginxinc/nginx-unprivileged:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
USER 101
EXPOSE 8080

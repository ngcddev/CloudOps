# Imagen del frontend en dos etapas: build con Node y servicio con nginx sin root en el puerto 8080.

# ---------- Etapa 1: compilar la SPA ----------
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# seed/ viene del contexto adicional "seed" de docker-compose.yml (api.ts la importa como ../seed)
COPY --from=seed . /seed
RUN npm run build

# ---------- Etapa 2: servir con nginx (usuario no root) ----------
FROM nginxinc/nginx-unprivileged:1.31-alpine
# Trivy encontró en esta imagen una CVE crítica (brotli-libs) y 12 altas con arreglo ya publicado en paquetes de Alpine (curl, expat, libxslt, musl, zlib):
# se actualizan los paquetes del sistema como root y se vuelve al usuario sin privilegios (spec 018, T01)
USER root
RUN apk upgrade --no-cache
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY seguridad.conf /etc/nginx/seguridad.conf
COPY --from=build /app/dist /usr/share/nginx/html
USER 101
EXPOSE 8080
# Lo que `docker ps` muestra: nginx sirve /health (auditoría CT-09 y CT-10)
HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 CMD ["wget", "-q", "-O", "/dev/null", "http://127.0.0.1:8080/health"]

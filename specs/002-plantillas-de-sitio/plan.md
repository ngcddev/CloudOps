# Plan 002 · Plantillas de sitio y apps demo

> Cómo se construye [la spec](spec.md). Base: sección "Sitios de cliente" de
> [constitution/tech-stack.md](../../constitution/tech-stack.md).

## Stack (módulo 1)

| Pieza | Herramienta |
|---|---|
| Sitio estático | HTML/CSS/JS (o Astro) servido por `nginxinc/nginx-unprivileged` (puerto 8080) |
| Backend del formulario | FastAPI mínimo, usuario no root |
| Entorno | Docker multi-stage, `docker compose` |

## Estructura

```
apps/
├── templates/
│   ├── landing/                 # Plantilla 1
│   │   ├── src/                 # index.html, styles.css
│   │   ├── nginx.conf           # /health y selección de versión
│   │   └── Dockerfile
│   └── landing-form/            # Plantilla 2
│       ├── frontend/            # igual a landing + formulario
│       ├── backend/             # POST /api/contact, GET /health
│       ├── Dockerfile.frontend
│       └── Dockerfile.backend
├── restaurante/                 # copia de landing + contenido de La Sazón
├── ferreteria/                  # copia de landing + contenido de El Tornillo
└── consultorio/                 # copia de landing-form + contenido de Dental Popayán
```

Los manifiestos `deploy/` de cada app se agregan en la spec 003 (en `gitops/`), no aquí.

## Versiones v1 y v2

- La versión se fija en build: `--build-arg APP_VERSION=v1|v2`.
- **v1:** `/health` → `{"status":"ok","version":"v1"}`; `/` sirve la página.
- **v2:** `nginx.conf` generado devuelve `return 500` en `/` y `/health` (en el consultorio, también
  el backend responde 500 en `/health`).
- Etiquetas de imagen: `hub/<cliente>:v1`, `hub/<cliente>:v2`. En el módulo 2 se publican en el
  registro de Gitea.

## Contenedores sin root

- Nginx: `nginxinc/nginx-unprivileged`, `USER 101`, puerto 8080.
- Backend: `python:3.12-slim`, usuario `app` (UID 10001), puerto 8000.
- Sin capacidades extra ni volúmenes de escritura salvo `/tmp`; cumple Pod Security `restricted`
  cuando llegue la spec 003.

## Formulario del consultorio

| Método | Ruta | Qué hace |
|---|---|---|
| POST | `/api/contact` | Guarda nombre, teléfono y motivo; responde `{"ok":true}` |
| GET | `/health` | Estado y versión |

Guarda en SQLite dentro del contenedor (dato de demo, se pierde al reiniciar). El contador de
formularios recibidos/fallidos que pide la auditoría se agrega con OpenTelemetry en la spec 008.

## En `docker-compose.yml`

Servicios `restaurante` (8081), `ferreteria` (8082), `consultorio-web` (8083) y `consultorio-api`,
junto a `db`, `api` y `web` de la spec 001. Variable `APP_VERSION` por servicio para cambiar a v2.

## Contratos con otras specs

- Entrega a **003**: imágenes sin root, puerto 8080, `/health` como readiness probe.
- Entrega a **008**: `/health` como objetivo de Blackbox Exporter; v2 como falla controlada.
- Entrega a **005 / 009**: dos tags (`v1`, `v2`) para desplegar y revertir.

## Riesgos

| Riesgo | Respuesta |
|---|---|
| Contenido de sitios toma tiempo | Contenido corto y ficticio; mismo CSS para los 3 |
| Nginx sin root no puede usar el puerto 80 | Usar 8080 en todo el proyecto |

## Cómo se verifica

- `curl -i` a `/` y `/health` en v1 (200) y v2 (500).
- `docker compose exec restaurante id -u` distinto de 0.
- Demo de [spec.md](spec.md#demo-de-cierre).

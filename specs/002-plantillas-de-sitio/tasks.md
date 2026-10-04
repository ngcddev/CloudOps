# Tareas 002 · Plantillas de sitio y apps demo

> Cada tarea: una acción con verbo · se comprueba en minutos · menos de un día · se integra sola.
> Rama por tarea: `feat/002-tNN-slug`. Poner el nombre de quien la toma entre corchetes.

## Plantilla 1 · Landing estática

- [x] T01 · Crear la página base (HTML/CSS en blanco y negro) con pie de versión — **Verifica:** se abre en el navegador. [ERIC]
- [x] T02 · Escribir el Dockerfile con `nginx-unprivileged` y `APP_VERSION` — **Verifica:** `id -u` en el contenedor ≠ 0. [ERIC]
- [x] T03 · Configurar `/health` y el modo v2 (HTTP 500) en `nginx.conf` — **Verifica:** `curl -i` da 200 en v1 y 500 en v2. [ERIC]

## Plantilla 2 · Landing + formulario

- [x] T04 · Crear el backend mínimo con `POST /api/contact` y `/health` — **Verifica:** `curl` devuelve `{"ok":true}`. [ERIC]
- [ ] T05 · Agregar el formulario al frontend y el proxy `/api` en Nginx — **Verifica:** enviar el formulario muestra la confirmación. [ ]
- [ ] T06 · Escribir los Dockerfiles sin root y el modo v2 del backend — **Verifica:** v2 responde 500 en `/health`. [ ]

## Sitios de clientes

- [ ] T07 · Crear el sitio de La Sazón desde la plantilla 1 — **Verifica:** muestra menú y reservas ficticias. [ ]
- [ ] T08 · Crear el sitio de El Tornillo desde la plantilla 1 — **Verifica:** muestra catálogo ficticio. [ ]
- [ ] T09 · Crear el sitio de Dental Popayán desde la plantilla 2 — **Verifica:** formulario de citas funciona. [ ]

## Integración

- [ ] T10 · Agregar los 3 sitios a `docker-compose.yml` con puertos 8081–8083 — **Verifica:** `docker compose up` los levanta con el Hub. [ ]

## Cierre

- [ ] T11 · Demo: 3 sitios en v1, La Sazón en v2 con 500, formulario enviado, usuario no root — **Verifica:** todos los criterios de [spec.md](spec.md#criterios-de-aceptación). [ ]

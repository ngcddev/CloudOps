# Tareas 005 · Cambios por GitOps

> Cada tarea: una acción con verbo · se comprueba en minutos · menos de un día · se integra sola.
> Rama por tarea: `feat/005-tNN-slug`. Poner el nombre de quien la toma entre corchetes.
>
> Depende de 003 (clúster, Gitea y registro) y de 004 (tickets con `kind = cambio`). El Hub **no** habla con
> Kubernetes: escribe en Gitea y lee de Argo CD. Los tokens van en `Secret` y en `.env`, nunca en el repo.
> Las tareas de backend (T07–T17) pueden avanzar con Gitea y Argo CD simulados mientras T01–T04 terminan.

## GitOps en la plataforma

- [ ] T01 · Instalar Argo CD en el namespace `argocd` con límites de memoria, expuesto en `argocd.hub.local` — **Verifica:** la interfaz abre e inicia sesión con el usuario administrador. [ ]
- [ ] T02 · Crear el repo `hub-gitops` en Gitea y sembrarlo desde `gitops/` — **Verifica:** el repo muestra `platform/`, `hub/` y `clients/` con el mismo contenido que el monorepo. [ ]
- [ ] T03 · Crear una `Application` de Argo CD por cliente con sincronización automática y `self-heal` apuntando a `clients/<cliente>` — **Verifica:** las 3 aparecen `Synced` y `Healthy`. [ ]
- [ ] T04 · Crear un token de Gitea con escritura solo sobre `hub-gitops` y uno de Argo CD de solo lectura, guardados en `Secret` y en `.env.example` como valores de ejemplo — **Verifica:** `git grep` no encuentra ningún token real en el repo. [ ]
- [ ] T05 · Publicar la versión `v1.1` de El Tornillo (portada nueva) en el registro de Gitea — **Verifica:** la imagen `ferreteria:v1.1` aparece en los paquetes y su pie y `/health` muestran `v1.1`. [ ]
- [ ] T06 · Probar el ciclo a mano: cambiar `newTag` en Gitea y luego revertir ese commit — **Verifica:** Argo CD sincroniza en menos de 3 minutos, el sitio muestra `v1.1` y tras el `revert` vuelve a `v1` (CA-3 y CA-5). [ ]

## Modelo de datos

- [ ] T07 · Crear las tablas `change_requests` y `deployments`, y sumar a `services` los campos `current_version`, `stable_version`, `sync_status` y `health_status`, con migración — **Verifica:** `alembic upgrade head` y `alembic downgrade -1` sin errores. [ ]
- [ ] T08 · Agregar `current_version` y `stable_version` en `v1` a los servicios de `seed/clients.json` y actualizar `seed/README.md` — **Verifica:** los tests de semilla pasan y `GET /api/clients/{id}` muestra la versión. [ ]

## Reglas e integraciones (`backend/app/`)

- [ ] T09 · Escribir `services/change_flow.py` con `pendiente → aprobada → en_validacion → desplegada` y `rechazada` — **Verifica:** `pytest` acepta las transiciones válidas, rechaza las inválidas y exige motivo al rechazar. [ ]
- [ ] T10 · Escribir la función que cambia solo `images.newTag` en el `kustomization.yaml` de un cliente — **Verifica:** `pytest` compara antes y después: la única línea distinta es la del tag. [ ]
- [ ] T11 · Escribir `integrations/gitea.py` para leer un archivo y actualizarlo con el mensaje `chore(<cliente>): versión <tag> (cambio #<id>)` y autor del Hub — **Verifica:** contra Gitea local, la llamada crea exactamente un commit con ese mensaje. [ ]
- [ ] T12 · Escribir `integrations/argocd.py` que lee sincronización, salud y revisión de una aplicación — **Verifica:** contra Argo CD local devuelve `Synced`, `Healthy` y el SHA de la revisión para La Sazón. [ ]

## API

- [ ] T13 · Crear `POST /api/change-requests` (vinculada a un ticket `kind = cambio`) y `POST /api/change-requests/{id}/reject` — **Verifica:** desde `/docs` se crea la solicitud en `pendiente` y se rechaza con motivo; sin motivo responde 422. [ ]
- [ ] T14 · Crear `POST /api/change-requests/{id}/approve` que escribe el tag en Gitea y deja la solicitud en `en_validacion` con el SHA del commit — **Verifica:** aprobar crea un commit en `hub-gitops` y ningún otro archivo cambia (CA-2). [ ]
- [ ] T15 · Crear la tarea periódica (cada 15 s) que consulta Argo CD y pasa la solicitud a `desplegada` cuando la aplicación está `Synced`, `Healthy` y en la revisión del commit — **Verifica:** `pytest` con Argo CD simulado cubre desplegada, sincronización pendiente y falla de salud; la solicitud queda registrada en `deployments`. [ ]
- [ ] T16 · Crear `GET /api/services/status` y `GET /api/services/{id}/deployments` — **Verifica:** devuelve versión activa, sincronización, salud y último autor de los 3 clientes, y el historial de versiones. [ ]
- [ ] T17 · Agregar la prueba de integración con Gitea local: aprobar un cambio crea exactamente un commit — **Verifica:** `docker compose exec api pytest` en verde. [ ]

## Pantallas

- [ ] T18 · Crear la bandeja `/agencia/cambios` con aprobar y rechazar (el rechazo pide motivo) — **Verifica:** aprobar muestra "En validación" y luego "Publicada" sin recargar. [ ]
- [ ] T19 · Agregar al detalle del ticket de tipo cambio el botón "Registrar cambio" con la versión destino — **Verifica:** el cambio aparece `pendiente` en la bandeja de cambios. [ ]
- [ ] T20 · Crear `/agencia/servicios` con versión activa, sincronización, salud y último autor por cliente — **Verifica:** tras la demo muestra `v1.1`, "Sincronizado" y el nombre del técnico (CA-4). [ ]

## Catálogo (RF-22, apagable si falta RAM)

- [ ] T21 · Escribir un `catalog-info.yaml` por cliente (`kind: Component`, `spec.owner: forja-digital`, enlace al Hub) — **Verifica:** los 3 archivos pasan la validación YAML. [ ]
- [ ] T22 · Instalar Backstage con catálogo mínimo y registrar los 3 clientes desde `hub-gitops` — **Verifica:** el catálogo lista los 3 clientes con su servicio y el enlace al Hub (CA-6); si falta RAM, se apaga y `/agencia/servicios` cumple el rol. [ ]

## Cierre

- [ ] T23 · Demo: El Tornillo pide publicar la nueva portada, el técnico aprueba, se ve el commit en Gitea, Argo CD sincroniza y la consola muestra `v1.1` — **Verifica:** todos los criterios de [spec.md](spec.md#criterios-de-aceptación). [ ]

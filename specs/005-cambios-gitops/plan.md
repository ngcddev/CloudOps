# Plan 005 · Cambios por GitOps

> Cómo se construye [la spec](spec.md). El Hub **no** habla con Kubernetes (principio 5): escribe en
> Gitea y lee de Argo CD.

## Stack (módulo 2)

| Pieza | Herramienta |
|---|---|
| Repositorio de configuración | Gitea, repo `hub-gitops` sembrado desde `gitops/` |
| Reconciliación | Argo CD, una `Application` por cliente (auto-sync, self-heal) |
| Catálogo | Backstage con `catalog-info.yaml` (apagable si falta RAM) |

## Flujo

```
Hub (aprobar) ──API Gitea──> commit en hub-gitops: clients/<c>/kustomization.yaml (images.newTag)
                                      │
Argo CD ──detecta cambio──> sync del namespace cliente-<c>
                                      │
Hub ──API Argo CD (lectura)──> sync status, health, revision → estado del cambio
```

## Modelo de datos

| Tabla | Campos |
|---|---|
| `change_requests` | `id` · `ticket_id` FK · `service_id` FK · `from_version` · `to_version` · `status` · `requested_by_id` · `approved_by_id` · `gitops_commit_sha` · `rejection_reason` · `created_at` · `approved_at` · `deployed_at` |
| `deployments` | `id` · `service_id` FK · `version` · `commit_sha` · `author` · `source` (`cambio` / `rollback`) · `created_at` |

`services` suma `current_version`, `stable_version`, `sync_status`, `health_status`.

## Integraciones (`backend/app/integrations/`)

- `gitea.py`: leer archivo, `PUT /repos/{owner}/{repo}/contents/{path}` con mensaje
  `chore(<cliente>): versión <tag> (cambio #<id>)` y autor = usuario del Hub.
- `argocd.py`: `GET /api/v1/applications/{name}` → `status.sync.status`, `status.health.status`,
  `status.sync.revision`. Token de solo lectura.
- Tarea periódica (cada 15 s) que actualiza el estado de los cambios en `en_validacion`.

## API

| Método | Ruta | Qué hace |
|---|---|---|
| POST | `/api/change-requests` | Crea solicitud de cambio |
| POST | `/api/change-requests/{id}/approve` | Aprueba y escribe en Gitea |
| POST | `/api/change-requests/{id}/reject` | Rechaza con motivo |
| GET | `/api/services/{id}/deployments` | Historial de versiones |
| GET | `/api/services/status` | Versión, sync y salud por cliente |

## Pantallas

- `/agencia/cambios`: bandeja de solicitudes de cambio con acciones.
- `/agencia/servicios`: tabla de clientes con versión activa, sincronización, salud y último autor.

## Backstage (RF-22)

`catalog-info.yaml` por cliente (`kind: Component`, `spec.owner: forja-digital`, anotación con el
enlace al Hub). Se registran desde el repo `hub-gitops`.

## Secretos

Token de Gitea y de Argo CD en `Secret` de Kubernetes y en `.env` local; nunca en el repo (RNF-06).

## Riesgos

| Riesgo | Respuesta |
|---|---|
| Hub y Argo CD desincronizados | El estado siempre se lee de Argo CD, no se infiere |
| Backstage consume varios GB | Catálogo mínimo; la consola del Hub cumple el rol si se apaga |

## Cómo se verifica

- Prueba de integración con Gitea local: aprobar crea exactamente un commit.
- Demo de [spec.md](spec.md#demo-de-cierre); `git revert` manual en Gitea devuelve la versión.

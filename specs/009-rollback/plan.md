# Plan 009 · Recuperación por rollback

> Cómo se construye [la spec](spec.md).

## Stack

Gitea API + Argo CD API (lectura), sin herramientas nuevas.

## Flujo

1. `POST /api/incidents/{id}/rollback` (rol agencia, con confirmación).
2. `integrations/gitea.py`: busca en `deployments` el último commit de `source=cambio` del servicio
   y crea un commit que restaura `clients/<c>/kustomization.yaml` al contenido previo
   (equivalente a `git revert`; la API de Gitea no tiene revert, se escribe el contenido anterior
   con mensaje `revert(<cliente>): volver a <stable> (incidente #<id>)`).
3. Se crea `deployments` con `source=rollback`; evento en `incident_events`; `audit.record(...)`.
4. La tarea periódica de la spec 005 lee Argo CD hasta `Synced` + `Healthy`.
5. El `resolved` de Alertmanager (spec 008) fija `mitigated_at`. Si llega antes que el sync, gana la
   primera hora en que la sonda volvió a verde.
6. `services/sla.py`: `mttr_minutes = mitigated_at - started_at`.

## Modelo de datos

- `incidents` suma `mttr_minutes` y `rollback_deployment_id`.
- `services.stable_version` se actualiza cuando un despliegue lleva 30 min sano.

## Mensaje al cliente

Plantilla de la constitución en `services/messages.py`:
*"Detectamos una falla temporal en su sitio a las {hora}. Activamos la recuperación y a las
{hora_fin} el servicio volvió a funcionar. Tiempo total: {min} minutos."* (hora de Colombia).

## Pantalla

Detalle del incidente: bloque "Recuperación" con versión actual → estable, botón, estado del
rollback (Enviado → Sincronizando → Recuperado) y MTTR.

## Riesgos

| Riesgo | Respuesta |
|---|---|
| Dos rollbacks simultáneos | Bloquear el botón mientras hay uno en curso |
| No existe versión estable previa | Botón deshabilitado con explicación |

## Cómo se verifica

- Prueba de integración con Gitea local: el rollback deja el archivo igual al de la versión estable.
- Demo de [spec.md](spec.md#demo-de-cierre).

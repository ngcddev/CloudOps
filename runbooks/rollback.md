# Rollback de una publicación

**Síntoma:** un sitio quedó en una versión rota o lenta tras publicar (alerta `PresupuestoQuemadoRapido` o incidente abierto).

## Diagnóstico

1. En el incidente, `GET /api/incidents/<id>/rollback-plan` (botón «Ver plan») dice a qué versión se vuelve y qué commit se escribe en `hub-gitops`.
2. Confirmar que la versión anterior es la última sana: la bitácora del Hub y el historial del cambio la muestran.

## Acción

- Desde el Hub: botón «Rollback» del incidente (`POST /api/incidents/<id>/rollback`). El Hub **no toca Kubernetes**: escribe el commit de vuelta en Gitea y Argo CD lo aplica.
- Sin el Hub (emergencia): hacer `git revert` del commit de la publicación en `hub-gitops` y subirlo; Argo CD sincroniza.
- El rollback queda en la bitácora con quién lo pidió.

## Verificación

La aplicación del cliente en Argo CD queda `Synced` y `Healthy`, `/health` responde en la versión anterior y el incidente pasa a mitigado con el tiempo de recuperación (MTTR) calculado.

## Cuándo escalar

Si el rollback falla (Gitea caído o conflicto en `hub-gitops`): revisar [respaldo-y-restauracion.md](respaldo-y-restauracion.md) para la plataforma y avisar a Sistemas.

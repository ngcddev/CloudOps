# Respaldo y restauración de PostgreSQL del Hub

**Síntoma:** datos perdidos o corruptos en el Hub, o hay que mover la base a otro entorno.

## Diagnóstico

- ¿Hay respaldo reciente? El CronJob `hub-db-backup` guarda un volcado diario: `kubectl -n hub get cronjob hub-db-backup` y `kubectl -n hub get jobs`.
- Para probar que el respaldo sirve sin riesgo: `bash gitops/pruebas/respaldo.sh` (respalda, restaura en una base nueva y compara filas tabla por tabla).

## Acción

1. Respaldo manual: `kubectl -n hub create job --from=cronjob/hub-db-backup respaldo-manual`.
2. Restaurar con `gitops/hub/respaldo/restaurar.sh` sobre una base nueva, con la API detenida (`kubectl -n hub scale deploy/api --replicas=0`); luego levantarla con `--replicas=1`.
3. Gitea y Argo CD se respaldan aparte, fuera del nodo: `bash gitops/pruebas/respaldo-plataforma.sh`.

## Verificación

Mismo número de filas por tabla que la base original, el Hub inicia sesión con los usuarios sembrados y la API responde.

## Cuándo escalar

El volcado no existe o falla al restaurar: no sobrescribir la base actual; guardar una copia del volumen y avisar a Sistemas.

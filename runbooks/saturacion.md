# Saturación de CPU o memoria

**Síntoma:** la API del Hub o un sitio responden lento o se reinician (`OOMKilled`); el tablero «RED y USE» muestra CPU o memoria cerca del límite.

## Diagnóstico

1. Tablero RED y USE de Grafana: qué Pod está cerca de su límite y desde cuándo.
2. `kubectl top pods -A --sort-by=memory` y el informe `bash observability/capacidad.sh` (uso frente a la cuota de cada cliente).
3. El HPA de la API y de la web (`kubectl -n hub get hpa`) escala de 1 a 2 réplicas con la CPU al 70 %.

## Acción

- La API del Hub: el HPA ya responde; si llega a su máximo, subir `maxReplicas` en `gitops/hub/escalado.yaml` por Git.
- Un sitio de cliente: no subir el límite a mano; el plan define la cuota (`seed/plans.json`). Si el cliente necesita más, es un cambio de plan.
- Prueba controlada de saturación: `bash gitops/pruebas/simulaciones.sh saturacion` (sube y baja el HPA y deshace todo al terminar).

## Verificación

CPU y memoria bajo el 70 % del límite, sin reinicios nuevos y el HPA de vuelta a 1 réplica.

## Cuándo escalar

La cuota del namespace impide que el HPA escale, o el nodo entero está sin memoria: ver [reinicio-del-cluster.md](reinicio-del-cluster.md).

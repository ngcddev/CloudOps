# Resultado final de C24 (demo 010) y C30 (OpenTofu): hallazgos, no repeticiones pendientes

## C24 · demo-010 — hallazgo H-OPS-02
- Pasos 1 a 3 (tablero de la agencia, portal del cliente, serie de disponibilidad y latencia): **pasan**.
- Pasos 4 a 6 **no se pueden cumplir con Argo CD selfHeal activo**: el script apaga el sitio con `kubectl scale --replicas=0` (paso 4) y Prometheus con la misma orden (paso 6); Argo CD revierte ambos cambios en unos 4 s (medido: `spec.replicas` vuelve a 1 a los +4 s, tanto en `cliente-restaurante/web` como en `monitoring/prometheus`), así que la alerta nunca llega a disparar ni Prometheus queda apagado. La demo se escribió antes de activar selfHeal (spec 017) y no se ajustó.
- La primera repetición (con el estado del 14 nov) pasó los pasos 4 y 5 por una carrera con la reconciliación; es intermitente.
- Lo que esa demo quería mostrar sí está verificado de otra forma: la caída real con incidente automático y MTTR con `cronometro.sh` (C26: 3 corridas, 48–49 s del corte al incidente, mitigación en ~167 s) y `demo-caso-restaurante.sh` (C25); la degradación sin Prometheus queda cubierta por pruebas unitarias del backend (consola con `null` cuando Prometheus no responde).

## C30 · crear-cliente — hallazgo H-IAC-01 (grave)
- `infra/pruebas/crear-cliente.sh` aplica el inventario completo (`clients.auto.tfvars.json`), que declara también a los tres clientes reales. El módulo reescribió en hub-gitops los `kustomization.yaml` de restaurante, ferreteria y consultorio (commits del usuario `hub-bot`, 01:51 UTC del 17 nov) con una plantilla genérica: la imagen pasó a `plantilla:v1`, que no existe en el registro. Resultado: los tres sitios quedaron en `ImagePullBackOff` y se abrieron tres alertas `SitioCaido`.
- Se revirtió con `git revert` de esos cinco commits en hub-gitops; los tres sitios volvieron a responder 200 y se cerraron los incidentes.
- Consecuencia para el informe: la creación de un cliente nuevo con OpenTofu funciona (`Apply complete`), pero **mientras los clientes existentes estén en el inventario sin estar en el estado, un apply los pisa**. Corrección propuesta: importar los tres clientes al estado o excluirlos del inventario; probar siempre con un inventario temporal.

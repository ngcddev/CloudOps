<!-- Sección 18 · Fuente: gitops/ (platform/argocd, clients, hub, sincronizar-hub-gitops.sh, pruebas/), runbooks/rollback.md. Estado de las Applications consultado en el clúster el 16 nov 2026. -->

# GitOps y despliegue

El despliegue de todo lo que corre en el clúster es declarativo y sigue el modelo de extracción (pull) de los principios de GitOps (OpenGitOps, 2021): el repositorio de configuración `hub-gitops` describe el estado deseado, y Argo CD lo lee y lo aplica. Ni el Hub ni las personas aplican manifiestos a mano. Las únicas excepciones son el arranque de Gitea y de Argo CD, que se aplican una vez con `kubectl` porque son los que hacen posible el resto (excepción de arranque documentada), y los Secrets, que no están en Git.

## Repositorio GitOps

El repositorio es `forja-digital/hub-gitops`, dentro de Gitea (`gitea.hub.local`). Tiene dos tipos de contenido con dueños distintos:

- **Lo que escribe el equipo:** `clients/_base` (manifiestos base de todos los sitios), `observability/`, `hub/` y `platform/` (Backstage, MLflow y respaldos). Se promueve desde el repositorio principal con un solo comando y en un solo sentido, `bash gitops/sincronizar-hub-gitops.sh`, que reemplaza cada carpeta destino completa. `bash gitops/pruebas/sincronia.sh` comprueba, solo en lectura, que `hub-gitops` esté en sincronía con el repositorio principal; el 16 de noviembre de 2026 respondió «hub-gitops está en sincronía con el repositorio principal».
- **Lo que escribe el Hub:** `clients/<nombre>/kustomization.yaml`, `catalog-info.yaml` y `backend.yaml` de cada cliente: la versión de imagen, el catálogo y los datos de cada sitio. Una regla de protección de la rama `main` en Gitea limita al usuario `hub-bot` a esos archivos (ADR-03); la promoción del equipo no pisa lo que escribe el Hub.

## Argo CD

Argo CD (Argo Project, s. f.) gobierna nueve Applications, todas `Synced` y `Healthy` el 16 de noviembre de 2026 en la misma revisión de `hub-gitops`:

::: {custom-style="Table Caption"}
**Tabla {T:applications}**\
*Applications de Argo CD y su política de sincronización*
:::

| Application | Qué despliega | Poda (`prune`) | Autocorrección (`selfHeal`) | Estado (16 nov 2026) |
|------------|----------------------|--------|----------|-----------------|
| `cliente-restaurante` | Sitio del restaurante (plan premium) | Sí | Sí | Synced y Healthy |
| `cliente-ferreteria` | Sitio de la ferretería (plan estándar) | Sí | Sí | Synced y Healthy |
| `cliente-consultorio` | Sitio del consultorio (plan básico) | Sí | Sí | Synced y Healthy |
| `cliente-ferreteria-staging` | Copia de pruebas de la ferretería, creada por el ApplicationSet | Sí | Sí | Synced y Healthy |
| `hub` | API, web, voz y base de datos del Hub | No | Sí | Synced y Healthy |
| `monitoring` | Prometheus, Alertmanager, Blackbox, Loki, Alloy, Tempo y Grafana | Sí | Sí | Synced y Healthy |
| `plataforma-backstage` | Backstage | No | Sí | Synced y Healthy |
| `plataforma-mlops` | MLflow | No | Sí | Synced y Healthy |
| `plataforma-respaldo` | Respaldos programados de Gitea y de Argo CD | No | Sí | Synced y Healthy |

::: {custom-style="Nota"}
*Nota.* Elaboración propia a partir de `gitops/platform/argocd/applications/` y de `kubectl get applications -n argocd` del 16 de noviembre de 2026. Las aplicaciones con estado no podan: adoptan recursos que ya corrían y un borrado por error no debe llevarse un volumen ni un Secret (ADR-04).
:::

Los sitios de clientes nuevos no necesitan una Application escrita a mano: el **ApplicationSet `clientes`** crea la Application `cliente-<nombre>` por cada carpeta `clients/<nombre>` que aparece en `hub-gitops`, y el generador mira Git cada 20 segundos, de modo que un sitio dado de alta aparece en segundos (`gitops/platform/argocd/applications/clientes-appset.yaml`). Todas las Applications de clientes pertenecen al **proyecto `clientes`**, que solo permite el repositorio `hub-gitops`, los destinos `cliente-*` y un conjunto cerrado de tipos de recurso: Namespace, Deployment, Service, Ingress, NetworkPolicy, ResourceQuota, LimitRange y ConfigMap (`gitops/platform/argocd/projects/clientes.yaml:14-28`). Un cliente comprometido no puede crear roles ni recursos del clúster. Las Applications de plataforma (`hub`, `monitoring`, `plataforma-backstage`, `plataforma-mlops` y `plataforma-respaldo`) usan el proyecto `default`, porque necesitan roles y recursos de clúster; su protección es la regla que limita lo que puede escribir el Hub en `hub-gitops` (ADR-03), no un proyecto confinado.

## Sincronización

Argo CD consulta Git cada 30 segundos (`timeout.reconciliation: 30s`, `gitops/platform/argocd/kustomization.yaml:27`), de modo que un cambio aprobado se aplica en menos de tres minutos (criterio de la especificación 005). El Hub no confía en inferir el estado: lo lee de la API de Argo CD y solo confirma una publicación cuando Argo CD ya aplicó el commit escrito o uno posterior que lo incluye (`backend/app/services/deploy_watch.py`). La secuencia completa se describe en la sección de diagramas de secuencia.

## Manejo de la deriva

Con `selfHeal` activo, un cambio hecho a mano en el clúster se revierte a lo que dice Git. La prueba `gitops/pruebas/drift.sh` lo comprueba escalando a mano el Deployment de un sitio y borrando su Ingress: Argo CD devuelve el Deployment a su réplica declarada (en 4 segundos en la medición registrada) y recrea el Ingress, y la prueba falla si `selfHeal` está apagado (`docs/bitacora.md:377`). Para la infraestructura de OpenTofu la deriva se detecta con `plan -detailed-exitcode` (ver la sección de infraestructura como código); el 16 de noviembre de 2026 se repitió la prueba y se detectó y corrigió la deriva.

## Rollback

El rollback es un commit en `hub-gitops` que restaura la etiqueta de imagen estable anterior; Argo CD lo aplica y el Hub confirma la recuperación (ADR-02). Se hace desde el incidente (`POST /api/incidents/{id}/rollback`, con un plan previo en `GET /api/incidents/{id}/rollback-plan`) o, en una emergencia sin el Hub, con `git revert` del commit de la publicación en `hub-gitops` (`runbooks/rollback.md`). El rollback queda en la bitácora con quién lo pidió, la versión de origen y la de destino. En el caso del restaurante medido el 14 de noviembre de 2026 el sitio quedó mitigado a los 48 a 60 segundos de pedir el rollback y el MTTR fue de 1,3 a 1,5 minutos.

## Evidencia de despliegue

La evidencia del despliegue es el estado de las nueve Applications (E-08), el rollback con su tiempo de recuperación en el incidente (E-20), el recorrido completo del caso del restaurante con `bash gitops/pruebas/demo-caso-restaurante.sh` (E-28) y la prueba de sincronía de `hub-gitops`. Las capturas se incorporan en el Apéndice A.

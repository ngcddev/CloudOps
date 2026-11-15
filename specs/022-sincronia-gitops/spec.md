# 022 · Sincronía simple y correcta entre el repositorio principal y hub-gitops

> **Acciona:** Equipo de Sistemas · **Módulo:** 2 (GitOps) · **Depende de:** 005, 016, 017 · **Estado:** En curso

## Qué y por qué

Hay dos lugares con manifiestos: la carpeta `gitops/` del repositorio principal (GitHub, donde se escribe y se revisa) y `forja-digital/hub-gitops` en Gitea (lo único que Argo CD vigila y
donde el Hub escribe las versiones). Pasaban de uno al otro con un script que **reemplaza carpetas enteras** a mano, sin comprobar qué se sube y sin saber qué parte es de quién. Resultado
real del 15 nov: el solo lectura de los sitios estaba en GitHub y nunca llegó a `hub-gitops`; y el mismo script, aplicado a `clients/<cliente>`, habría pisado las versiones que escribe el Hub.

El diseño correcto, el de un entorno real, es: **una sola fuente por cosa** y **un solo sentido por camino**.

| Quién escribe | Qué | Camino |
|---|---|---|
| El equipo (repositorio principal) | `clients/_base`, el resto de cada cliente salvo su versión, `observability/`, `hub/`, `platform/backstage/` | Se **promueve** a `hub-gitops` con un solo comando, desde un commit ya mezclado |
| El Hub (API de Gitea) | `clients/<cliente>/kustomization.yaml` (la versión: `newTag`) y `catalog-info.yaml` | Se escribe en `hub-gitops` y **nunca** se pisa desde el repositorio principal |
| Nadie (arranque único) | `platform/argocd`, `platform/gitea`, `platform/k3s`, `platform/namespaces.yaml` | Se aplican una vez con `kubectl` desde el repositorio principal; no se copian a `hub-gitops` |

El funcionamiento de la aplicación no cambia: el Hub sigue escribiendo versiones en `hub-gitops` y Argo CD sigue leyéndolo.

## Criterios de aceptación

- [ ] CA-1. Un solo comando (`gitops/sincronizar-hub-gitops.sh`) promueve a `hub-gitops` solo lo que es del equipo, con modo `--simular`, y **no pisa** la versión ni el `catalog-info.yaml` que escribe el Hub.
- [ ] CA-2. Solo promueve commits limpios y ya mezclados (`origin/dev` u `origin/main`); `--forzar` lo salta y lo avisa. El commit en `hub-gitops` dice de qué commit y rama salió.
- [ ] CA-3. Un chequeo (`gitops/pruebas/sincronia.sh`) dice si `hub-gitops` está en sincronía con el repositorio principal y lista los archivos distintos.
- [ ] CA-4. Las copias sin uso de `platform/` en `hub-gitops` se retiran y la documentación dice quién escribe qué.
- [ ] CA-5. El Hub se despliega por Argo CD desde `hub-gitops` (Application `hub`), sin `kubectl apply` a mano, sin cambiar su funcionamiento.

## Fuera de alcance

- Automatizar la promoción desde el CI de GitHub: el clúster del laboratorio está en un portátil y GitHub no puede alcanzar su Gitea. En un entorno real el CI promovería a un repositorio de configuración alcanzable (con PR) y el CI de la aplicación solo subiría las etiquetas de imagen; aquí lo hace el comando.
- Mover Argo CD, Gitea, k3s o el espacio de nombres: son el arranque del clúster y se aplican una vez.

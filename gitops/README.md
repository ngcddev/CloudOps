# gitops/ — manifiestos del clúster

> Lo que se aplica en el clúster k3s (spec 003). Desde la spec 005 esta carpeta se siembra en el
> repo `forja-digital/hub-gitops` de Gitea y la aplica Argo CD; mientras tanto se aplica una sola vez
> con `kubectl apply -k` para validar.

## Estructura

```
gitops/
├── platform/   # namespaces de plataforma: hub, argocd, monitoring, gitea
├── hub/        # el Hub: api, web y PostgreSQL
└── clients/
    ├── _base/          # plantilla por cliente (kustomize)
    ├── restaurante/    # La Sazón · Premium
    ├── ferreteria/     # El Tornillo · Estándar
    └── consultorio/    # Dental Popayán · Básico
```

## Clúster de un nodo

En el PC A va k3s directamente. Para desarrollar en otro equipo con Docker se usa `k3d`, que corre el
mismo k3s (con Traefik) dentro de Docker:

```bash
bash gitops/platform/k3s/crear-cluster.sh
```

El script crea la red con dirección fija, fija k3s en 1.32, publica los puertos 80/443, carga
[`registries.yaml`](platform/k3s/registries.yaml) (registro de Gitea por HTTP) y hace que
`gitea.hub.local` se resuelva desde dentro del nodo. Los alias de host y el registro solo se fijan al
crear el clúster: para cambiarlos hay que recrearlo.

- **Versión de k3s fijada en 1.32:** Docker Desktop con cgroup v1 no arranca k3s 1.35 en adelante
  (el kubelet se apaga con "cgroup v1 support is unsupported").
- **Puerto 80 libre:** si XAMPP/Apache lo usa, `restaurante.hub.local` respondería Apache y no Traefik.
- **Kubeconfig:** `k3d` escribe `host.docker.internal`, que en algunos equipos resuelve a la IP de la
  red y rechaza la conexión. Se corrige con
  `kubectl config set-cluster k3d-hub --server=https://127.0.0.1:<puerto>` (el puerto sale de
  `docker ps`, columna `PORTS` de `k3d-hub-serverlb`).

## Direcciones (`hosts`)

Los nombres `*.hub.local` no existen en ningún DNS. Cada equipo que los use los apunta a la IP del
nodo con una línea en el archivo `hosts` (en Windows, `C:\Windows\System32\drivers\etc\hosts`, con
PowerShell como administrador; en Linux, `/etc/hosts`). Se usan entradas explícitas porque `.local`
puede resolverse por mDNS.

```
127.0.0.1 hub.local restaurante.hub.local ferreteria.hub.local consultorio.hub.local gitea.hub.local argocd.hub.local backstage.hub.local
```

Cambia `127.0.0.1` por la IP fija del PC A cuando se entre desde otro equipo.

Al editar el archivo, la línea nueva debe ir en su propia línea: si la última línea existente no
termina en salto de línea, `Add-Content` la pega a ella y rompe las dos entradas.

## Cómo se comprueba

```bash
kubectl get nodes                          # el nodo, Ready
kubectl get pods -n kube-system            # traefik, Running
curl -i http://restaurante.hub.local       # 404 de Traefik: aún no hay sitio
```

## Gitea y registro de imágenes

```bash
kubectl apply -k gitops/platform/gitea
kubectl -n gitea wait --for=condition=Ready pod -l app=gitea --timeout=300s
```

El administrador **no** se guarda en el repo. Se crea una vez, con una contraseña que solo conoce quien
instala (guárdala en el gestor de contraseñas del equipo, no en un archivo versionado):

```bash
kubectl -n gitea exec deploy/gitea -- gitea admin user create --admin \
  --username forja-admin --password '<contraseña>' --email admin@forja.test --must-change-password=false
```

La organización `forja-digital` se crea desde la web (`http://gitea.hub.local`) o por la API.

Gitea queda como registro en `gitea.hub.local/forja-digital/<imagen>:<versión>`. La organización es
**pública** para que el nodo descargue sin credenciales (k3s no guarda contraseñas en
`registries.yaml`); subir imágenes sí pide usuario. Comprobación desde el nodo:

```bash
docker exec k3d-hub-server-0 crictl pull gitea.hub.local/forja-digital/<imagen>:v1
```

### Publicar las imágenes de los sitios

```bash
REGISTRY_USER=forja-admin REGISTRY_PASSWORD='<contraseña>' bash apps/publicar-imagenes.sh
```

Construye `restaurante`, `ferreteria`, `consultorio-web` y `consultorio-api` en `v1` (sana) y `v2`
(responde 500 en `/health`) y las sube a `gitea.hub.local/forja-digital/`. Se puede pasar el nombre de
una o más apps para publicar solo esas. Se usa `skopeo` en un contenedor porque Docker solo acepta
un registro HTTP si es `localhost`.

## Argo CD

```bash
kubectl apply -k gitops/platform/argocd
kubectl -n argocd rollout status deploy/argocd-server --timeout=300s
```

Instala Argo CD 2.13.3 en `argocd` con límites de memoria y lo expone en `http://argocd.hub.local`.
Dex (SSO) y el controlador de notificaciones quedan en 0 réplicas: no se usan y ahorran RAM. Se aplica
a mano una sola vez; Argo CD no se gestiona a sí mismo por GitOps.

El usuario es `admin` y la contraseña inicial la genera Argo CD (no está en el repo):

```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d
```

Cámbiala en *User Info → Update password* y borra el Secret inicial.

## Repo `hub-gitops`

Argo CD no lee el monorepo: vigila el repo `forja-digital/hub-gitops` de Gitea, y es ahí donde el Hub
escribe cada cambio de versión (spec 005). Se crea y se siembra una sola vez con el contenido de
`platform/`, `hub/` y `clients/`:

```bash
GITEA_USER=forja-admin GITEA_PASSWORD='<contraseña>' bash gitops/platform/gitea/sembrar-hub-gitops.sh
```

El script es idempotente: si el repo ya tiene commits no lo vuelve a sembrar. Desde ese momento el
contenido de `hub-gitops` manda; los cambios del monorepo en `gitops/` no se propagan solos.

## Una Application por cliente

```bash
kubectl apply -k gitops/platform/argocd/applications
kubectl -n argocd get applications     # las 3, Synced y Healthy
```

Cada `Application` (`cliente-restaurante`, `cliente-ferreteria`, `cliente-consultorio`) vigila
`clients/<cliente>` de `hub-gitops` con sincronización automática, `prune` y `self-heal`. Su nombre es
el del namespace: el Hub la consulta por ese nombre. Argo CD llega a Gitea por el Service
(`gitea.gitea.svc:3000`), no por `gitea.hub.local`, que los Pods no resuelven.

Si el sitio ya se había aplicado a mano con `kubectl apply -k` (spec 003), Argo CD lo adopta sin
recrearlo porque los manifiestos son los mismos.

## Tokens del Hub (Gitea y Argo CD)

El Hub escribe en `hub-gitops` (Gitea) y lee el estado de Argo CD. Cada acceso tiene su token, con el
mínimo permiso, y ninguno vive en el repo:

| Token | Quién | Alcance |
|---|---|---|
| `GITEA_TOKEN` | usuario `hub-bot` | `write:repository`, y `hub-bot` es colaborador solo de `forja-digital/hub-gitops` |
| `ARGOCD_TOKEN` | cuenta local `hub-readonly` | rol `readonly`: lee aplicaciones, no sincroniza ni borra |

```bash
GITEA_ADMIN_USER=forja-admin GITEA_ADMIN_PASSWORD='<contraseña>' bash gitops/hub/crear-tokens.sh
```

Los deja en el Secret `hub-gitops-tokens` del namespace `hub`, que la API del Hub lee como
`GITEA_TOKEN` y `ARGOCD_TOKEN`. En desarrollo local van en `.env` (ignorado por Git);
`.env.example` solo trae valores de ejemplo. Para rotarlos: borrar el Secret y volver a correr el script.

### Sesiones del Hub (spec 007)

Desde la spec 007 la API pide iniciar sesión y no arranca sin `JWT_SECRET`. Los dos valores viven en el
Secret `hub-auth` del namespace `hub`, que crea el mismo script de la base de datos (con valores al azar,
solo dentro del clúster):

```bash
bash gitops/hub/crear-secretos.sh
kubectl -n hub get secret hub-auth -o jsonpath='{.data.SEED_USER_PASSWORD}' | base64 -d   # contraseña de los usuarios sembrados
```

Correrlo **antes** de publicar la imagen nueva de `hub-api`. Los usuarios sembrados (`sofia@forjadigital.test`,
`camilo@forjadigital.test` y los de cada cliente) comparten esa contraseña. Una base creada antes de la
spec 007 también sirve: al arrancar, la API da contraseña solo a los usuarios que no tienen.

### Publicar la `v1.1` de El Tornillo (spec 005)

La portada nueva de El Tornillo (banner de temporada) aparece en toda versión distinta de `v1`: es la
versión que la demo de la spec 005 publica con un cambio aprobado.

```bash
REGISTRY_USER=forja-admin REGISTRY_PASSWORD='<contraseña>' bash apps/publicar-imagenes.sh ferreteria:v1.1
```

Para verla sin clúster: `FERRETERIA_VERSION=v1.1 docker compose up --build -d ferreteria` y abrir
`http://localhost:8082`.

## Probar el ciclo GitOps a mano

```bash
GITEA_USER=forja-admin GITEA_PASSWORD='<contraseña>' bash gitops/pruebas/ciclo-gitops.sh
```

Cambia `newTag` de El Tornillo a `v1.1` en `hub-gitops`, mide cuánto tarda Argo CD en dejar el sitio en
`v1.1` (debe ser menos de 3 minutos), revierte el commit con `git revert` y comprueba que el sitio
vuelve a `v1`. Es la misma ruta que seguirá el Hub, sin el Hub: si esto falla, el problema está en la
plataforma y no en el código de la API.

## Catálogo con Backstage (opcional)

```bash
kubectl apply -k gitops/platform/backstage
kubectl -n hub rollout status deploy/backstage --timeout=300s
```

Backstage queda en `http://backstage.hub.local` con un catálogo mínimo: la agencia (`forja-digital`) y
los 3 clientes con su servicio y el enlace a la consola del Hub. Lee los `catalog-info.yaml` de
`hub-gitops`, así que primero hay que sembrar ese repo. Usa hasta 1 GiB de memoria: si el PC A queda
justo, se apaga sin afectar nada más y `/agencia/servicios` del Hub cumple el rol:

```bash
kubectl -n hub scale deploy/backstage --replicas=0
```

## Demo de la spec 005 (cambios por GitOps)

```bash
bash gitops/pruebas/demo-005.sh
```

Recorre la demo con el clúster real: El Tornillo pide publicar la nueva portada (`v1` → `v1.1`), el
técnico aprueba en el Hub, se comprueba el commit en `hub-gitops` (un solo archivo, con el mensaje
`chore(ferreteria): versión v1.1 (cambio #N)`), Argo CD sincroniza en menos de 3 minutos y la consola
muestra `v1.1`, `Synced`, `Healthy` y el nombre del técnico. El script termina con `DEMO OK` o con la
cantidad de fallas. Antes: `ferreteria:v1.1` publicada, `hub-gitops` sembrado, Application de
El Tornillo `Synced` y el sitio en `v1`. Para repetirla hay que dejar el sitio en `v1` (revertir el
commit, ver [`ciclo-gitops.sh`](pruebas/ciclo-gitops.sh)) y la base del Hub vacía.

## Cambios hechos a mano en Git

Si alguien cambia `newTag` o hace `git revert` directamente en `hub-gitops`, el seguimiento del Hub
(cada 15 s) lo detecta cuando Argo CD ya sincronizó y alinea la consola: actualiza la versión activa,
registra el cambio en el historial como "Cambio manual en Git" (restauración si vuelve a una versión
anterior) y deja la estable solo si la aplicación está sana. No actúa mientras haya un cambio del Hub en curso.

### Rapidez con que Argo CD ve los cambios

Por defecto Argo CD consulta Git cada 3 minutos (más hasta 1 minuto de variación), así que "publicar en
menos de 3 minutos" no estaba garantizado. `gitops/platform/argocd` fija `timeout.reconciliation` en
30 s y quita la variación. Si Argo CD ya estaba instalado, aplica y reinicia (las claves se leen al arrancar):

```bash
kubectl apply -k gitops/platform/argocd
kubectl -n argocd rollout restart statefulset/argocd-application-controller deploy/argocd-repo-server
```

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
127.0.0.1 hub.local restaurante.hub.local ferreteria.hub.local consultorio.hub.local gitea.hub.local argocd.hub.local
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

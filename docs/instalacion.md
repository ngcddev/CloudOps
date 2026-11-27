<!-- Guía de instalación de CloudOps Client Hub desde cero hasta http://hub.local (Windows con Docker Desktop). -->
# Instalación completa desde cero hasta `http://hub.local`

> **Estado:** armada leyendo los scripts del repositorio el 27 nov 2026. **Ni la guía ni el instalador se han ejecutado de principio a fin en un PC limpio.**
> No ejecutes los pasos manuales en un equipo que ya tenga el clúster `k3d-hub`: no tienen protección.

## Instalación automática

Con los requisitos del apartado 0, en **Git Bash**:

```bash
git clone https://github.com/ngcddev/CloudOps.git
cd CloudOps
bash infra/instalar.sh --comprobar   # solo revisa; no cambia nada
bash infra/instalar.sh               # instala hasta http://hub.local
```

- **Claves:** no hay que preparar ninguna. Para elegir las principales, crea antes `.env.cluster` (ignorado por Git) con `GITEA_ADMIN_PASSWORD` (administrador de Gitea) y `SEED_USER_PASSWORD` (usuarios del Hub): solo letras y números, 12 o más. Las que falten se generan y quedan en ese archivo. Los tokens, las claves internas y las de firma los generan los scripts.
- **Permisos:** Windows pide permiso de administrador para editar el archivo `hosts`.
- **Si un paso falla:** corrige el problema y ejecuta el mismo comando; salta los pasos terminados (los anota en `.instalacion-estado`).
- **Protección:** si ya existe un clúster `k3d-hub` que no creó el instalador, se detiene sin tocarlo. No crees `.instalacion-estado` a mano.
- **Al terminar:** muestra la dirección y el usuario, y deja la contraseña en el portapapeles.
- **Cambios locales:** la instalación genera claves de firma propias, así que `pipelines/cosign.pub` queda modificado en tu copia.

Lo que sigue es el mismo procedimiento paso a paso, para entenderlo o resolver una falla.

## 0. Requisitos

| Herramienta | Nota |
|---|---|
| Windows 10/11 con Docker Desktop (WSL 2) | Abierto y en ejecución. Incluye `kubectl` |
| Git para Windows | Trae Git Bash |
| Python 3 | `python --version` debe mostrar una versión (no el acceso a Microsoft Store) |
| Ollama | Abierto. Con GPU de 8 GB como la del equipo; sin GPU va muy lento |
| Equipo | Internet, puertos **80 y 443 libres** (cerrar XAMPP, Apache o IIS). Recomendado 16 GB de RAM o más y varias decenas de GB de disco (estimación) |

**Terminal:** todos los comandos van en **Git Bash**, en la misma ventana y desde la raíz del proyecto. Solo el paso 2 usa PowerShell como administrador.
Si cierras la ventana, repite los `export` de los pasos 3 y 4.

## 1. Clonar y descargar los modelos

```bash
git clone https://github.com/ngcddev/CloudOps.git
cd CloudOps
ollama pull qwen2.5:7b-instruct
ollama pull nomic-embed-text
```

## 2. Archivo `hosts` (PowerShell como administrador)

```powershell
Add-Content C:\Windows\System32\drivers\etc\hosts "`r`n127.0.0.1 hub.local restaurante.hub.local ferreteria.hub.local consultorio.hub.local gitea.hub.local argocd.hub.local grafana.hub.local mlflow.hub.local backstage.hub.local ferreteria-staging.hub.local colegio.hub.local"
```

## 3. Crear el clúster k3d (no hace falta instalar k3d)

```bash
docker network create k3d-hub --subnet 172.30.0.0/24 --gateway 172.30.0.1

MSYS_NO_PATHCONV=1 docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  -v "$(pwd -W)/gitops/platform/k3s/registries.yaml:/cfg/registries.yaml:ro" \
  ghcr.io/k3d-io/k3d:5.8.3 cluster create hub --image rancher/k3s:v1.32.9-k3s1 --network k3d-hub \
  -p "80:80@loadbalancer" -p "443:443@loadbalancer" \
  --registry-config /cfg/registries.yaml --host-alias "172.30.0.1:gitea.hub.local" --wait

mkdir -p ~/.kube
MSYS_NO_PATHCONV=1 docker run --rm -v /var/run/docker.sock:/var/run/docker.sock ghcr.io/k3d-io/k3d:5.8.3 kubeconfig get hub > ~/.kube/k3d-hub.yaml
PUERTO="$(docker port k3d-hub-serverlb 6443 | head -1 | sed 's/.*://')"
sed -i "s#server: .*#server: https://127.0.0.1:${PUERTO}#" ~/.kube/k3d-hub.yaml
export KUBECONFIG="$(cygpath -m ~/.kube/k3d-hub.yaml)"
kubectl get nodes
```

**Comprobar:** el nodo está `Ready`.

## 4. Namespaces, Gitea y administrador

```bash
kubectl apply -f gitops/platform/namespaces.yaml
kubectl apply -k gitops/platform/gitea
kubectl -n gitea wait --for=condition=Ready pod -l app=gitea --timeout=600s
```

Define las credenciales. Cambia `TU_CLAVE` por una contraseña larga de letras y números:

```bash
export GITEA_ADMIN_USER=forja-admin
export GITEA_ADMIN_PASSWORD='TU_CLAVE'
export GITEA_USER="$GITEA_ADMIN_USER" GITEA_PASSWORD="$GITEA_ADMIN_PASSWORD"
export REGISTRY_USER="$GITEA_ADMIN_USER" REGISTRY_PASSWORD="$GITEA_ADMIN_PASSWORD"
printf "GITEA_ADMIN_USER=%s\nGITEA_ADMIN_PASSWORD='%s'\n" "$GITEA_ADMIN_USER" "$GITEA_ADMIN_PASSWORD" > .env.cluster

kubectl -n gitea exec deploy/gitea -- gitea admin user create --admin \
  --username "$GITEA_ADMIN_USER" --password "$GITEA_ADMIN_PASSWORD" --email admin@forja.test --must-change-password=false
```

`.env.cluster` está ignorado por Git. No lo compartas.

## 5. Secretos, organización y claves de firma

```bash
bash gitops/hub/crear-secretos.sh
bash pipelines/configurar-gitea.sh --rotar-claves
```

El segundo script crea la organización `forja-digital`. `--rotar-claves` es **obligatorio** en una instalación nueva: el repositorio trae la clave pública del equipo original, cuya clave privada no tienes. Cambia `pipelines/cosign.pub` en tu copia.

## 6. Publicar las imágenes (la parte más lenta)

```bash
bash apps/publicar-imagenes.sh
bash apps/publicar-imagenes.sh ferreteria:v1.1
bash apps/publicar-imagenes.sh hub-api hub-web hub-voz mlflow
bash apps/publicar-imagenes.sh colegio-web colegio-api
```

**Comprobar:** cada comando termina en `Listo: imágenes publicadas`.

## 7. Argo CD

```bash
kubectl apply -k gitops/platform/argocd --server-side --force-conflicts
kubectl -n argocd rollout status deploy/argocd-server --timeout=600s
```

No borres todavía el Secret `argocd-initial-admin-secret`: el paso 8 lo usa.

## 8. Repositorio GitOps y tokens

```bash
bash gitops/platform/gitea/sembrar-hub-gitops.sh
bash gitops/hub/crear-tokens.sh
bash gitops/sincronizar-hub-gitops.sh --limpiar
```

## 9. Desplegar el Hub, los sitios y la plataforma

```bash
kubectl apply -f gitops/platform/argocd/applications/hub.yaml
kubectl apply -k gitops/platform/argocd/applications
kubectl apply -f gitops/platform/argocd/applications/monitoring.yaml
kubectl apply -f gitops/platform/argocd/applications/plataforma-mlops.yaml
kubectl apply -f gitops/platform/argocd/applications/plataforma-respaldo.yaml
kubectl apply -f gitops/platform/argocd/applications/plataforma-backstage.yaml
kubectl apply -f gitops/platform/politicas/
kubectl get applications -n argocd -w
```

Espera a que todas estén `Synced` y `Healthy` y sal con `Ctrl+C`.

**Primer hito:** `http://hub.local` abre la pantalla de ingreso.

## 10. Conectar la IA

```bash
bash gitops/hub/configurar-ia.sh http://host.docker.internal:11434 rag
```

La política de red del Hub solo permite Ollama en `192.168.65.254`, que es la dirección de `host.docker.internal` en Docker Desktop. En otro entorno hay que cambiar `gitops/hub/networkpolicy.yaml`.

Registrar la compuerta en MLflow:

```bash
MSYS_NO_PATHCONV=1 docker run --rm --add-host mlflow.hub.local:host-gateway \
  -e MLFLOW_TRACKING_URI=http://mlflow.hub.local -v "$(pwd -W):/repo" -w /repo python:3.12-slim \
  sh -c "pip install -q -r ai/requirements.txt && python ai/classifier/train.py --promover"
git status --short
```

Este comando no sale de un script del repositorio: es el que menos garantía tiene. El Hub no depende de él, porque la compuerta que usa viene dentro de su imagen.

## 11. Runner de la puerta de seguridad

```bash
export GITEA_INSTANCE_URL=http://gitea.hub.local
export GITEA_RUNNER_REGISTRATION_TOKEN="$(curl -s -u "$GITEA_ADMIN_USER:$GITEA_ADMIN_PASSWORD" http://gitea.hub.local/api/v1/admin/runners/registration-token | sed -n 's/.*"token":"\([^"]*\)".*/\1/p')"
docker compose -f pipelines/runner/docker-compose.yml up -d --build
bash pipelines/sembrar-repos-sitios.sh restaurante ferreteria consultorio
bash pipelines/sembrar-repos-sitios.sh --sin-etiquetas colegio
```

Las corridas se ven en `http://gitea.hub.local`, en la pestaña *Actions* de cada repositorio. Espera a que terminen.

## 12. Dejar los datos listos

```bash
bash demo/dejar-demo-lista.sh
```

**Borra la base del Hub** y la siembra de nuevo, vuelve a pasar los sitios por la puerta, los deja en `v1` e indexa la ayuda. **Comprobar:** termina en `fallos: 0`.

## 13. Entrar al Hub

La contraseña de los usuarios (no la compartas):

```bash
kubectl -n hub get secret hub-auth -o jsonpath='{.data.SEED_USER_PASSWORD}' | base64 -d; echo
```

Abre `http://hub.local` e ingresa con `sofia@forjadigital.test`. Para usar el micrófono, entra por `https://hub.local` y acepta el certificado autofirmado.

## 14. Comprobación final

```bash
kubectl get nodes
kubectl get applications -n argocd
kubectl get pods -A
curl -s http://hub.local/health
for s in restaurante ferreteria consultorio; do curl -s http://$s.hub.local/health; echo; done
```

| Dirección | Qué se ve |
|---|---|
| `http://hub.local` | El Hub, con sesión iniciada y una respuesta del asistente |
| `http://argocd.hub.local` | Aplicaciones sincronizadas (usuario `admin`) |
| `http://gitea.hub.local` | Repositorios y corridas de la puerta |
| `http://grafana.hub.local` | Tableros (usuario `admin`) |
| `http://mlflow.hub.local` | El modelo `compuerta-asistente` |
| `https://backstage.hub.local` | El catálogo |

Documentación de Backstage (opcional): `bash gitops/platform/backstage/publicar-docs.sh`.

## Si algo falla

| Síntoma | Qué revisar |
|---|---|
| El puerto 80 está ocupado o responde Apache | Cerrar XAMPP, Apache o IIS |
| `kubectl` no conecta | Repetir el `export KUBECONFIG` y revisar `docker port k3d-hub-serverlb 6443` |
| `ImagePullBackOff` | Que el paso 6 haya terminado; `kubectl -n <namespace> describe pod <pod>` |
| Una aplicación no queda `Healthy` | `kubectl get pods -A` y `kubectl -n <namespace> logs <pod>` |
| La puerta falla por vulnerabilidades | Puede haber CVE nuevas. Las excepciones de nginx vencen el **4 dic 2026** |
| El asistente dice que la IA no está disponible | Ollama abierto, modelos descargados y paso 10 aplicado |
| El nodo reinicia sin parar tras apagar el equipo | [Runbook de reinicio](../runbooks/reinicio-del-cluster.md) |

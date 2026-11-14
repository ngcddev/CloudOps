# Plan 016 · Alta de sitio por GitOps y demo del colegio

## Decisiones

1. **El Hub solo escribe en hub-gitops** (principio 5). El alta crea la carpeta `clients/<cliente>/`; no se crea ninguna Application a mano.
2. **ApplicationSet con generador de directorios** (`clientes-appset.yaml`): una Application por carpeta, nombre `cliente-<nombre>`
   (igual al namespace, que es como el Hub la consulta). Excluye `_base` y los tres clientes sembrados, que conservan su Application.
   `requeueAfterSeconds: 20` en lugar de los 3 minutos por defecto.
3. **Orden de escritura:** primero `backend.yaml`, al final `kustomization.yaml`: el generador no ve la carpeta hasta que está completa.
4. **Convención de imágenes:** `<cliente>` (landing) o `<cliente>-web` y `<cliente>-api` (con formulario), `v1` como primera versión.
   Si el registro dice que no existen (404) el alta se rechaza; si no se puede saber (sin permiso de lectura), no se bloquea.
5. **El kustomization se genera con código** y una prueba lo compara con los tres reales: así no se desvía de lo sembrado.
6. **Puerta de seguridad del colegio:** sin runner de Gitea Actions se simula (`demo/preparar-colegio.sh`, ~2 min por versión) y se lanza
   al dar de alta el sitio.

## Piezas

`backend/app/services/provisioning.py`, endpoint en `routers/services.py`, `GiteaClient.create_file` e `image_exists`, botón «Dar de alta en GitOps»
en la ficha del cliente, `gitops/platform/argocd/applications/clientes-appset.yaml`, `apps/colegio/`, `demo/reiniciar-cluster.sh`,
`demo/preparar-colegio.sh`, y `demo-caso-restaurante.sh` con `NS` parametrizable.

## Riesgos

- La puerta tarda unos 2 minutos por versión: se lanza en otra terminal apenas se da de alta el sitio.
- Si el token del Hub no puede leer paquetes, no se valida la imagen y un alta sin imagen deja el Pod en `ImagePullBackOff`.

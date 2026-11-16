# Infraestructura como código

Esta carpeta contiene la configuración OpenTofu/Terraform para administrar el punto de entrada de cada cliente: su overlay en el repositorio `hub-gitops` y su `Application` de Argo CD.

## Alcance

OpenTofu/Terraform crea y administra los archivos de configuración del cliente en Gitea (su overlay en `hub-gitops`). La `Application` que los entrega a Argo CD la crea el ApplicationSet `clientes` en cuanto existe el overlay, en el AppProject `clientes`; por defecto el módulo no la crea (`crear_application = false`) para que no haya dos creadores del mismo recurso, y si se activa usa el mismo proyecto confinado, nunca `default` (auditoría IA-01). Los tres clientes anteriores (restaurante, ferretería y consultorio) conservan su Application manual y no están en el estado de OpenTofu. Argo CD sigue siendo responsable de reconciliar los recursos Kubernetes del cliente, como el namespace, las cuotas, los límites, la red y el sitio.

Esta configuración no crea ni administra las máquinas, el clúster, la red del laboratorio ni los componentes compartidos de la plataforma. Tampoco administra Deployments, Services o Ingress directamente.

Las cuotas se obtendrán de `seed/plans.json`; ese archivo es la fuente única de los planes. El inventario versionado de clientes no debe contener credenciales. El token de Gitea se proporcionará mediante `GITEA_TOKEN`.

## Estructura

- `tofu/`: configuración HCL común a OpenTofu y Terraform.
- `tofu/modules/client-env/`: módulo que crea el overlay y la `Application` de un cliente.
- `pruebas/`: verificaciones de creación, cuota y limpieza de clientes.
- `state/`: estado local y respaldos; está excluido de Git y debe conservarse fuera del repositorio compartido.
- `.kubeconfig`: kubeconfig temporal generado para conectar las herramientas con el clúster; está excluido de Git.

## Requisitos

`tofu.sh` ejecuta OpenTofu 1.13.2 o Terraform 1.17.0 en contenedores. Los comandos `version` y `help` no requieren que el clúster esté iniciado. Para operar sobre el entorno se necesita el clúster k3d `hub`, la red `k3d-hub` y el token de Gitea en `GITEA_TOKEN`.

Ejemplo: `GITEA_TOKEN=<token> infra/tofu.sh tofu plan`.

No guardes tokens, kubeconfigs ni archivos de estado en el repositorio. Antes de ejecutar cambios sobre un cliente existente, revisa el plan de ejecución y confirma que no propone recrearlo.

## Kit offline

`bash infra/kit-offline.sh exportar kit-offline` junta las imágenes OCI del proyecto, los paquetes de Python del backend, la caché de npm del frontend, la base de
Trivy y el inventario de los modelos de Ollama (`--con-modelos` copia la carpeta de modelos), con sumas SHA-256. `verificar` detecta archivos corruptos y `restaurar`
carga las imágenes y muestra cómo instalar sin red. Probado el 14 nov: exportar, verificar, detectar un archivo alterado, borrar una imagen y restaurarla,
`pip install --no-index` y `npm ci --offline` con la red cortada. Pendiente de probar a escala: el kit completo con todas las imágenes (varios GB).

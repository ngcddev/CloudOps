# Infraestructura como código

Esta carpeta contiene la configuración OpenTofu/Terraform para administrar el punto de entrada de cada cliente: su overlay en el repositorio `hub-gitops` y su `Application` de Argo CD.

## Alcance

OpenTofu/Terraform crea y administra los archivos de configuración del cliente en Gitea y la `Application` que los entrega a Argo CD. Argo CD sigue siendo responsable de reconciliar los recursos Kubernetes del cliente, como el namespace, las cuotas, los límites, la red y el sitio.

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

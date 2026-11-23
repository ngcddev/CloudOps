<!-- Sección 17 · Fuente: infra/ (tofu/, client-new.sh, tofu.sh, estado-remoto.sh, pruebas/), specs/011 (verificaciones). Prueba de deriva ejecutada el 16 nov 2026. -->

# Infraestructura como código

La infraestructura de los clientes se declara con OpenTofu y se ejecuta, igual que con Terraform, desde contenedores con versión fija. El inventario de clientes y el catálogo de planes son datos: agregar un cliente es agregar una entrada, no escribir recursos. Lo que el código provisiona está acotado a lo que es técnicamente viable en el laboratorio (ver la justificación al final de la sección); el clúster mismo se crea con un script (`gitops/platform/k3s/crear-cluster.sh`) y no con OpenTofu.

## Recursos provisionados

Para cada cliente del inventario, el módulo `client-env` crea dos recursos (`infra/tofu/modules/client-env/main.tf`):

1. **El overlay del cliente en `hub-gitops`** (`gitea_repository_file.overlay`): el archivo `clients/<nombre>/kustomization.yaml`, generado con una plantilla a partir del dominio, el plan, las cuotas del plan y la imagen. Con `lifecycle { ignore_changes = [content] }`, OpenTofu no pisa después los cambios de versión que escribe el Hub.
2. **La Application de Argo CD** (`kubernetes_manifest.application`), solo si `crear_application = true`. Por defecto no se crea: la Application la crea el ApplicationSet `clientes` en cuanto aparece el overlay, y dos creadores para el mismo nombre chocan (hallazgo IA-01 de la auditoría). Cuando se usa, queda en el proyecto confinado `clientes` y nunca en `default`.

El espacio de nombres, la cuota, el LimitRange y las políticas de red de cada cliente no los crea OpenTofu: los aplica Argo CD desde la base común `gitops/clients/_base` con los valores del overlay.

## Estructura del código

::: {custom-style="Table Caption"}
**Tabla {T:estructura-iac}**\
*Estructura de `infra/` y función de cada archivo*
:::

| Archivo | Función |
|------------------|------------------------------------------|
| `infra/tofu/providers.tf` | Versión mínima de OpenTofu (1.10) y proveedores fijados: `hashicorp/kubernetes` 3.4.0 y `go-gitea/gitea` 0.8.1; backend local por defecto |
| `infra/tofu/variables.tf` | Variables: `gitea_token` (sensible) y `clients` (inventario) |
| `infra/tofu/clients.auto.tfvars.json` | Inventario real: `restaurante` (premium), `ferreteria` (estándar) y `consultorio` (básico) |
| `infra/tofu/clients.tf` | Instancia el módulo con `for_each` sobre el inventario y toma las cuotas del plan |
| `infra/tofu/plans.tf` | Lee el catálogo de planes de `seed/plans.json`, el mismo que carga el Hub |
| `infra/tofu/modules/client-env/` | Módulo del entorno de un cliente (overlay y Application opcional) |
| `infra/tofu/backend_remoto.tf.example` | Estado remoto S3 con bloqueo, para activarlo como `backend_override.tf` |
| `infra/tofu.sh` | Ejecuta `tofu` o `terraform` en un contenedor, en la red `k3d-hub`, con el `kubeconfig` generado y `gitea.hub.local` resuelto |
| `infra/client-new.sh` | Valida y agrega un cliente al inventario: nombre repetido, plan inexistente o dominio fuera de `.hub.local` terminan con un mensaje y sin tocar nada |
| `infra/estado-remoto.sh` | Levanta el almacén de estado (SeaweedFS) y prueba, activa o detiene el estado remoto |
| `infra/pruebas/` | `drift.sh` (prueba de deriva) y `crear-cliente.sh` (crear, comprobar cuota y etiquetas, destruir) |

::: {custom-style="Nota"}
*Nota.* Elaboración propia a partir de `infra/`, leído el 16 de noviembre de 2026.
:::

## Variables, entornos y secretos

- **Variables:** `clients` (con dominio y código de plan) y `gitea_token`. Las cuotas de CPU y memoria de cada cliente salen del plan en `seed/plans.json`, no del inventario.
- **Entornos:** hay un único entorno, el laboratorio. El mismo código sirve para otro clúster cambiando el backend y la dirección de Gitea.
- **Secretos:** el token de Gitea se entrega por `TF_VAR_gitea_token` y está marcado como sensible; no se versiona. Las credenciales del estado remoto (`AWS_ACCESS_KEY_ID` y `AWS_SECRET_ACCESS_KEY`) van en el entorno y no en el código; el archivo con las credenciales generadas está ignorado por Git. La tarea T14 de la especificación 011 comprobó con `git grep` que no hay token ni estado en el repositorio.
- **Estado:** por defecto local, en el archivo `terraform.tfstate` de la carpeta `state`, que Git ignora. En laboratorio se puede pasar a un almacén compatible con S3 con bloqueo: dos `apply` simultáneos no se pisan porque `use_lockfile` guarda el bloqueo en el mismo almacén. El estado local y el remoto de laboratorio son un riesgo aceptado (decisión D13).
- **Versiones fijadas:** OpenTofu 1.13.2 (`ghcr.io/opentofu/opentofu:1.13.2`), Terraform 1.17.0, y SeaweedFS y la CLI de AWS por `digest`.

## Plan y aplicación

El flujo es `infra/client-new.sh <nombre> <dominio> <plan>` para agregar al inventario, `infra/tofu.sh tofu plan -detailed-exitcode` para ver qué cambiaría (código 0 sin cambios, 2 con diferencias) y `infra/tofu.sh tofu apply` para aplicar. Un código 2 es deriva y se revisa antes de aplicar. Para recrear un cliente se usa `apply` sobre el módulo o `destroy -target` para borrarlo.

## Evidencia de ejecución

::: {custom-style="Table Caption"}
**Tabla {T:evidencia-iac}**\
*Verificaciones de la infraestructura como código*
:::

| Verificación | Resultado | Fuente |
|----------------------|------------------------------|--------------------|
| Dos `apply` seguidos con el estado ya creado | La segunda ejecución informa 0 por agregar, 0 por cambiar y 0 por destruir | `specs/011-infraestructura-como-codigo/tasks.md` (T11) |
| Destruir y recrear la ferretería | El plan final queda sin diferencias, la Application `Synced` y `Healthy` y el sitio responde 200 | T12 |
| Mismo recorrido con Terraform | Mismos resultados con el mismo código | T13 |
| Importar los tres clientes existentes | El plan posterior no recrea nada y los sitios siguen respondiendo | T10 |
| Prueba de deriva (`infra/pruebas/drift.sh`) | Ejecutada el 16 de noviembre de 2026: plan en 0 tras aplicar, código 2 y nombre del recurso tras un cambio a mano, y plan otra vez en 0 tras reconciliar | Ejecución del 16 de noviembre de 2026 |
| `infra/pruebas/crear-cliente.sh` y `tofu plan` contra el clúster real | **No se corrieron el 16 de noviembre de 2026**: piden un token de administrador de Gitea | `docs/bitacora.md:30` |

::: {custom-style="Nota"}
*Nota.* Elaboración propia. Las verificaciones T10 a T13 se registraron como hechas en la especificación 011; el 16 de noviembre de 2026 solo se repitió la prueba de deriva. La captura E-24 del Apéndice A reúne la evidencia de la prueba de deriva.
:::

## Justificación de los recursos viables en laboratorio

El laboratorio es un solo equipo sin cuenta de nube. Por eso OpenTofu administra lo que existe allí: archivos en el repositorio de configuración (Gitea) y recursos de Kubernetes. No provisiona redes, máquinas ni almacenamiento de un proveedor, porque no hay proveedor. El clúster se reconstruye con scripts (`gitops/platform/k3s/crear-cluster.sh` y los scripts de `demo/`), y el estado remoto usa SeaweedFS como almacén compatible con S3 para mostrar el bloqueo de estado; en una nube bastaría cambiar el `endpoint` del backend. La reconstrucción completa del laboratorio desde cero depende entonces de OpenTofu para los clientes y de scripts para la plataforma.

# Plan 011 · Infraestructura como código

> Cómo se construye [la spec](spec.md). El HCL es el mismo para OpenTofu y Terraform; se prueba con ambos.

## Punto de partida

| Pieza | Estado | Dónde |
|---|---|---|
| Plantilla base del cliente (Namespace con PSA `restricted`, ResourceQuota, LimitRange, NetworkPolicy, Deployment, Service, Ingress) | Hecho (003) | `gitops/clients/_base/` |
| Carpeta por cliente (`kustomization.yaml` con parches de nombre, plan, cuota y host + `images.newTag`) | Hecho (003/005) | `gitops/clients/{restaurante,ferreteria,consultorio}/` |
| Una `Application` de Argo CD por cliente | Hecho (005), aplicadas a mano | `gitops/platform/argocd/applications/` |
| Cuotas por plan | Hecho (000) | `seed/plans.json` |
| `hub-gitops` en Gitea sembrado una vez | Hecho (003/005) | `sembrar-hub-gitops.sh`; las actualizaciones por commit las trae la 008 (`actualizar-hub-gitops.sh`) |
| Carpeta `infra/` | **No existe** | la crea esta spec (según [convenciones](../../constitution/conventions.md)) |

## Decisión 1: quién es dueño de qué (opción híbrida)

Para no tener dos dueños sobre lo mismo (OpenTofu y Argo CD) y no arriesgar un `prune` de Argo CD:

| Recurso | Dueño | Por qué |
|---|---|---|
| Namespace, ResourceQuota, LimitRange, NetworkPolicy, Deployment, Service, Ingress | **Git / Argo CD** (`_base` + overlay) | Ya existen y son la fuente del principio 3; se evita un segundo gestor |
| `clients/<c>/kustomization.yaml` en `hub-gitops` | **OpenTofu** (`gitea_repository_file`) | Es lo único que cambia entre clientes y es el punto de creación |
| `Application` de Argo CD del cliente | **OpenTofu** (`kubernetes_manifest`) | Hoy se aplica a mano; es lo que falta para automatizar |

El overlay que genera OpenTofu es idéntico en forma a los de la 003 (nombre, plan, cuota, host), con valores de
`plans.tf`. La **cuota sale de `seed/plans.json`** (`jsondecode(file("../../seed/plans.json"))`), nunca se copia.

`images.newTag` lo cambia después el Hub al publicar versiones (005). Por eso el recurso lleva
`lifecycle { ignore_changes = [content] }`: OpenTofu crea el archivo y no pelea con el Hub por él. El plan de
ejecución solo se vuelve a comparar contra la existencia del archivo (CA-3).

**Borrado en cascada:** la `Application` lleva el finalizador `resources-finalizer.argocd.argoproj.io`, de modo
que destruirla hace que Argo CD borre el namespace y todo lo del cliente. Orden de destrucción garantizado con
`depends_on`: primero la `Application`, después el archivo en Git (si se borrara el archivo antes, la
`Application` vería un camino inexistente).

## Decisión 2: cómo se ejecuta

Instalar `tofu` y `terraform` en cada PC es fricción; `infra/tofu.sh` corre el binario en un contenedor con
versión fija, en la red `k3d-hub` para llegar al clúster y a Gitea:

| Pieza | Versión | Nota |
|---|---|---|
| OpenTofu | 1.13.2 | `ghcr.io/opentofu/opentofu`, imagen oficial |
| Terraform | 1.17.0 | `hashicorp/terraform` (para CA-5) |
| Proveedor `hashicorp/kubernetes` | 3.4.0 | |
| Proveedor `go-gitea/gitea` | 0.8.1 | recurso `gitea_repository_file` |

`tofu.sh <tofu|terraform> <comando…>`:

1. Genera `infra/.kubeconfig` con `k3d kubeconfig get hub`, cambiando el servidor a
   `https://k3d-hub-serverlb:6443` (ignorado por Git).
2. Resuelve `gitea.hub.local` hacia el `serverlb` con `--add-host` (Gitea responde por Ingress).
3. Lee el token de Gitea de `GITEA_TOKEN` (variable de entorno, **nunca** en un archivo del repo) y lo pasa como
   `TF_VAR_gitea_token`.
4. Monta `infra/` (código) y `infra/state/` (estado), ambos fuera de Git salvo el código.

El estado es local en `infra/state/terraform.tfstate`, ignorado por `.gitignore`, con respaldo automático en
`infra/state/backups/` tras cada `apply` y ese directorio también ignorado (CA-4). El estado no guarda secretos
porque el token solo entra por variable de entorno.

## Estructura

```
infra/
├── README.md
├── .gitignore               # state/, .kubeconfig, *.tfvars (salvo el .example)
├── tofu.sh                  # ejecuta tofu o terraform en contenedor
├── client-new.sh            # agrega un cliente a clients.auto.tfvars.json y aplica
└── tofu/
    ├── providers.tf         # kubernetes y gitea, versiones fijas
    ├── plans.tf             # locals: planes leídos de seed/plans.json
    ├── clients.tf           # for_each sobre var.clients
    ├── variables.tf
    ├── clients.auto.tfvars.json.example
    └── modules/
        └── client-env/
            ├── main.tf      # gitea_repository_file + kubernetes_manifest Application
            ├── variables.tf # name, host, plan, quota, image_tag
            ├── outputs.tf
            └── overlay.tftpl
```

`clients.auto.tfvars.json` (con los clientes reales) **sí** se versiona: es el inventario de clientes, sin
secretos. Su forma: `{ "clients": { "ferreteria": { "host": "ferreteria.hub.local", "plan": "estandar" } } }`.

`overlay.tftpl` reproduce el `kustomization.yaml` de los clientes existentes (misma estructura, parches y
comentario de cabecera), con la imagen `gitea.hub.local/forja-digital/plantilla` y la etiqueta inicial
`var.image_tag` (por omisión `v1`). Un cliente nuevo arranca sirviendo la plantilla genérica de la 002 hasta que
la agencia publique su propia imagen.

## `client-new.sh`

```
infra/client-new.sh <nombre> <dominio> <plan>      # ej.: panaderia panaderia.hub.local basico
```

Valida (CA-8): nombre en minúsculas sin guiones bajos, único en `clients.auto.tfvars.json`, plan existente en
`seed/plans.json` y dominio terminado en `.hub.local`; agrega el cliente, corre `plan` y `apply`, y al final
imprime lo que falta a mano: la línea de `hosts` (`gitea/README`) y dar de alta al cliente en el Hub.

## Migración de los tres clientes existentes (CA-7)

1. Se importan los archivos y las `Application` con `tofu import` (`gitea_repository_file` y
   `kubernetes_manifest`): no se recrea nada.
2. Las carpetas `gitops/clients/<c>/kustomization.yaml` del monorepo siguen existiendo (siembran `hub-gitops`
   desde cero); el `plan` posterior al `import` debe mostrar solo diferencias de forma, que se absorben con
   `ignore_changes`.
3. `gitops/platform/argocd/applications/` deja de ser la forma de crear clientes nuevos; las tres actuales
   quedan administradas por OpenTofu y se documenta en `gitops/README.md`.

## Riesgos

| Riesgo | Respuesta |
|---|---|
| Doble gestión (Argo CD y OpenTofu sobre lo mismo) | Frontera de la decisión 1: OpenTofu solo es dueño del overlay y la `Application` |
| El Hub y OpenTofu se pisan el `newTag` | `ignore_changes = [content]` |
| `kubernetes_manifest` exige que el clúster responda al hacer `plan` | `tofu.sh` falla con un mensaje claro si el clúster no está arriba |
| Borrar un cliente borra sus datos (el namespace) | `destroy` solo se hace con `-target` explícito; `client-new.sh` no destruye nada; documentado en el README |
| Estado perdido | Respaldo tras cada `apply`; el estado se puede reconstruir con `import` (CA-7) |
| Token de Gitea en el repo | Solo entra por `GITEA_TOKEN`; `git grep` en la verificación |

## Cómo se verifica

- `tofu plan` sin cambios después de `apply` (CA-3).
- `tofu destroy -target='module.client["ferreteria"]'`, esperar a que el namespace desaparezca, `apply` y `plan`
  sin diferencias; el sitio responde otra vez (CA-2).
- Misma secuencia con `terraform` (CA-5).
- `git grep` no encuentra el token ni el estado en el repositorio (CA-4).
- `infra/pruebas/crear-cliente.sh`: crea y destruye un cliente `prueba` de punta a punta y comprueba cuota y
  etiquetas contra `seed/plans.json` (CA-1, CA-6).

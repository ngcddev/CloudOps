# Plan 011 · Infraestructura como código

> Cómo se construye [la spec](spec.md). Decisión pendiente: binario `tofu` o `terraform` (profesor,
> antes del 24 oct). El HCL es el mismo.

## Stack (módulo 4)

| Pieza | Herramienta |
|---|---|
| IaC | OpenTofu (compatible con Terraform) |
| Providers | `hashicorp/kubernetes`, `hashicorp/helm` |
| Bootstrap (opcional) | Ansible: instalar k3s en el PC A |

## Estructura

```
infra/
├── ansible/                 # opcional: playbook k3s.yml
└── tofu/
    ├── modules/
    │   └── client-env/      # namespace + labels PSA, quota, limitrange, networkpolicy, argocd Application
    │       ├── main.tf
    │       ├── variables.tf # name, host, plan, template, image_tag
    │       └── outputs.tf
    ├── platform/            # namespaces de plataforma, Helm releases (argocd, monitoring)
    ├── clients.tf           # for_each sobre var.clients
    ├── plans.tf             # locals: cuotas por plan (spec 000)
    ├── providers.tf
    └── clients.tfvars.example
```

## Decisiones

- **Qué gestiona OpenTofu:** el "contenedor" de cada cliente (namespace y políticas) y la
  `Application` de Argo CD. **Qué no:** los Deployments, que siguen en `hub-gitops` (principio 3).
- Estado local en `infra/tofu/terraform.tfstate`, ignorado por `.gitignore`; copia de respaldo
  fuera del repo.
- `make client-new NAME=panaderia HOST=panaderia.hub.local PLAN=basico` agrega la entrada al tfvars
  y ejecuta `tofu apply`.
- Migración: importar los recursos creados en la spec 003 con `tofu import` para no recrearlos.

## Riesgos

| Riesgo | Respuesta |
|---|---|
| Doble gestión (Argo CD y OpenTofu sobre lo mismo) | Frontera clara: OpenTofu no toca Deployments/Services/Ingress |
| Estado perdido | Respaldo del tfstate después de cada apply |

## Cómo se verifica

- `tofu plan` sin cambios después de `apply` (CA-3).
- `tofu destroy -target=module.client["ferreteria"]` + `apply` + `plan` sin diferencias (CA-2).
- Misma prueba con `terraform` (CA-5).

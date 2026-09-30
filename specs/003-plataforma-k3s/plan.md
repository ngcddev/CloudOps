# Plan 003 · Plataforma multi-cliente en k3s

> Cómo se construye [la spec](spec.md). Base: "Estructura de Kubernetes" y "Políticas de seguridad"
> de [constitution/tech-stack.md](../../constitution/tech-stack.md).

## Stack (módulo 2)

| Pieza | Herramienta |
|---|---|
| Clúster | k3s de un nodo en el PC A (trae Traefik como Ingress) |
| Aislamiento | Namespace, ResourceQuota, LimitRange, NetworkPolicy |
| Seguridad de Pods | Pod Security Admission `restricted` (etiqueta del namespace) |
| Imágenes | Registro de Gitea |
| Nombres | `hub.local` y subdominios en `/etc/hosts` (o DNS del router) apuntando al PC A |

## Estructura en el repo

```
gitops/
├── platform/
│   └── namespaces.yaml              # hub, argocd, monitoring, gitea
├── hub/                             # api, web, postgres (StatefulSet + PVC)
└── clients/
    ├── _base/                       # plantilla por cliente (kustomize)
    │   ├── namespace.yaml           # con etiquetas de Pod Security
    │   ├── resourcequota.yaml
    │   ├── limitrange.yaml
    │   ├── networkpolicy.yaml
    │   ├── deployment.yaml
    │   ├── service.yaml
    │   └── ingress.yaml
    ├── restaurante/kustomization.yaml   # nombre, host, imagen, plan
    ├── ferreteria/kustomization.yaml
    └── consultorio/kustomization.yaml   # + backend y ruta /api
```

## Manifiestos clave

- **Namespace:** etiquetas `pod-security.kubernetes.io/enforce: restricted`, `hub/client: <nombre>`,
  `hub/plan: <plan>`.
- **ResourceQuota:** `limits.cpu` y `limits.memory` según el plan (Básico 250m/256Mi, Estándar
  500m/512Mi, Premium 1000m/1Gi).
- **LimitRange:** requests/limits por defecto para que ningún Pod quede sin límites.
- **NetworkPolicy:** `default-deny` de entrada + permitir desde el namespace de Traefik
  (`kube-system`) y desde `monitoring`.
- **Deployment:** `runAsNonRoot: true`, `allowPrivilegeEscalation: false`,
  `capabilities.drop: [ALL]`, `seccompProfile: RuntimeDefault`, readiness/liveness en `/health`.
- **Ingress:** host `<cliente>.hub.local`; en el consultorio `/` → frontend y `/api` → backend.

## Contratos con otras specs

- Recibe de **002**: imágenes sin root en puerto 8080 con `/health`.
- Recibe de **000**: cuotas por plan.
- Entrega a **005**: carpeta `gitops/` que se siembra en el repo `hub-gitops` de Gitea.
- Entrega a **011**: los mismos recursos, luego generados con OpenTofu.

## Riesgos

| Riesgo | Respuesta |
|---|---|
| PC A sin RAM | Límites en todos los componentes; Backstage apagable |
| Traefik no respeta NetworkPolicy entre namespaces | Probar con un Pod `busybox` en la demo |
| `.local` resuelve por mDNS en algunos equipos | Entradas explícitas en `/etc/hosts` |

## Cómo se verifica

- `kubectl get ns --show-labels`, `kubectl describe quota -A`.
- `kubectl run --rm -it -n cliente-restaurante test --image=busybox -- wget ferreteria...` falla.
- `kubectl run root-test --image=nginx -n cliente-restaurante` es rechazado por Pod Security.

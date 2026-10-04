# Nombres canónicos

Todas las specs usan exactamente estos nombres. Si hace falta cambiarlos, se cambian aquí primero.

## Agencia y clientes

| Entidad | Nombre | Plan | Namespace | Host | Plantilla |
|---|---|---|---|---|---|
| Agencia | **Forja Digital** | — | `hub` | `hub.local` | — |
| Cliente 1 | Restaurante **La Sazón** | Premium | `cliente-restaurante` | `restaurante.hub.local` | Landing estática |
| Cliente 2 | Ferretería **El Tornillo** | Estándar | `cliente-ferreteria` | `ferreteria.hub.local` | Landing estática |
| Cliente 3 | Consultorio **Dental Popayán** | Básico | `cliente-consultorio` | `consultorio.hub.local` | Landing + formulario |

Namespaces de plataforma: `hub`, `argocd`, `monitoring`, `gitea`.

## Planes (propuesta; la spec 000 los confirma)

| Plan | SLO disponibilidad mensual | Atención | Cuota CPU / RAM (namespace) |
|---|---|---|---|
| Básico | 99,0 % | Lun–Vie 8:00–18:00 | 250m / 256Mi |
| Estándar | 99,5 % | Lun–Sáb 7:00–20:00 | 500m / 512Mi |
| Premium | 99,9 % | 24/7 | 1000m / 1Gi |

## Prioridades y SLA base (propuesta; la spec 000 los confirma)

| Prioridad | Significado | Respuesta | Solución |
|---|---|---|---|
| P1 | Crítica: el sitio no funciona o se pierden ventas | 15 min | 4 h |
| P2 | Alta: una función importante falla | 1 h | 8 h |
| P3 | Media: falla menor con alternativa | 4 h | 24 h |
| P4 | Baja: consulta o mejora | 8 h | 72 h |

## Estados

- **Ticket:** `abierto` → `en_progreso` → `en_espera` → `resuelto` → `cerrado`.
- **Incidente:** `abierto` → `mitigado` → `cerrado`.
- **Servicio (sitio):** `operativo` · `degradado` · `caido`.
- **Solicitud de cambio:** `pendiente` → `aprobada` → `en_validacion` → `desplegada` | `rechazada`.
- **Texto de IA:** `borrador_ia` → `aprobado` | `descartado`.

## Apps demo

- `v1` = versión sana; `v2` = versión rota que responde HTTP 500 en `/` y en `/health`.
- Todas exponen `GET /health` → `{"status":"ok","version":"v1"}`.

## Roles

- `agencia` (administrador y técnico de la agencia: ve todo).
- `cliente` (usuario de una PyME: ve solo lo suyo).

## Repositorios

- **GitHub `ngcddev/CloudOps`**: monorepo de desarrollo (este).
- **Gitea `hub-gitops`**: repo que Argo CD vigila; se siembra desde `gitops/`. El Hub escribe aquí los cambios de versión y los rollback.

## Herramientas de plataforma (módulo 2)

| Qué | Dirección / nombre |
|---|---|
| Gitea | `gitea.hub.local` · organización `forja-digital` |
| Registro de imágenes | `gitea.hub.local/forja-digital/<app>:<versión>` (`restaurante`, `ferreteria`, `consultorio-web`, `consultorio-api`) |
| Repo GitOps | `forja-digital/hub-gitops` |
| Argo CD | `argocd.hub.local` |

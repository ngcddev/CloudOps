# Mapa de especificaciones

> Las 16 specs cubren todos los [requerimientos](../docs/requerimientos.md). La 000 es la única
> propia del diseño del servicio (industrial) y alimenta a varias de las demás; el resto es de todo
> el equipo. Cómo se trabaja cada una: [docs/sdd.md](../docs/sdd.md).

## Tabla

**Acciona** dice quién ejecuta la spec: los ingenieros de **Sistemas**, el ingeniero **Industrial** o ambos. El detalle por rol está al inicio de cada `spec.md`.

| Spec | Nombre | Acciona | Módulo | Requerimientos | Depende de | Estado |
|---|---|---|---|---|---|---|
| [000](000-modelo-de-servicio/spec.md) | Modelo de servicio (industrial) | Industrial | 1–2 | Planes, P1–P4, SLA, KPI | — | Tareas listas |
| [001](001-clientes-y-planes/spec.md) | Clientes y planes | Sistemas · apoya Industrial | 1 | RF-01, RF-02 | 000 | Tareas listas |
| [002](002-plantillas-de-sitio/spec.md) | Plantillas de sitio y apps demo | Sistemas | 1 | RNF-01, RNF-02 | — | Tareas listas |
| [003](003-plataforma-k3s/spec.md) | Plataforma multi-cliente en k3s | Sistemas · apoya Industrial | 2 | RF-03, RNF-03 | 002 | Spec y plan |
| [004](004-mesa-de-servicio/spec.md) | Mesa de servicio: tickets y prioridad | Sistemas · apoya Industrial | 2 | RF-04, RF-05 | 000, 001 | Spec y plan |
| [005](005-cambios-gitops/spec.md) | Cambios por GitOps | Sistemas | 2 | RF-06, RF-07, RF-22, RNF-04 | 003, 004 | Spec y plan |
| [006](006-puerta-de-seguridad/spec.md) | Puerta de calidad y seguridad | Sistemas | 3 | RF-08, RF-09, RNF-05, RNF-06 | 005 | Spec y plan |
| [007](007-roles-y-auditoria/spec.md) | Acceso por roles y auditoría | Sistemas | 3 | RF-01 (roles), RF-10 | 001 | Spec y plan |
| [008](008-monitoreo-e-incidentes/spec.md) | Monitoreo e incidente automático | Sistemas · apoya Industrial | 4 | RF-11, RF-12, RF-13, RNF-07 | 000, 003, 004 | Spec y plan |
| [009](009-rollback/spec.md) | Recuperación por rollback | Sistemas | 4 | RF-14 | 005, 008 | Spec y plan |
| [010](010-dashboards/spec.md) | Dashboards y métricas del servicio | Sistemas · apoya Industrial | 4 | RF-15, RF-16, RF-17, RNF-10 | 008, 009 | Spec y plan |
| [011](011-infraestructura-como-codigo/spec.md) | Infraestructura como código | Sistemas | 4 | RNF-08 | 003 | Spec y plan |
| [012](012-asistente-ia/spec.md) | Asistente de incidentes con IA local | Sistemas · apoya Industrial | 5 | RF-18, RF-19, RNF-09 | 008 | Spec y plan |
| [013](013-reportes/spec.md) | Reportes operativo y ejecutivo | Industrial + Sistemas | 5 | RF-20 | 010 | Spec y plan |
| [014](014-infografia/spec.md) | Infografía mensual | Sistemas · apoya Industrial | 6 | RF-21, RF-23 | 010, 013 | Spec y plan |
| [015](015-demo-integrada/spec.md) | Demo integrada | Todo el equipo | 7 | RNF-11 | todas | Spec y plan |

**Estados posibles:** Spec y plan → Tareas listas → En curso → Terminada (criterios pasan en la demo).

## Orden de arranque

- **Ya (módulo 1):** 000, 001 y 002.
- **Pueden adelantarse (solo producto):** 004 y la parte de backend/frontend de 007, 008 (incidentes
  manuales), 010 y 013.
- **Esperan su módulo:** todo lo que instala herramientas de plataforma (003, 005, 006,
  008-monitoreo, 009, 011, 012, 014).

## Dependencias

```
000 ─┬─> 001 ─┬─> 004 ─┬─> 005 ──> 006
     │        │        │     └────────> 009 ──> 010 ──> 013 ──> 014
     │        └─> 007  └─> 008 ──┘       ↑        ↑
002 ──> 003 ──┬─> 005             008 ───┘        │
              ├─> 008 ──> 012                     │
              └─> 011                   010 ──────┘
Todas ──> 015
```

## Abrir una spec nueva

Copiar [`_plantilla/`](_plantilla/spec.md) a `specs/NNN-nombre/`, llenar `spec.md` sin mencionar
tecnología, pasar a `plan.md` y, cuando el módulo ya se haya visto, escribir `tasks.md`.

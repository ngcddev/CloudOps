# Mapa de especificaciones

> Las 24 specs del proyecto (000 a 023). La 000 es la del diseño del servicio (industrial); de la 016 a la 023 se agregaron después del plan inicial (alta en vivo, cierres de módulo, voz, sincronía GitOps y entrega final). Cómo se trabaja cada una: [docs/sdd.md](../docs/sdd.md).
>
> La tabla se regenera desde el encabezado de cada `spec.md` y desde sus `tasks.md` (el conteo de tareas no se escribe a mano). Los requerimientos de la columna son los originales de [docs/requerimientos.md](../docs/requerimientos.md).

## Tabla

**Acciona** dice quién ejecuta la spec: los ingenieros de **Sistemas**, el ingeniero **Industrial** o ambos.

| Spec | Nombre | Acciona | Módulo | Requerimientos | Depende de | Estado | Tareas hechas / total |
|---|---|---|---|---|---|---|---|
| [000](000-modelo-de-servicio/spec.md) | Modelo de servicio (industrial) | Industrial · Sistemas apoya validando que cada regla y KPI se pueda medir en el Hub | 1–2 | Planes, P1–P4, SLA, KPI | — | En curso | 4 / 5 |
| [001](001-clientes-y-planes/spec.md) | Clientes y planes | Sistemas (Backend, Frontend) · Industrial valida planes y SLA | 1 | RF-01, RF-02 | 000 | Terminada | 12 / 12 |
| [002](002-plantillas-de-sitio/spec.md) | Plantillas de sitio y apps demo | Sistemas (Cloud / Platform, Frontend) | 1 | RNF-01, RNF-02 | — | Terminada | 11 / 11 |
| [003](003-plataforma-k3s/spec.md) | Plataforma multi-cliente en k3s | Sistemas (Cloud / Platform) · Industrial aporta las cuotas por plan | 2 | RF-03, RNF-03 | 002 | Terminada | 18 / 18 |
| [004](004-mesa-de-servicio/spec.md) | Mesa de servicio: tickets y prioridad | Sistemas (Backend, Frontend) · Industrial valida la matriz P1–P4 y el flujo de estados | 2 (producto: puede adelantarse) | RF-04, RF-05 | 000, 001 | Terminada | 20 / 20 |
| [005](005-cambios-gitops/spec.md) | Cambios por GitOps | Sistemas (Cloud / Platform, Backend) | 2 | RF-06, RF-07, RF-22, RNF-04 | 003, 004 | Terminada | 25 / 25 |
| [006](006-puerta-de-seguridad/spec.md) | Puerta de calidad y seguridad | Sistemas (DevSecOps / SRE, Backend, Frontend) | 3 | RF-08, RF-09, RNF-05, RNF-06 | 005 | Terminada | 24 / 24 |
| [007](007-roles-y-auditoria/spec.md) | Acceso por roles y auditoría | Sistemas (Backend, Frontend) | 3 (producto: puede adelantarse) | RF-01 (roles), RF-10 | 001, 004, 005 | Terminada | 21 / 21 |
| [008](008-monitoreo-e-incidentes/spec.md) | Monitoreo e incidente automático | Sistemas (DevSecOps / SRE, Backend, Frontend) · Industrial valida el cálculo del SLA | 4 (los incidentes manuales y sus pantallas pueden adelantarse) | RF-11, RF-12, RF-13, RNF-07 | 000, 003, 004, 005, 007 | En curso | 30 / 33 |
| [009](009-rollback/spec.md) | Recuperación por rollback | Sistemas (Cloud / Platform, Backend, Frontend) | 4 | RF-14 | 005, 007, 008 | Terminada | 17 / 17 |
| [010](010-dashboards/spec.md) | Dashboards y métricas del servicio | Sistemas (Frontend, Backend) · Industrial define los KPI y hace la prueba con personas no técnicas | 4 (las vistas con datos del Hub se pueden adelantar) | RF-15, RF-16, RF-17, RNF-10 | 004, 005, 007, 008, 009 | Terminada | 20 / 20 |
| [011](011-infraestructura-como-codigo/spec.md) | Infraestructura como código | Sistemas (Cloud / Platform) | 4 | RNF-08 | 003, 005 | En curso | 14 / 15 |
| [012](012-asistente-ia/spec.md) | Asistente de incidentes con IA local | Sistemas (Backend) · Industrial revisa que los mensajes al cliente no tengan jerga | 5 | RF-18, RF-19, RF-25, RNF-09 | 008 | En curso | 22 / 30 |
| [013](013-reportes/spec.md) | Reportes operativo y ejecutivo | Industrial (contenido y formato) y Sistemas (Backend, Frontend) | 5 (puede adelantarse con datos del Hub) | RF-20 | 010 | En curso | 6 / 8 |
| [014](014-infografia/spec.md) | Infografía mensual | Sistemas (Frontend, Backend) · Industrial define el contenido de la infografía | 6 | RF-21, RF-23 | 010, 013 | Pospuesta | sin tasks.md |
| [015](015-demo-integrada/spec.md) | Demo integrada | Todo el equipo (Sistemas e Industrial) | 7 | RNF-11 | todas | Spec y plan | sin tasks.md |
| [016](016-alta-de-sitio-y-demo-colegio/spec.md) | Alta de sitio por GitOps y demo del colegio | Equipo de Sistemas | — | — | 001, 003, 005, 008, 009, 015 | Implementada y probada en el clúster (14 nov 2026) | 13 / 15 |
| [017](017-cierre-modulo-2/spec.md) | Cierre del módulo 2 (Kubernetes, GitOps y Platform Engineering) | Equipo de Sistemas | 2 | — | 003, 005, 011, 016 | Implementada y probada en el clúster (15 nov 2026) | 6 / 6 |
| [018](018-cierre-modulo-3/spec.md) | Cierre del módulo 3 (DevSecOps y seguridad de la cadena de suministro) | Equipo de Sistemas | 3 | — | 006, 007, 016, 017 | Terminada (todas sus tareas cerradas; verificado en la corrida de evidencias del 16–17 nov 2026) | 7 / 7 |
| [019](019-cierre-modulo-4/spec.md) | Cierre del módulo 4 (IaC, observabilidad, SRE y operación sostenible) | Equipo de Sistemas | 4 | — | 008, 010, 011, 016 | Terminada (todas sus tareas cerradas; verificado en la corrida de evidencias del 16–17 nov 2026) | 6 / 6 |
| [020](020-cierre-modulo-5/spec.md) | Cierre del módulo 5 (MLOps, LLMOps y serving de IA local) | Equipo de Sistemas | 5 | — | 012, 016, 019 | En curso | 6 / 7 |
| [021](021-voz-del-asistente/spec.md) | Voz del asistente (componente multimodal, módulo 6) | Equipo de Sistemas | 6 | — | 012, 019, 020 | Terminada (todas sus tareas cerradas; voz verificada en navegador real el 17 nov 2026) | 9 / 9 |
| [022](022-sincronia-gitops/spec.md) | Sincronía simple y correcta entre el repositorio principal y hub-gitops | Equipo de Sistemas | 2 (GitOps) | — | 005, 016, 017 | Terminada (todas sus tareas cerradas; sincronía verificada el 16 nov 2026) | 37 / 37 |
| [023](023-entrega-final/spec.md) | Entrega final: informe consolidador | Sistemas (redacción técnica y verificación contra el código) · Industrial (contexto, partes interesadas, riesgos de cronograma) | 7 | — | 015, 019, 020, 021 | En curso | 9 / 10 |

**Estados posibles:** Spec y plan → Tareas listas → En curso → Terminada (criterios pasan en la demo). «Pospuesta» indica que se reemplazó por otra spec.

La verificación de lo construido (pruebas, demos de punta a punta y evaluación de IA) está en el paquete de evidencias: [`entrega/evidencias/`](../entrega/evidencias/).

## Abrir una spec nueva

Copiar [`_plantilla/`](_plantilla/spec.md) a `specs/NNN-nombre/`, llenar `spec.md` sin mencionar
tecnología, pasar a `plan.md` y, cuando el módulo ya se haya visto, escribir `tasks.md`.

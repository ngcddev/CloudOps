# CloudOps Client Hub

> Un centro de operación de servicios digitales para agencias que administran múltiples clientes.

CloudOps Client Hub **no es otro Vercel**. Ayuda a una agencia digital a gestionar el servicio completo que presta a sus clientes: solicitudes, cambios, despliegues, monitoreo, incidentes, recuperación, calidad y reportes.

Proyecto integrador del diplomado **CloudForge AI 5.0** (Unicomfacauca), 28 sep – 30 nov 2026.

**Empieza por aquí:** [constitución](constitution.md) · [cómo trabajamos (SDD)](docs/sdd.md) · [mapa de specs](specs/README.md) · [requerimientos](docs/requerimientos.md) · [calendario](docs/calendario.md) · [stack](docs/tech-stack.md) · [glosario](docs/glosario.md)

## Tabla de contenidos

- [El problema](#el-problema)
- [Diferencia frente a Vercel](#diferencia-frente-a-vercel)
- [Flujo de operación](#flujo-de-operación)
- [Diferenciales](#diferenciales)
- [Ejemplo: falla en el sitio de un restaurante](#ejemplo-falla-en-el-sitio-de-un-restaurante)
- [Aporte del ingeniero industrial](#aporte-del-ingeniero-industrial)
- [Alcance de la demo](#alcance-de-la-demo)
- [Arquitectura del laboratorio](#arquitectura-del-laboratorio)
- [Cómo trabajamos (SDD)](#cómo-trabajamos-sdd)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Equipo y roles](#equipo-y-roles)

## El problema

Publicar una página ya está resuelto por plataformas como Vercel. Lo que sigue sin resolverse, sobre todo para agencias pequeñas, es lo que pasa **después** de publicar:

- ¿Qué cliente pidió un cambio y cuándo se atiende?
- ¿Qué pasa si la página cae?
- ¿Cuánto tardó la solución y se cumplió lo prometido?
- ¿Qué se le informa al cliente?
- ¿Cuánto soporte consume cada cuenta?

CloudOps Client Hub organiza esas respuestas en un mismo sistema.

## Diferencia frente a Vercel

| Tema | Vercel | CloudOps Client Hub |
|---|---|---|
| Usuario principal | Desarrollador o equipo de producto | Agencia digital, soporte y cliente PyME |
| Problema central | Publicar y operar aplicaciones web | Gestionar el servicio de varios clientes |
| Inicio del flujo | Repositorio de código | Cliente, proyecto, servicio y acuerdo de atención |
| Monitoreo | Métricas y errores de la aplicación | Métricas conectadas con incidentes, SLA y reportes |
| Rollback | Volver a una versión anterior | Volver a versión estable y registrar incidente, causa y tiempo de recuperación |
| Tickets y solicitudes de cambio | No es su foco principal | Parte central del producto |
| Portal para cliente no técnico | No es su foco principal | Diseñado específicamente para esto |
| SLA y prioridades | No es la propuesta central | Se definen, miden y reportan por cliente o plan |
| Rentabilidad y capacidad | No es su foco | Indicadores de carga, costos y horas de soporte |
| IA local privada | No es su enfoque | Asistente local para apoyo operativo supervisado |
| Alcance | Plataforma global de despliegue | Producto acotado para agencias y PyMEs |

> Vercel responde: *"Tengo código, ¿cómo lo publico rápido?"*
> CloudOps Client Hub responde: *"Tengo varios clientes, ¿cómo organizo su soporte, detecto problemas, cumplo tiempos y explico el valor del servicio?"*

## Flujo de operación

El despliegue es una pieza necesaria, no el producto completo. Cada sitio o aplicación se trata como un **servicio** con cliente, responsables, prioridad, historial, versiones, alertas, incidentes y reportes.

```
Cliente solicita un cambio o el sistema detecta una falla
  → Se clasifica el caso y se asigna prioridad
  → El equipo realiza el cambio o corrección
  → Se valida antes de publicar
  → Se despliega de forma controlada
  → Se monitorea el resultado
  → Si algo falla, se recupera una versión estable
  → Se registra el incidente y se informa al cliente
  → Se mide el servicio y se mejora el proceso
```

## Diferenciales

1. **El servicio empieza en el cliente, no en el código.** Una página es un servicio con cliente, plan de atención, responsable y condiciones de calidad: historial de solicitudes, cambios e incidentes, criticidad, SLA, versiones recuperables, evidencias de seguridad y reportes periódicos.
2. **Traduce lo técnico a lenguaje de negocio.**

   | Dato técnico | Cómo lo ve el cliente |
   |---|---|
   | 99,2 % de disponibilidad | "Su sitio se mantuvo disponible dentro del objetivo acordado." |
   | Error HTTP 500 | "Se detectó una falla temporal y se activó el proceso de recuperación." |
   | Rollback de un despliegue | "Se restauró una versión estable para mantener la continuidad." |
   | Latencia elevada | "El sitio presentó lentitud y se inició una acción de mejora." |
   | Vulnerabilidad en una dependencia | "Una actualización fue detenida antes de publicarse por controles de seguridad." |

3. **Convierte el mantenimiento web en un servicio medible:** disponibilidad, cambios realizados, incidentes atendidos, tiempos de respuesta y recuperación, seguridad y mejoras.
4. **Puede operar con infraestructura propia:** contenedores, Kubernetes, GitOps, observabilidad y modelo local, sin depender de un proveedor comercial para la demo.

## Ejemplo: falla en el sitio de un restaurante

| Paso | Qué hace CloudOps Client Hub |
|---|---|
| 1. Detección | El monitoreo identifica que el sitio no responde. |
| 2. Incidente | Se crea un incidente asociado al cliente "Restaurante". |
| 3. Prioridad | Se clasifica como **P1** (puede afectar reservas o pedidos). |
| 4. SLA | Inicia la medición: respuesta en 15 min, solución objetivo en 4 h. |
| 5. Diagnóstico | El responsable revisa alertas, logs y cambios recientes. |
| 6. Recuperación | Rollback a una versión estable desde GitOps. |
| 7. Verificación | Las métricas confirman la recuperación. |
| 8. Comunicación | El cliente recibe una explicación sencilla de lo ocurrido. |
| 9. Mejora | El caso queda en el reporte y se evalúa ajustar el proceso o automatizar una prueba. |

## Aporte del ingeniero industrial

Los ingenieros de sistemas construyen la plataforma que publica, monitorea y recupera; el ingeniero industrial diseña **cómo se presta el servicio y cómo se mide** si se hace bien.

| Área | Aporte | Resultado en el producto |
|---|---|---|
| Proceso | Modela el paso a paso de solicitud a cierre | Flujo de tickets, estados, responsables y aprobaciones |
| Priorización | Define P1–P4 según impacto y urgencia | Reglas de clasificación y escalamiento |
| SLA | Define tiempos objetivo de respuesta y solución | Medición automática de cumplimiento |
| Indicadores | Diseña KPI técnicos, operativos y de negocio | Dashboards de SLA, MTTR, tickets, carga y calidad |
| Capacidad | Estima cuántos clientes y tickets puede atender el equipo | Alertas de sobrecapacidad |
| Costos | Analiza horas de soporte y costo por cliente o plan | Información para rentabilidad y planes |
| Mejora continua | Identifica reprocesos, fallas recurrentes y cuellos de botella | Acciones correctivas y automatización |
| Experiencia del cliente | Define qué debe entender el cliente | Reportes claros y portal no técnico |

## Alcance de la demo

Clientes demo (ficticios): Restaurante **La Sazón** (Premium), Ferretería **El Tornillo** (Estándar) y Consultorio **Dental Popayán** (Básico), atendidos por la agencia **Forja Digital**.

- [ ] Registrar una agencia y tres clientes ficticios — [001](specs/001-clientes-y-planes/spec.md)
- [ ] Crear un proyecto o servicio por cliente — [001](specs/001-clientes-y-planes/spec.md)
- [ ] Desplegar aplicaciones demo con contenedores y Kubernetes — [002](specs/002-plantillas-de-sitio/spec.md), [003](specs/003-plataforma-k3s/spec.md)
- [ ] Ejecutar validación automática antes de publicar — [006](specs/006-puerta-de-seguridad/spec.md)
- [ ] Dashboard técnico para la agencia y uno simplificado para el cliente — [010](specs/010-dashboards/spec.md)
- [ ] Simular una falla controlada — [002](specs/002-plantillas-de-sitio/spec.md)
- [ ] Detectarla por monitoreo y abrir un incidente — [008](specs/008-monitoreo-e-incidentes/spec.md)
- [ ] Clasificar prioridad, asignar responsable y medir SLA — [000](specs/000-modelo-de-servicio/spec.md), [004](specs/004-mesa-de-servicio/spec.md), [008](specs/008-monitoreo-e-incidentes/spec.md)
- [ ] Recuperar el servicio mediante rollback — [009](specs/009-rollback/spec.md)
- [ ] Generar un reporte operativo y ejecutivo — [013](specs/013-reportes/spec.md)
- [ ] Usar un asistente local para resumir el incidente, con verificación humana — [012](specs/012-asistente-ia/spec.md)
- [ ] Generar una infografía operativa como componente visual o multimodal — [014](specs/014-infografia/spec.md)

## Arquitectura del laboratorio

Contenedores · Kubernetes · GitOps · Pipelines con validaciones de seguridad · Observabilidad (métricas, logs, alertas) · Modelo de IA local

| Capa | Herramienta |
|---|---|
| Hub | FastAPI + PostgreSQL · React + Vite + TypeScript |
| Kubernetes | k3s (Traefik) |
| Git, CI y registro | Gitea + Gitea Actions |
| GitOps | Argo CD · catálogo en Backstage |
| Seguridad | Gitleaks, Trivy, Syft, Cosign, Pod Security Admission |
| Observabilidad | Prometheus, Grafana, Alertmanager, Loki, Blackbox Exporter, OpenTelemetry |
| IaC | OpenTofu (compatible con Terraform), Ansible opcional |
| IA local | Ollama (7–8B), AnythingLLM, MLflow, ComfyUI (SD 1.5) |

Dos equipos: **PC A** (plataforma: k3s, Hub, Gitea, Argo CD, observabilidad y sitios) y **PC B** (IA: Ollama, AnythingLLM, MLflow, ComfyUI). Detalle en [docs/tech-stack.md](docs/tech-stack.md).

```
Push a Gitea → Gitea Actions (Gitleaks → build → Trivy → Syft → Cosign → verify)
  → tag en hub-gitops → Argo CD sincroniza el namespace del cliente
  → Blackbox Exporter vigila → Alertmanager avisa al Hub → incidente P1 + SLA
  → rollback (git revert) → métrica verde → MTTR → resumen con IA local aprobado por un humano
```

## Cómo trabajamos (SDD)

El proyecto usa **Spec-Driven Development**: una [constitución](constitution.md) con 10 principios y
[16 specs](specs/README.md) derivadas de los [requerimientos](docs/requerimientos.md). Cada spec
pasa por `spec.md` (qué y por qué) → `plan.md` (cómo) → `tasks.md` (pasos de menos de un día) →
implementación, y se cierra con una demo. Las herramientas de plataforma entran solo cuando el
diplomado ya cubrió su módulo. Detalle en [docs/sdd.md](docs/sdd.md).

| Módulo | Fechas | Specs |
|---|---|---|
| 1 · Contenedores | 28 sep – 1 oct | 000, 001, 002 |
| 2 · Kubernetes y GitOps | 2 – 13 oct | 003, 004, 005 |
| 3 · DevSecOps | 16 – 24 oct | 006, 007 |
| 4 · IaC y observabilidad | 24 oct – 3 nov | 008, 009, 010, 011 |
| 5 · IA local | 3 – 12 nov | 012, 013 |
| 6 · IA multimodal | 13 – 20 nov | 014 |
| 7 · Integrador | 24 – 30 nov | 015 |

## Estructura del repositorio

```
cloudops/
├── constitution.md    # principios, stack por módulo y nombres canónicos
├── CLAUDE.md          # reglas para trabajar con asistentes de código
├── docs/              # requerimientos, calendario, stack, glosario, guía SDD
├── specs/             # mapa, plantilla y las 16 specs (000–015)
├── backend/           # API FastAPI (desde la spec 001)
├── frontend/          # consola de agencia y portal del cliente (desde la spec 001)
├── apps/              # plantillas y sitios demo de clientes (spec 002)
├── gitops/            # manifiestos Kubernetes → repo hub-gitops en Gitea (spec 003)
├── pipelines/         # Gitea Actions (spec 006)
├── observability/     # Prometheus, Alertmanager, Grafana, Loki (spec 008)
├── infra/             # OpenTofu y Ansible (spec 011)
├── ai/                # prompts, evaluación, integración con Ollama/MLflow/ComfyUI (specs 012, 014)
├── seed/              # datos semilla (specs 000, 001, 015)
└── demo/              # guion y reinicio de la demo (spec 015)
```

Las carpetas de código aparecen cuando su spec empieza. Para contribuir: tomar una tarea de
`tasks.md`, crear la rama `feat/<spec>-t<NN>-<slug>` y abrir un PR con la plantilla.

## Equipo y roles

| Integrante | Rol | Aporta |
|---|---|---|
| Sistemas 1 | Cloud / Platform | Kubernetes, GitOps, manifiestos, infraestructura y despliegue |
| Sistemas 2 | Backend | API, usuarios, roles, clientes, tickets, SLA y base de datos |
| Sistemas 3 | DevSecOps / SRE | Pipelines, seguridad, observabilidad, alertas, logs y recuperación |
| Sistemas 4 | Frontend / Producto | Portal de cliente, consola de agencia, UX y dashboards |
| Industrial | Operación de servicios | Procesos, prioridades, SLA, KPI, capacidad, costos y mejora continua |

## Conclusión

La propuesta no compite con Vercel en despliegue global. Usa capacidades cloud-native (contenedores, Kubernetes, GitOps, seguridad, observabilidad y recuperación) para profesionalizar la operación y la relación de servicio entre agencias digitales y PyMEs: una página web deja de ser una entrega puntual y se convierte en un servicio administrado, medible y mejorable.

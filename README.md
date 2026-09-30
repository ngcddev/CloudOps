# CloudOps Client Hub

> Un centro de operación de servicios digitales para agencias que administran múltiples clientes.

CloudOps Client Hub **no es otro Vercel**. Ayuda a una agencia digital a gestionar el servicio completo que presta a sus clientes: solicitudes, cambios, despliegues, monitoreo, incidentes, recuperación, SLA, calidad y reportes. El despliegue es una capacidad interna, no el producto.

Proyecto integrador del diplomado **CloudForge AI 5.0** (Unicomfacauca), 28 sep – 30 nov 2026. Equipo de 5: 4 ingenieros de sistemas y 1 ingeniero industrial.

**Documentos de referencia:** [constitución](constitution.md) · [cómo trabajamos (SDD)](docs/sdd.md) · [mapa de specs](specs/README.md) · [requerimientos](docs/requerimientos.md) · [calendario](docs/calendario.md) · [tech stack](docs/tech-stack.md) · [glosario](docs/glosario.md)

## Tabla de contenidos

- [Estado actual](#estado-actual)
- [El problema](#el-problema)
- [Diferencia frente a Vercel](#diferencia-frente-a-vercel)
- [Flujo de operación](#flujo-de-operación)
- [Diferenciales](#diferenciales)
- [Caso demo: falla en el sitio de un restaurante](#caso-demo-falla-en-el-sitio-de-un-restaurante)
- [Agencia, clientes y planes](#agencia-clientes-y-planes)
- [Tech stack](#tech-stack)
- [Hardware](#hardware)
- [Arquitectura](#arquitectura)
- [Seguridad](#seguridad)
- [Sitios de cliente](#sitios-de-cliente)
- [Qué audita el sistema por cliente](#qué-audita-el-sistema-por-cliente)
- [Cómo trabajamos (SDD)](#cómo-trabajamos-sdd)
- [Especificaciones](#especificaciones)
- [Calendario](#calendario)
- [Alcance de la demo](#alcance-de-la-demo)
- [Equipo y roles](#equipo-y-roles)
- [Aporte del ingeniero industrial](#aporte-del-ingeniero-industrial)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Convenciones](#convenciones)
- [Cómo contribuir](#cómo-contribuir)
- [Decisiones pendientes](#decisiones-pendientes)
- [Riesgos](#riesgos)
- [Fuera de alcance](#fuera-de-alcance)
- [Conclusión](#conclusión)

## Estado actual

> Módulo 1 (28 sep – 1 oct). El repositorio contiene **solo documentación**: todavía no hay código,
> contenedores ni plataforma instalada.

| Qué | Estado |
|---|---|
| Constitución, requerimientos, calendario, stack, glosario y guía SDD | Listos |
| 16 specs (`spec.md` + `plan.md`, de 000 a 015) | Listas |
| `tasks.md` de 000, 001 y 002 (módulo 1) | Listos, sin tareas tomadas |
| `tasks.md` de 003 a 015 | Se escriben al empezar su módulo |
| Código del Hub, sitios demo, manifiestos, pipelines | Aún no existen |

**Siguiente paso:** el Industrial arranca la [spec 000](specs/000-modelo-de-servicio/tasks.md)
(matriz P1–P4 antes del 2 oct), y Sistemas arranca las [specs 001](specs/001-clientes-y-planes/tasks.md)
y [002](specs/002-plantillas-de-sitio/tasks.md).

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

Cada sitio se trata como un **servicio** con cliente, responsables, prioridad, historial, versiones, alertas, incidentes y reportes. El flujo empieza en el cliente: cliente → proyecto → servicio → acuerdo (plan + SLA).

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
2. **Traduce lo técnico a lenguaje de negocio** (lista completa en el [glosario](docs/glosario.md)).

   | Dato técnico | Cómo lo ve el cliente |
   |---|---|
   | 99,2 % de disponibilidad | "Su sitio se mantuvo disponible dentro del objetivo acordado." |
   | Error HTTP 500 | "Se detectó una falla temporal y se activó el proceso de recuperación." |
   | Rollback de un despliegue | "Se restauró una versión estable para mantener la continuidad." |
   | Latencia elevada | "El sitio presentó lentitud y se inició una acción de mejora." |
   | Vulnerabilidad en una dependencia | "Una actualización fue detenida antes de publicarse por controles de seguridad." |

3. **Convierte el mantenimiento web en un servicio medible:** disponibilidad, cambios realizados, incidentes atendidos, tiempos de respuesta y recuperación, seguridad y mejoras.
4. **Opera con infraestructura propia:** contenedores, Kubernetes, GitOps, observabilidad y modelo de IA local, sin depender de un proveedor comercial y sin que ningún dato de clientes salga del laboratorio.

## Caso demo: falla en el sitio de un restaurante

El sitio del Restaurante La Sazón cae tras desplegar la `v2`:

| Paso | Qué hace CloudOps Client Hub | Herramienta |
|---|---|---|
| 1. Detección | El monitoreo detecta HTTP 500 y avisa al Hub en ≤ 1 min | Blackbox Exporter → Prometheus → Alertmanager |
| 2. Incidente | Se abre un incidente asociado a La Sazón | Webhook del Hub |
| 3. Prioridad | Se clasifica como **P1** (afecta reservas y pedidos) | Matriz P1–P4 |
| 4. SLA | Arranca el reloj: respuesta 15 min, solución 4 h, con hora real | Hub |
| 5. Diagnóstico | El técnico revisa alertas, logs y el último cambio | Grafana, Loki, historial de Argo CD |
| 6. Recuperación | Pulsa **Rollback**: `git revert` en `hub-gitops` | Gitea + Argo CD |
| 7. Verificación | La métrica vuelve a verde; el incidente se cierra con su MTTR | Prometheus |
| 8. Comunicación | La IA local redacta el resumen y el mensaje; un humano los aprueba | Ollama + AnythingLLM |
| 9. Mejora | El caso queda en el reporte mensual y en la infografía | Hub + ComfyUI |

Mensaje al cliente: *"Detectamos una falla temporal en su sitio a las {hora}. Activamos la recuperación y a las {hora_fin} el servicio volvió a funcionar. Tiempo total: {min} minutos."*

## Agencia, clientes y planes

Todos los datos de la demo son ficticios.

| Entidad | Nombre | Plan | Namespace | Host | Plantilla |
|---|---|---|---|---|---|
| Agencia | **Forja Digital** | — | `hub` | `hub.local` | — |
| Cliente 1 | Restaurante **La Sazón** | Premium | `cliente-restaurante` | `restaurante.hub.local` | Landing estática |
| Cliente 2 | Ferretería **El Tornillo** | Estándar | `cliente-ferreteria` | `ferreteria.hub.local` | Landing estática |
| Cliente 3 | Consultorio **Dental Popayán** | Básico | `cliente-consultorio` | `consultorio.hub.local` | Landing + formulario |

**Planes** (propuesta; la [spec 000](specs/000-modelo-de-servicio/spec.md) los confirma):

| Plan | SLO disponibilidad mensual | Atención | Cuota CPU / RAM |
|---|---|---|---|
| Básico | 99,0 % | Lun–Vie 8:00–18:00 | 250m / 256Mi |
| Estándar | 99,5 % | Lun–Sáb 7:00–20:00 | 500m / 512Mi |
| Premium | 99,9 % | 24/7 | 1000m / 1Gi |

**Prioridades y SLA base:**

| Prioridad | Significado | Respuesta | Solución |
|---|---|---|---|
| P1 | Crítica: el sitio no funciona o se pierden ventas | 15 min | 4 h |
| P2 | Alta: una función importante falla | 1 h | 8 h |
| P3 | Media: falla menor con alternativa | 4 h | 24 h |
| P4 | Baja: consulta o mejora | 8 h | 72 h |

**Roles:** `agencia` (administrador y técnico: ve todo) y `cliente` (usuario de una PyME: ve solo lo suyo).

**Estados:** ticket `abierto → en_progreso → en_espera → resuelto → cerrado` · incidente `abierto → mitigado → cerrado` · servicio `operativo · degradado · caido` · solicitud de cambio `pendiente → aprobada → en_validacion → desplegada | rechazada` · texto de IA `borrador_ia → aprobado | descartado`.

## Tech stack

Cada herramienta de plataforma se instala cuando el diplomado cubre su módulo. El stack de producto (backend, frontend, base de datos) está fijo desde el módulo 1.

### Producto (el Hub)

| Capa | Tecnología | Notas |
|---|---|---|
| Backend | Python 3.12 + **FastAPI** | SQLAlchemy 2, Alembic (migraciones), Pydantic, pytest |
| Base de datos | **PostgreSQL 16** | Fechas en UTC (`timestamptz`) |
| Frontend | **React + Vite + TypeScript** | react-router-dom; CSS propio en blanco y negro, sin librerías de UI. Consola de agencia y portal del cliente con las mismas rutas y roles distintos |
| Contenedores | **Docker**, **docker compose** (desarrollo) | Imágenes multi-stage, usuario no root |
| Dependencias | `pip` + `requirements.txt` / `npm` | |

### Plataforma

| Capa | Herramienta | Módulo | Notas |
|---|---|---|---|
| Kubernetes | **k3s** | 2 | Nodo único en el PC A; trae Traefik como Ingress |
| Git, CI y registro | **Gitea + Gitea Actions** | 2–3 | Autoalojado; incluye registro de imágenes |
| GitOps | **Argo CD** | 2 | Fuente de verdad = repo Git; detecta drift; hace rollback |
| Platform Engineering | **Backstage** | 2 | Catálogo mínimo de clientes y servicios; se apaga si falta RAM |
| Secretos en código | **Gitleaks** | 3 | Bloquea commits con secretos |
| Vulnerabilidades | **Trivy** | 3 | Bloquea imágenes con CVE críticas |
| SBOM | **Syft** | 3 | Inventario de componentes de cada imagen |
| Firma | **Cosign / Sigstore** | 3 | Firma y `cosign verify` en el pipeline |
| Seguridad de Pods | **Pod Security Admission** | 3 | Nativo de Kubernetes, perfil `restricted` |
| IaC | **OpenTofu** (compatible con Terraform) | 4 | HCL genérico; binario final según el profesor |
| Bootstrap de SO | Ansible (opcional) | 4 | Solo para instalar k3s |
| Métricas y alertas | **Prometheus + Grafana + Alertmanager** | 4 | Alertmanager dispara el webhook que abre el incidente |
| Logs | **Loki** | 4 | Retención corta |
| Uptime | **Blackbox Exporter** | 4 | Sonda HTTP a cada sitio |
| Instrumentación | **OpenTelemetry** | 4 | Métricas custom (formularios recibidos/fallidos) |

### IA local

| Capa | Herramienta | Módulo | Notas |
|---|---|---|---|
| LLM | **Ollama** | 5 | Qwen2.5 7B-Instruct o Llama 3.1 8B (Q4, ≈ 5 GB VRAM); respaldo Qwen2.5 3B |
| RAG | **AnythingLLM** | 5 | Embeddings con `nomic-embed-text` servido desde Ollama |
| MLOps | **MLflow** (Docker Compose) | 5 | Versiones de prompt y modelo con sus evaluaciones |
| Multimodal | **Stability Matrix + ComfyUI** | 6 | SD 1.5 (SDXL Turbo solo si cabe en 6 GB); ilustración de la infografía |

Detalle y justificación de cada elección en [docs/tech-stack.md](docs/tech-stack.md).

## Hardware

| Equipo | Qué corre | Por qué |
|---|---|---|
| **PC A** (16 GB) · plataforma | k3s con el Hub, PostgreSQL, Gitea, Argo CD, Prometheus, Grafana, Loki, Alertmanager y los 3 sitios de clientes | Todo lo que debe estar siempre arriba vive en un nodo; la GPU no se usa |
| **PC B** (16 GB, GPU ≥ 6 GB) · IA | Ollama, AnythingLLM, MLflow, ComfyUI | 6 GB de VRAM no alcanzan para LLM e imágenes a la vez: se usan por turnos (Ollama con `keep_alive` corto) |
| Equipos de desarrollo | `docker compose` y runner de Gitea Actions (si tiene RAM) | Mantienen las compilaciones fuera del PC A |

El Hub (PC A) llama a Ollama y AnythingLLM (PC B) por la red local. Ambos PC necesitan IP fija en la red de la demo.

## Arquitectura

### Clúster

```
Clúster k3s (PC A)
├── namespace: hub                  → el Hub (FastAPI, React, PostgreSQL)
├── namespace: argocd               → Argo CD
├── namespace: gitea                → Gitea y registro de imágenes
├── namespace: monitoring           → Prometheus, Grafana, Alertmanager, Loki
├── namespace: cliente-restaurante  → sitio de La Sazón
├── namespace: cliente-ferreteria   → sitio de El Tornillo
└── namespace: cliente-consultorio  → sitio de Dental Popayán
```

Cada namespace de cliente incluye **ResourceQuota + LimitRange** (según el plan), **NetworkPolicy** (aislamiento entre clientes), **Pod Security Admission `restricted`** (sin root ni privilegios) e **Ingress** (`<cliente>.hub.local`).

**El Hub no toca Kubernetes directamente:** se comunica con Gitea (cambios), Argo CD (estado del despliegue) y Prometheus (métricas). Alertmanager avisa al Hub por webhook cuando algo falla.

### Flujo de despliegue

1. Push a Gitea → dispara Gitea Actions.
2. Pipeline: Gitleaks → build de imagen → Trivy → Syft (SBOM) → Cosign (firma) → push al registro → `cosign verify` → actualiza el tag en el repo `hub-gitops`.
3. Argo CD detecta el cambio y sincroniza el `Deployment` en el namespace del cliente; Pod Security Admission rechaza cualquier Pod que no cumpla `restricted`.
4. La readiness probe actúa como smoke test antes de recibir tráfico.
5. Blackbox Exporter monitorea el endpoint público de cada sitio.
6. Si falla → Alertmanager → webhook → el Hub abre un incidente P1 y arranca el SLA.
7. Revisión de logs (Loki) y cambios recientes → rollback con `git revert` en `hub-gitops`.
8. Argo CD reconcilia a la versión estable → las métricas confirman la recuperación → el Hub cierra el incidente y calcula el MTTR.
9. Ollama (vía AnythingLLM, en el PC B) redacta el resumen y el mensaje al cliente, siempre con aprobación humana.

### Repositorios

- **GitHub `ngcddev/CloudOps`**: monorepo de desarrollo (este).
- **Gitea `hub-gitops`**: repo que vigila Argo CD; se siembra desde `gitops/`. El Hub escribe ahí los cambios de versión y los rollback.

## Seguridad

Sin motores de políticas extra (se descartó Kyverno):

1. **Verificación de firma en el pipeline.** Antes de actualizar el tag en `hub-gitops`, Gitea Actions ejecuta `cosign verify`. Sin firma válida, no hay despliegue.
2. **Pod Security Admission `restricted`** en cada namespace de cliente: bloquea contenedores root, privilegiados o con capacidades peligrosas.
3. **ResourceQuota y LimitRange** por namespace según el plan.
4. **Nadie despliega a mano:** todo cambio entra por Gitea y Argo CD.
5. **Secretos fuera del código:** `.env` (ignorado) y `.env.example` con valores de desarrollo; `.gitignore` bloquea llaves, tokens y estados de OpenTofu.

Limitación conocida: la firma se verifica en el pipeline, no dentro del clúster. Queda como mejora futura (admission controller de verificación de imágenes).

## Sitios de cliente

Dos plantillas estándar de servicio; no se acepta "cualquier repositorio":

| Plantilla | Contenido | Clientes |
|---|---|---|
| **Landing estática** | HTML/CSS/JS (o Astro) servido por `nginx-unprivileged` | La Sazón, El Tornillo |
| **Landing + formulario** | Landing en Nginx + API mínima que recibe el formulario; Ingress `/` al frontend y `/api` al backend | Dental Popayán |

- Cliente nuevo = copiar una plantilla y cambiar nombre, dominio y plan.
- Todas las imágenes corren como usuario no root.
- `v1` = versión sana; `v2` = versión rota que responde HTTP 500 en `/` y en `/health`.
- Todas exponen `GET /health` → `{"status":"ok","version":"v1"}`.

## Qué audita el sistema por cliente

| Qué se audita | Fuente |
|---|---|
| ¿El sitio está arriba? | Blackbox Exporter → Prometheus |
| Latencia de respuesta | Métricas del Ingress (Traefik) |
| Errores 4xx/5xx | Logs de Nginx vía Loki |
| Formularios recibidos / fallidos | Métrica custom del backend con OpenTelemetry |
| Seguridad de la imagen desplegada | Reporte de Trivy y resultado de `cosign verify`, guardados como evidencia |
| Versión activa y quién la desplegó | Historial de Argo CD + commits de Git |
| Acciones de los usuarios | Bitácora de auditoría del Hub |

## Cómo trabajamos (SDD)

El proyecto usa **Spec-Driven Development**. Cada spec pasa por el mismo ciclo y se cierra con una demo:

1. **Constitución:** los [10 principios](constitution.md#los-10-principios) que ninguna spec puede romper.
2. **Spec (`spec.md`):** qué se construye y por qué, en lenguaje de negocio, con criterios de aceptación medibles. Sin tecnología.
3. **Plan (`plan.md`):** cómo se construye con el stack: modelo de datos, endpoints, manifiestos, pantallas.
4. **Tareas (`tasks.md`):** pasos ordenados de menos de un día, cada uno verificable en minutos. Se escribe al empezar la spec.
5. **Implementar:** la spec termina cuando sus criterios pasan en la demo.

Los 10 principios en una línea cada uno: el flujo empieza en el cliente · infraestructura propia · Git es la única puerta · seguridad antes de publicar · el Hub no toca Kubernetes · la IA propone, el humano decide · medición real · el cliente no ve jerga · módulo a módulo · simple y verificable.

Guía completa en [docs/sdd.md](docs/sdd.md).

## Especificaciones

**Acciona** indica quién ejecuta la spec. El detalle por rol está al inicio de cada `spec.md`.

| Spec | Nombre | Acciona | Módulo | Requerimientos | Depende de |
|---|---|---|---|---|---|
| [000](specs/000-modelo-de-servicio/spec.md) | Modelo de servicio | Industrial | 1–2 | Planes, P1–P4, SLA, KPI | — |
| [001](specs/001-clientes-y-planes/spec.md) | Clientes y planes | Sistemas · apoya Industrial | 1 | RF-01, RF-02 | 000 |
| [002](specs/002-plantillas-de-sitio/spec.md) | Plantillas de sitio y apps demo | Sistemas | 1 | RNF-01, RNF-02 | — |
| [003](specs/003-plataforma-k3s/spec.md) | Plataforma multi-cliente en k3s | Sistemas · apoya Industrial | 2 | RF-03, RNF-03 | 002 |
| [004](specs/004-mesa-de-servicio/spec.md) | Mesa de servicio: tickets y prioridad | Sistemas · apoya Industrial | 2 | RF-04, RF-05 | 000, 001 |
| [005](specs/005-cambios-gitops/spec.md) | Cambios por GitOps | Sistemas | 2 | RF-06, RF-07, RF-22, RNF-04 | 003, 004 |
| [006](specs/006-puerta-de-seguridad/spec.md) | Puerta de calidad y seguridad | Sistemas | 3 | RF-08, RF-09, RNF-05, RNF-06 | 005 |
| [007](specs/007-roles-y-auditoria/spec.md) | Acceso por roles y auditoría | Sistemas | 3 | RF-01 (roles), RF-10 | 001 |
| [008](specs/008-monitoreo-e-incidentes/spec.md) | Monitoreo e incidente automático | Sistemas · apoya Industrial | 4 | RF-11, RF-12, RF-13, RNF-07 | 000, 003, 004 |
| [009](specs/009-rollback/spec.md) | Recuperación por rollback | Sistemas | 4 | RF-14 | 005, 008 |
| [010](specs/010-dashboards/spec.md) | Dashboards y métricas del servicio | Sistemas · apoya Industrial | 4 | RF-15, RF-16, RF-17, RNF-10 | 008, 009 |
| [011](specs/011-infraestructura-como-codigo/spec.md) | Infraestructura como código | Sistemas | 4 | RNF-08 | 003 |
| [012](specs/012-asistente-ia/spec.md) | Asistente de incidentes con IA local | Sistemas · apoya Industrial | 5 | RF-18, RF-19, RNF-09 | 008 |
| [013](specs/013-reportes/spec.md) | Reportes operativo y ejecutivo | Industrial + Sistemas | 5 | RF-20 | 010 |
| [014](specs/014-infografia/spec.md) | Infografía mensual | Sistemas · apoya Industrial | 6 | RF-21, RF-23 | 010, 013 |
| [015](specs/015-demo-integrada/spec.md) | Demo integrada | Todo el equipo | 7 | RNF-11 | todas |

**Orden de arranque:** 000, 001 y 002 empiezan ya. Pueden adelantarse (solo producto) la 004 y la parte de backend/frontend de 007, 008 (incidentes manuales), 010 y 013. Todo lo que instala herramientas de plataforma espera su módulo.

Requerimientos completos (RF/RNF con prioridad MoSCoW y trazabilidad): [docs/requerimientos.md](docs/requerimientos.md).

## Calendario

120 horas en 9 semanas. Tres carriles en paralelo: **plataforma** (atada al módulo), **producto** (puede adelantarse) y **servicio** (industrial, se diseña antes de que el código lo necesite).

| Módulo | Fechas | Incremento obligatorio | Specs |
|---|---|---|---|
| 1 · Cloud Native, Linux, Git, contenedores | 28 sep – 1 oct | Todo corre en contenedores con un solo comando | 000, 001, 002 |
| 2 · Kubernetes, GitOps, Platform Engineering | 2 – 13 oct | Un cambio en Git despliega la app sin tocar el clúster; un revert la devuelve | 003, 004, 005 |
| 3 · DevSecOps y cadena de suministro | 16 – 24 oct | Un cambio inseguro no llega a producción y el Hub muestra por qué | 006, 007 |
| 4 · IaC, observabilidad, SRE | 24 oct – 3 nov | El caso del restaurante de punta a punta, sin IA | 008, 009, 010, 011 |
| 5 · MLOps, LLMOps, IA local | 3 – 12 nov | El Hub redacta el resumen con IA local y un humano lo aprueba | 012, 013 |
| 6 · IA local multimodal | 13 – 20 nov | Infografía mensual de cada cliente | 014 |
| 7 · Integrador | 24 – 30 nov | Demo final ensayada; ninguna funcionalidad nueva | 015 |

**Hitos:** 2 oct matriz P1–P4 cerrada · 13 oct GitOps funcionando · 24 oct puerta de seguridad · 31 oct caso del restaurante sin IA · **3 nov sustentación del módulo 4** · 12 nov asistente IA y reportes · 20 nov infografía · 21–23 nov colchón · **30 nov sustentación final**.

Detalle en [docs/calendario.md](docs/calendario.md).

## Alcance de la demo

Meta para la sustentación final (30 nov). Ningún punto está hecho todavía.

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

La demo final recorre estos puntos en menos de 15 minutos, arrancando siempre desde datos semilla ([spec 015](specs/015-demo-integrada/spec.md)).

## Equipo y roles

| Integrante | Rol | Aporta | Acciona en las specs |
|---|---|---|---|
| Sistemas 1 | Cloud / Platform | Kubernetes, GitOps, manifiestos, infraestructura y despliegue | 002, 003, 005, 009, 011 |
| Sistemas 2 | Backend | API, usuarios, roles, clientes, tickets, SLA y base de datos | 001, 004–010, 012–014 |
| Sistemas 3 | DevSecOps / SRE | Pipelines, seguridad, observabilidad, alertas, logs y recuperación | 006, 008 |
| Sistemas 4 | Frontend / Producto | Portal de cliente, consola de agencia, UX y dashboards | 001, 002, 004, 007, 010, 013, 014 |
| Industrial | Operación de servicios | Procesos, prioridades, SLA, KPI, capacidad, costos y mejora continua | 000, 013 · apoya en 001, 003, 004, 008, 010, 012, 014 |

Todo el equipo acciona la 015 (demo integrada).

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

## Estructura del repositorio

**Lo que existe hoy:**

```
cloudops/
├── README.md
├── constitution.md                  # principios, stack por módulo y nombres canónicos
├── CLAUDE.md                        # reglas para trabajar con asistentes de código
├── .github/pull_request_template.md # revisión de cada PR contra la constitución
├── docs/
│   ├── requerimientos.md            # RF/RNF, MoSCoW y trazabilidad con la demo
│   ├── calendario.md                # módulos, hitos, dependencias y riesgos
│   ├── tech-stack.md                # stack, hardware y flujo de despliegue
│   ├── sdd.md                       # cómo trabajamos y plantillas recomendadas
│   └── glosario.md                  # términos técnicos → lenguaje del cliente
└── specs/
    ├── README.md                    # mapa de specs
    ├── _plantilla/                  # spec.md · plan.md · tasks.md para specs nuevas
    └── 000-… a 015-…/               # spec.md + plan.md (tasks.md en 000, 001 y 002)
```

**Lo que se agregará**, cada carpeta cuando empiece su spec:

| Carpeta | Contenido | Spec |
|---|---|---|
| `backend/`, `frontend/`, `docker-compose.yml` | Hub: API FastAPI y consola/portal en React | 001 |
| `seed/` | Datos semilla (planes, SLA, clientes, usuarios) | 000, 001, 015 |
| `apps/` | Plantillas y sitios demo de clientes | 002 |
| `gitops/` | Manifiestos Kubernetes → repo `hub-gitops` en Gitea | 003 |
| `pipelines/` | Gitea Actions | 006 |
| `observability/` | Prometheus, Alertmanager, Grafana, Loki | 008 |
| `infra/` | OpenTofu y Ansible | 011 |
| `ai/` | Prompts, evaluación, Ollama, MLflow, ComfyUI | 012, 014 |
| `demo/` | Guion y reinicio de la demo | 015 |

## Convenciones

- **Idioma:** interfaz, documentación y comentarios en español; nombres de código en inglés (`snake_case` en Python y SQL, `camelCase` en TypeScript, `PascalCase` en componentes React).
- **Diseño:** blanco y negro; el estado se comunica con texto e íconos, no con color.
- **Datos:** fechas en UTC en la base, mostradas en hora de Colombia (America/Bogota); ids enteros autoincrementales; todo dato de demo es ficticio.
- **Git:** `main` protegida (se entra por PR). Ramas `feat/<spec>-t<NN>-<slug>`, `fix/<spec>-<slug>`, `docs/<slug>`. Commits con Conventional Commits en español: `feat(001): …`, `docs(004): …`. Un commit = un cambio lógico.
- **Secretos:** nunca en el código ni en el repo; `.env` ignorado y `.env.example` con valores de desarrollo.
- **Editor:** `.editorconfig` y `.gitattributes` fuerzan UTF-8 y finales de línea LF.

## Cómo contribuir

1. Leer la [constitución](constitution.md) y la spec en curso (`spec.md`, `plan.md`, `tasks.md`).
2. Tomar la siguiente tarea libre de `tasks.md` y poner tu nombre al lado.
3. Crear la rama `feat/<spec>-t<NN>-<slug>` desde `main`.
4. Commits con Conventional Commits; marcar la casilla de la tarea en `tasks.md` en el mismo PR.
5. Abrir un PR con la plantilla; otra persona lo revisa contra la spec y la constitución.

Para abrir una spec nueva, copiar [`specs/_plantilla/`](specs/_plantilla/spec.md).

**Plantillas recomendadas para desarrollar más rápido:**

| Qué | Plantilla | Cuándo |
|---|---|---|
| Spec nueva | `specs/_plantilla/` | Siempre |
| Hub | Esqueleto propio del [plan de la spec 001](specs/001-clientes-y-planes/plan.md) (`full-stack-fastapi-template` solo como referencia: usa SQLModel y Chakra UI, que no encajan con la constitución) | Módulo 1 |
| Sitio de cliente | Repos plantilla en Gitea (`cliente-landing`, `cliente-landing-form`) marcados como *Template repository* | Módulo 2 |
| Cliente nuevo de punta a punta | *Software Template* de Backstage que crea repo, namespace y manifiestos con nombre, dominio y plan | Módulos 2–4 |

## Decisiones pendientes

| Decisión | Quién decide | Spec | Fecha límite |
|---|---|---|---|
| Tiempos SLA por plan y matriz P1–P4 definitiva | Industrial + equipo | 000 | 2 oct |
| Precio y horas incluidas por plan | Industrial | 000 | 2 oct |
| OpenTofu o Terraform | Profesor | 011 | 24 oct |
| Qué se presenta en la sustentación del 3 nov | Equipo | 015 | 27 oct |
| Qwen2.5 7B o Llama 3.1 8B | Prueba en PC B | 012 | 3 nov |
| SD 1.5 o SDXL Turbo | Prueba en PC B | 014 | 13 nov |

## Riesgos

| Riesgo | Respuesta |
|---|---|
| PC A justo de RAM con todo el clúster | Límites de memoria en cada componente, retención corta en Prometheus y Loki, runner de Gitea Actions fuera del PC A |
| Backstage consume varios GB | Catálogo mínimo; se apaga si falta RAM (la consola del Hub cumple el rol) |
| Solo 6 GB de VRAM | LLM y ComfyUI por turnos; resúmenes ya aprobados en los datos semilla por si la IA falla |
| Los dos PC deben verse en la red | IP fija y prueba en la red del salón antes del 30 nov |
| El Hub se construye desconectado de la infraestructura | Desde el módulo 2, cada pantalla nueva se conecta a Gitea, Argo CD o Prometheus antes de pulirse |
| Sustentación del 3 nov al cierre del módulo 4 | Caso del restaurante sin IA listo el 31 oct |
| La firma se verifica en el pipeline, no en el clúster | Nadie despliega a mano; verificación en clúster como mejora futura |
| Sobre-diseñar autenticación | Dos roles con usuarios sembrados bastan para la demo |

## Fuera de alcance

CDN, serverless, escala global, dominios reales, pagos y facturación, video y 3D, multi-agencia.

## Conclusión

La propuesta no compite con Vercel en despliegue global. Usa capacidades cloud-native (contenedores, Kubernetes, GitOps, seguridad, observabilidad y recuperación) para profesionalizar la operación y la relación de servicio entre agencias digitales y PyMEs: una página web deja de ser una entrega puntual y se convierte en un servicio administrado, medible y mejorable.

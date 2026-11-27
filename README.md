# CloudOps Client Hub

> Un centro de operación de servicios digitales para agencias que administran múltiples clientes.

CloudOps Client Hub **no es otro Vercel**. Ayuda a una agencia digital a gestionar el servicio completo que presta a sus clientes: solicitudes, cambios, despliegues, monitoreo, incidentes, recuperación, SLA, calidad y reportes. El despliegue es una capacidad interna, no el producto.

Proyecto integrador del diplomado **CloudForge AI 5.0** (Unicomfacauca), 28 sep – 30 nov 2026. Equipo de 5: 4 ingenieros de sistemas y 1 ingeniero industrial.

**Documentos de referencia:** [constitución](constitution/README.md) ([misión](constitution/mission.md) · [principios](constitution/principles.md) · [roadmap](constitution/roadmap.md) · [tech stack](constitution/tech-stack.md) · [convenciones](constitution/conventions.md) · [nombres canónicos](constitution/canonical-names.md)) · [cómo trabajamos (SDD)](docs/sdd.md) · [mapa de specs](specs/README.md) · [requerimientos](docs/requerimientos.md) · [glosario](docs/glosario.md) · [documento del diplomado](docs/diplomado-cloudforge-ai-5.0.md)

## Tabla de contenidos

- [Estado actual](#estado-actual)
- [Cómo levantarlo](#cómo-levantarlo)
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
- [Decisiones](#decisiones)
- [Riesgos](#riesgos)
- [Fuera de alcance](#fuera-de-alcance)
- [Conclusión](#conclusión)

## Estado actual
El estado verificado del proyecto **no se escribe a mano en este README**: las cifras salen de la monografía final y de los comandos que las producen (tabla de comandos en [CLAUDE.md](CLAUDE.md#comandos)).

- Estado por spec y tareas abiertas: [mapa de specs](specs/README.md).

## Cómo levantarlo

Hay dos formas. La primera es la rápida, para ver y desarrollar el Hub; la segunda instala la plataforma completa.

| Forma | Qué incluye | Dónde queda |
|---|---|---|
| Desarrollo con Docker Compose | API, consola y portal, PostgreSQL y los tres sitios; la IA es opcional | http://localhost:5173 |
| Plataforma completa en k3d | El Hub y los sitios en Kubernetes, con Argo CD, Gitea, puerta de seguridad, observabilidad, MLflow y Backstage | http://hub.local |

### Desarrollo con Docker Compose

Requisitos: Docker (Docker Desktop en Windows o Docker Engine en Linux) y Git. Para el asistente de IA, [Ollama](https://ollama.com) con `qwen2.5:7b-instruct` y `nomic-embed-text` (sin Ollama el Hub funciona y el asistente avisa que no está disponible).

```bash
git clone https://github.com/ngcddev/CloudOps.git
cd CloudOps
cp .env.example .env          # cambiar JWT_SECRET por un valor propio (la API no arranca con el de ejemplo)
docker compose up --build
```

Para conectar la IA con Docker Desktop, en `.env` quita el comentario de `OLLAMA_URL` y usa `http://host.docker.internal:11434`.

- Consola de la agencia y portal del cliente: http://localhost:5173 · API: http://localhost:8000 (`/health`).
- Usuarios sembrados: `sofia@forjadigital.test` (técnica de la agencia) y `contacto@lasazon.test` (cliente), con la contraseña `SEED_USER_PASSWORD` de tu `.env`.
- Sitios de los clientes: http://localhost:8081 (restaurante), :8082 (ferretería) y :8083 (consultorio).
- Pruebas del backend: `docker compose exec api pytest`.

### Plataforma completa en k3d

Para Windows con Docker Desktop, en Git Bash. Necesita Git, Python 3 y Ollama, y los puertos 80 y 443 libres.

```bash
git clone https://github.com/ngcddev/CloudOps.git
cd CloudOps
bash infra/instalar.sh --comprobar   # solo revisa los requisitos
bash infra/instalar.sh               # instala hasta http://hub.local
```

Las claves que no definas se generan solas. El instalador todavía **no se ha validado de principio a fin en un equipo limpio**.

Requisitos, claves, el procedimiento paso a paso y la solución de fallas están en la **[guía de instalación](docs/instalacion.md)**. Los manifiestos y su operación se describen en [gitops/README.md](gitops/README.md).

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
| 8. Comunicación | La IA local redacta el resumen y el mensaje; un humano los aprueba | Ollama (IA local en el equipo) |
| 9. Mejora | El caso queda en el reporte mensual | Hub (reportes) |

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

**Estados:** ticket `abierto → en_progreso → en_espera → resuelto → cerrado` · incidente `abierto → mitigado → cerrado` · servicio `operativo · degradado · caido` · solicitud de cambio `pendiente → aprobada → en_validacion → desplegada | fallida`, o `pendiente → rechazada` · texto de IA `borrador_ia → aprobado | descartado`.

## Tech stack

Cada herramienta de plataforma se instala cuando el diplomado cubre su módulo. El stack de producto (backend, frontend, base de datos) está fijo desde el módulo 1.

### Producto (el Hub)

| Capa | Tecnología | Notas |
|---|---|---|
| Backend | Python 3.12 + **FastAPI** | SQLAlchemy 2, Alembic (migraciones), Pydantic, pytest |
| Base de datos | **PostgreSQL 16** | Fechas en UTC (`timestamptz`) |
| Frontend | **React + Vite + TypeScript** | react-router-dom; CSS propio (monocromo con un acento verde, tema claro y oscuro), sin librerías de UI. Consola de agencia y portal del cliente con las mismas rutas y roles distintos |
| Contenedores | **Docker**, **docker compose** (desarrollo) | Imágenes multi-stage, usuario no root |
| Dependencias | `pip` + `requirements.txt` / `npm` | |

### Plataforma

| Capa | Herramienta | Módulo | Notas |
|---|---|---|---|
| Kubernetes | **k3s** (en k3d para el laboratorio) | 2 | Un nodo; trae Traefik como Ingress |
| Git, CI y registro | **Gitea + Gitea Actions** | 2–3 | Autoalojado; incluye registro de imágenes |
| GitOps | **Argo CD** | 2 | Fuente de verdad = repo Git; detecta drift; hace rollback |
| Platform Engineering | **Backstage** | 2 | Catálogo mínimo de clientes y servicios; se apaga si falta RAM |
| CI del Hub | **GitHub Actions / Gitea Actions** (`.github/workflows/ci.yml`) | 3 | ruff, pytest, `tsc`/`vite build`, validación de observabilidad, trazas y respaldo, y para la imagen de producción: Gitleaks, humo, Trivy y Syft |
| Secretos en código | **Gitleaks** | 3 | Bloquea commits con secretos |
| Vulnerabilidades | **Trivy** | 3 | Bloquea imágenes con CVE críticas |
| SBOM | **Syft** | 3 | Inventario de componentes de cada imagen |
| Firma y procedencia | **Cosign / Sigstore** | 3 | Firma, `cosign verify` y atestación de procedencia SLSA v1 (commit, repositorio y corrida) verificada contra el commit de la versión |
| Seguridad de Pods | **Pod Security Admission** | 3 | Nativo de Kubernetes, perfil `restricted` |
| IaC | **OpenTofu** (compatible con Terraform) | 4 | Versiones fijadas y ejecutadas en contenedor (`infra/tofu.sh`) |
| Métricas y alertas | **Prometheus + Grafana + Alertmanager** | 4 | Alertmanager dispara el webhook que abre el incidente |
| Logs | **Loki** | 4 | Retención corta |
| Trazas | **Tempo** | 4 | Recibe las trazas OTLP del Hub (peticiones y etapas del asistente, sin el texto de las preguntas); se ven en Grafana → Explore → Tempo |
| Uptime | **Blackbox Exporter** | 4 | Sonda HTTP a cada sitio |
| Instrumentación | **OpenTelemetry** | 4 | Métricas custom de los sitios (formularios) y trazas del Hub (FastAPI y etapas del asistente) |

### IA local

| Capa | Herramienta | Módulo | Notas |
|---|---|---|---|
| LLM | **Ollama** | 5 | Qwen2.5 7B-Instruct (Q4) en el Hub; Qwen2.5 3B solo para comparar (licencia de investigación) |
| RAG | **RAG propio** en el Hub: `nomic-embed-text` (Ollama) + índice en PostgreSQL (`kb_documents`, `kb_chunks`) | 5 | Similitud coseno en Python, sin extensiones; cae a búsqueda léxica si Ollama no responde. Reemplaza a AnythingLLM |
| MLOps | **MLflow** (namespace `mlops` del clúster; `ai/servidor-mlflow/` para desarrollo) | 5 | Experimentos, Model Registry (`compuerta-asistente` con alias `production`) y evaluaciones del asistente |
| Compuerta del asistente | **Clasificador Naive Bayes** (Python puro, JSON de ~40 KB) | 5 | Decide si la pregunta trata del Hub antes de despertar al LLM; se entrena con `ai/classifier/train.py` y se registra en MLflow |
| Multimodal | **Voz**: faster-whisper `small` (voz a texto) y Piper (texto a voz), en CPU | 6 | Servicio aparte (`voz/`); el audio no se guarda. Generación de imagen (ComfyUI) fuera de alcance por cómputo |

Detalle y justificación de cada elección en [constitution/tech-stack.md](constitution/tech-stack.md).

## Hardware
| Equipo | Qué corre |
|---|---|
| Laptop del equipo (RTX 4060 de 8 GB) | Docker Desktop con el clúster k3d (Hub, Gitea, Argo CD, observabilidad, MLflow, Backstage y los sitios de los clientes) y Ollama con los modelos en la GPU |

El Hub llama a Ollama en el equipo anfitrión; si no responde, el asistente avisa y el resto del Hub sigue funcionando. El segundo equipo con GPU que se había previsto (PC B) se descartó el 15 nov 2026; un despliegue en la nube está pendiente.

## Arquitectura

### Clúster

```
Clúster k3s (k3d, un nodo)
├── namespace: hub                  → el Hub (FastAPI, React, PostgreSQL), voz y Backstage
├── namespace: mlops                → MLflow
├── namespace: argocd               → Argo CD
├── namespace: gitea                → Gitea y registro de imágenes
├── namespace: monitoring           → Prometheus, Grafana, Alertmanager, Loki, Tempo, Alloy, Blackbox
├── namespace: cliente-restaurante  → sitio de La Sazón
├── namespace: cliente-ferreteria   → sitio de El Tornillo
├── namespace: cliente-consultorio  → sitio de Dental Popayán
└── namespace: cliente-ferreteria-staging → staging de El Tornillo
```

Cada namespace de cliente incluye **ResourceQuota + LimitRange** (según el plan), **NetworkPolicy** (aislamiento entre clientes), **Pod Security Admission `restricted`** (sin root ni privilegios) e **Ingress** (`<cliente>.hub.local`).

**El Hub no toca Kubernetes directamente:** se comunica con Gitea (cambios), Argo CD (estado del despliegue) y Prometheus (métricas). Alertmanager avisa al Hub por webhook cuando algo falla.

### Flujo de despliegue

1. Push a Gitea → dispara Gitea Actions.
2. Puerta de seguridad: Gitleaks → pruebas y build de la imagen → Trivy → Syft (SBOM) → subir, firmar y atestiguar la procedencia (Cosign) → `cosign verify`; el Hub registra la corrida. Al aprobar el cambio, el Hub actualiza el tag en `hub-gitops`.
3. Argo CD detecta el cambio y sincroniza el `Deployment` en el namespace del cliente; Pod Security Admission rechaza cualquier Pod que no cumpla `restricted`.
4. La readiness probe actúa como smoke test antes de recibir tráfico.
5. Blackbox Exporter monitorea el endpoint público de cada sitio.
6. Si falla → Alertmanager → webhook → el Hub abre un incidente P1 y arranca el SLA.
7. Revisión de logs (Loki) y cambios recientes → rollback con `git revert` en `hub-gitops`.
8. Argo CD reconcilia a la versión estable → las métricas confirman la recuperación → el Hub cierra el incidente y calcula el MTTR.
9. Ollama (local, en el equipo anfitrión) redacta el resumen y el mensaje al cliente, siempre con aprobación humana.

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

1. **Constitución:** los [10 principios](constitution/principles.md#los-10-principios) que ninguna spec puede romper.
2. **Spec (`spec.md`):** qué se construye y por qué, en lenguaje de negocio, con criterios de aceptación medibles. Sin tecnología.
3. **Plan (`plan.md`):** cómo se construye con el stack: modelo de datos, endpoints, manifiestos, pantallas.
4. **Tareas (`tasks.md`):** pasos ordenados de menos de un día, cada uno verificable en minutos. Se escribe al empezar la spec.
5. **Implementar:** la spec termina cuando sus criterios pasan en la demo.

Los 10 principios en una línea cada uno: el flujo empieza en el cliente · infraestructura propia · Git es la única puerta · seguridad antes de publicar · el Hub no toca Kubernetes · la IA propone, el humano decide · medición real · el cliente no ve jerga · módulo a módulo · simple y verificable.

Guía completa en [docs/sdd.md](docs/sdd.md).

## Especificaciones
El proyecto se construyó por especificaciones (SDD): 24 specs, de la 000 a la 023. La tabla con quién acciona cada una, sus dependencias y su estado está en un solo lugar: el [mapa de specs](specs/README.md). Para abrir una spec nueva se copia [`specs/_plantilla/`](specs/_plantilla/spec.md).

Los requerimientos originales (RF y RNF con prioridad MoSCoW) están en [docs/requerimientos.md](docs/requerimientos.md); los requerimientos vigentes con su verificación van en el informe final de la entrega.

## Calendario

120 horas en 9 semanas. Tres carriles en paralelo: **plataforma** (atada al módulo), **producto** (puede adelantarse) y **servicio** (industrial, se diseña antes de que el código lo necesite).

| Módulo | Fechas | Incremento obligatorio | Specs |
|---|---|---|---|
| 1 · Cloud Native, Linux, Git, contenedores | 28 sep – 1 oct | Todo corre en contenedores con un solo comando | 000, 001, 002 |
| 2 · Kubernetes, GitOps, Platform Engineering | 2 – 13 oct | Un cambio en Git despliega la app sin tocar el clúster; un revert la devuelve | 003, 004, 005 |
| 3 · DevSecOps y cadena de suministro | 16 – 24 oct | Un cambio inseguro no llega a producción y el Hub muestra por qué | 006, 007 |
| 4 · IaC, observabilidad, SRE | 24 oct – 3 nov | El caso del restaurante de punta a punta, sin IA | 008, 009, 010, 011 |
| 5 · MLOps, LLMOps, IA local | 3 – 12 nov | El Hub redacta el resumen con IA local y un humano lo aprueba | 012, 013 |
| 6 · IA local multimodal | 13 – 20 nov | Voz del asistente (la infografía con imagen quedó pospuesta) | 021 |
| 7 · Integrador | 24 – 30 nov | Demo final ensayada; ninguna funcionalidad nueva | 015 |

**Hitos:** 2 oct matriz P1–P4 cerrada · 13 oct GitOps funcionando · 24 oct puerta de seguridad · 31 oct caso del restaurante sin IA · **3 nov sustentación del módulo 4** · 12 nov asistente IA y reportes · 20 nov infografía · 21–23 nov colchón · **30 nov sustentación final**.

Detalle en [constitution/roadmap.md](constitution/roadmap.md).

## Alcance de la demo
Meta para la sustentación final (30 nov). Cada punto tiene su verificación en la monografía final y en las pruebas de `gitops/pruebas/`:

| Punto | Specs | Verificación |
|---|---|---|
| Registrar una agencia y tres clientes ficticios, con un proyecto o servicio cada uno | [001](specs/001-clientes-y-planes/spec.md) | Recorrido de la interfaz (E01) |
| Desplegar aplicaciones demo con contenedores y Kubernetes | [002](specs/002-plantillas-de-sitio/spec.md), [003](specs/003-plataforma-k3s/spec.md) | A14–A16, C01, C17 |
| Validación automática antes de publicar | [006](specs/006-puerta-de-seguridad/spec.md) | B06, C23 |
| Tablero técnico para la agencia y uno simplificado para el cliente | [010](specs/010-dashboards/spec.md) | C24 (pasos 1–3), E01 |
| Simular una falla controlada, detectarla y abrir el incidente | [008](specs/008-monitoreo-e-incidentes/spec.md) | C26, C28 |
| Clasificar prioridad, asignar responsable y medir el SLA | [000](specs/000-modelo-de-servicio/spec.md), [004](specs/004-mesa-de-servicio/spec.md) | Pruebas del backend (B02) |
| Recuperar el servicio mediante rollback | [009](specs/009-rollback/spec.md) | C25 |
| Reporte operativo y ejecutivo | [013](specs/013-reportes/spec.md) | E01 (pantallas de reportes) |
| Asistente local que resume el incidente, con verificación humana | [012](specs/012-asistente-ia/spec.md) | D02–D05 |
| Componente multimodal | [021](specs/021-voz-del-asistente/spec.md) | D11, D12 (voz) |

La demo arranca desde datos semilla; `bash demo/dejar-demo-lista.sh` deja el clúster listo ([spec 015](specs/015-demo-integrada/spec.md)).

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
```
cloudops/
├── README.md · CLAUDE.md · CONTRIBUTING.md · LICENSE · NOTICE
├── constitution/       # misión, principios, roadmap, stack, convenciones y nombres canónicos
├── docs/               # requerimientos, glosario, guía SDD, KPI, prioridades, proceso, modelos, amenazas
│   └── historico/      # bitácora, auditorías y revisiones fechadas (no describen el estado actual)
├── specs/              # mapa, plantilla y specs 000 a 023
├── backend/            # API FastAPI (app/, alembic/, tests/)
├── frontend/           # React + Vite + TS (consola de agencia y portal del cliente)
├── apps/               # sitios demo (restaurante, ferreteria, consultorio, colegio) y plantillas
├── gitops/             # manifiestos Kubernetes: hub, clients, platform, charts, staging, pruebas
├── pipelines/          # puerta de seguridad (Gitea Actions) y runner
├── observability/      # Prometheus, Alertmanager, Grafana, Loki, Tempo, Alloy, Blackbox
├── infra/              # OpenTofu y scripts de cliente nuevo
├── ai/                 # compuerta de ML, evaluación del asistente, tutor y registro en MLflow
├── voz/                # servicio de voz (faster-whisper y Piper)
├── runbooks/           # procedimientos de operación
├── demo/               # reinicio y preparación de la demo
├── seed/               # datos semilla en JSON
├── .github/            # CI y plantilla de PR
└── docker-compose.yml  # entorno de desarrollo
```

## Convenciones

- **Idioma:** interfaz, documentación y comentarios en español; nombres de código en inglés (`snake_case` en Python y SQL, `camelCase` en TypeScript, `PascalCase` en componentes React).
- **Diseño:** sobrio entre Vercel y GitHub: monocromo con un solo acento verde, tema claro y oscuro; el estado se comunica con texto e íconos, nunca solo con color.
- **Datos:** fechas en UTC en la base, mostradas en hora de Colombia (America/Bogota); ids enteros autoincrementales; todo dato de demo es ficticio.
- **Git:** la rama de integración es `dev` (se entra por PR); `main` recibe lo probado. Ramas `feat/<spec>-t<NN>-<slug>`, `fix/<spec>-<slug>`, `docs/<slug>`. Commits con Conventional Commits en español: `feat(001): …`, `docs(004): …`. Un commit = un cambio lógico.
- **Secretos:** nunca en el código ni en el repo; `.env` ignorado y `.env.example` con valores de desarrollo.
- **Editor:** `.editorconfig` y `.gitattributes` fuerzan UTF-8 y finales de línea LF.

## Cómo contribuir
Ver [CONTRIBUTING.md](CONTRIBUTING.md): ramas desde `dev`, Conventional Commits en español, una tarea de `tasks.md` por PR y las pruebas que hay que correr antes de abrirlo.

**Plantillas para desarrollar más rápido:**

| Qué | Plantilla |
|---|---|
| Spec nueva | `specs/_plantilla/` |
| Sitio de cliente | Plantillas de `apps/templates/` (landing estática y landing con formulario) |
| Registrar un sitio en el catálogo | *Software Template* «Sitio de cliente» de Backstage (registra el componente en el catálogo; el alta del sitio la hace el Hub por GitOps) |

## Decisiones
Las decisiones que estaban abiertas ya se tomaron: OpenTofu (compatible con Terraform) para la IaC; Qwen2.5 7B-Instruct como modelo del Hub; la voz como componente multimodal en lugar de la generación de imágenes; y un solo equipo con GPU en lugar de dos. El detalle con su contexto y evidencia va en las decisiones de arquitectura (ADR) del informe final y en [constitution/tech-stack.md](constitution/tech-stack.md).

## Riesgos

| Riesgo | Respuesta |
|---|---|
| Un solo equipo con todo el clúster | Límites de memoria en cada componente, retención corta en Prometheus y Loki, runner de Gitea Actions fuera del PC A |
| Backstage consume varios GB | Catálogo mínimo; se apaga si falta RAM (la consola del Hub cumple el rol) |
| La GPU de 8 GB la comparten el LLM y los embeddings | Modelo de 7B cuantizado; si la IA no responde, el asistente avisa y el resto del Hub sigue (degradación probada) |
| Un `apply` de OpenTofu con el inventario completo reescribe a los clientes existentes | Probar con un inventario temporal; hallazgo H-IAC-01 del paquete de evidencias |
| El Hub se construye desconectado de la infraestructura | Desde el módulo 2, cada pantalla nueva se conecta a Gitea, Argo CD o Prometheus antes de pulirse |
| Sustentación del 3 nov al cierre del módulo 4 | Caso del restaurante sin IA listo el 31 oct |
| La firma se verifica en el pipeline, no en el clúster | Nadie despliega a mano; verificación en clúster como mejora futura |
| Sobre-diseñar autenticación | Dos roles con usuarios sembrados bastan para la demo |

## Fuera de alcance

CDN, serverless, escala global, dominios reales, pagos y facturación, generación de imagen, video y 3D, multi-agencia.

## Conclusión

La propuesta no compite con Vercel en despliegue global. Usa capacidades cloud-native (contenedores, Kubernetes, GitOps, seguridad, observabilidad y recuperación) para profesionalizar la operación y la relación de servicio entre agencias digitales y PyMEs: una página web deja de ser una entrega puntual y se convierte en un servicio administrado, medible y mejorable.

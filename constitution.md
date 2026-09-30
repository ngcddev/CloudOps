# Constitución — CloudOps Client Hub

> Este archivo es la ley del proyecto. Cada spec, cada plan y cada tarea se revisa contra él.
> Si un plan rompe un principio, **se corrige el plan, no el principio**.
> Cambiar este archivo requiere acuerdo de todo el equipo y un commit `docs(constitution): …` propio.
> Cómo se aplica: [docs/sdd.md](docs/sdd.md) · Stack detallado: [docs/tech-stack.md](docs/tech-stack.md) · Specs: [specs/README.md](specs/README.md).

## Qué construimos (en 5 líneas)

**CloudOps Client Hub** es un centro de operación de servicios digitales para agencias web que atienden a varias PyMEs.
Gestiona clientes, planes, solicitudes, cambios, despliegues, monitoreo, incidentes, recuperación, SLA y reportes.
**No es otro Vercel**: el despliegue es una capacidad interna, no el producto.
El producto responde: *"Tengo varios clientes, ¿cómo organizo su soporte, detecto problemas, cumplo tiempos y explico el valor del servicio?"*
Es el proyecto integrador del diplomado CloudForge AI (28 sep – 30 nov 2026).

## Los 10 principios

1. **El flujo empieza en el cliente.** cliente → proyecto → servicio → acuerdo (plan + SLA). El despliegue es una capacidad interna, no el producto.
2. **Infraestructura propia.** La demo no depende de servicios de terceros, y ningún dato de clientes sale del laboratorio.
3. **Git es la única puerta.** Todo cambio entra por Gitea → Gitea Actions → Argo CD. Nadie despliega a mano.
4. **Seguridad antes de publicar.** Ninguna imagen se despliega sin escanear, firmar y verificar; ningún contenedor de cliente corre como root.
5. **El Hub no toca Kubernetes directamente.** Habla solo con Gitea, Argo CD y Prometheus.
6. **La IA propone, el humano decide.** Todo texto de IA es un borrador que alguien aprueba. El flujo completo funciona aunque la IA esté apagada.
7. **Medición real.** SLA, MTTR y disponibilidad se calculan con horas y métricas reales, nunca simuladas.
8. **El cliente no ve jerga técnica.** Todo lo que llega al portal del cliente está en lenguaje de negocio (ver [docs/glosario.md](docs/glosario.md)).
9. **Módulo a módulo.** Una herramienta de plataforma entra solo cuando el diplomado ya la cubrió. El carril de producto (backend, frontend, base de datos, procesos) sí puede adelantarse.
10. **Simple y verificable.** Diseño en blanco y negro, dos roles (agencia y cliente) y cada spec cierra con una demo reproducible desde datos semilla.

### Reglas derivadas

- **Regla de desacople:** el producto nunca depende de la plataforma para funcionar. Ejemplo: el backend registra incidentes manuales desde la semana 1; en el módulo 4 empiezan a llegar solos desde Alertmanager.
- **Regla de oro:** cada módulo termina con una demo de 3 a 5 minutos que conecta lo nuevo del módulo con el producto. Si la conexión no se ve en pantalla, el incremento no cuenta.
- **Regla de orden:** una spec se implementa cuando las specs de las que depende cumplen sus criterios de aceptación (o exponen ya el contrato que se necesita).

## Stack por módulo

| Módulo | Fechas | Herramientas que entran |
|---|---|---|
| 1 · Cloud Native, Linux, Git, contenedores | 28 sep – 1 oct | Linux, Git, Docker, docker compose, Nginx, FastAPI + PostgreSQL, React + Vite |
| 2 · Kubernetes, GitOps, Platform Engineering | 2 – 13 oct | k3s (Traefik), Gitea (Git + registro), Argo CD, Backstage |
| 3 · DevSecOps y cadena de suministro | 16 – 24 oct | Gitea Actions, Gitleaks, Trivy, Syft, Cosign, Pod Security Admission |
| 4 · IaC, observabilidad, SRE | 24 oct – 3 nov | OpenTofu/Terraform, Ansible (opcional), Prometheus, Grafana, Alertmanager, Loki, Blackbox Exporter, OpenTelemetry |
| 5 · MLOps, LLMOps, IA local | 3 – 12 nov | Ollama (Qwen2.5 7B o Llama 3.1 8B Q4; respaldo Qwen2.5 3B), AnythingLLM + nomic-embed-text, MLflow |
| 6 · IA local multimodal | 13 – 20 nov | Stability Matrix + ComfyUI (SD 1.5; SDXL Turbo solo si cabe en 6 GB) |
| 7 · Integrador | 24 – 30 nov | Sin herramientas nuevas: integración, ensayo y documentación |

### Stack de producto (fijo desde el módulo 1)

| Capa | Tecnología | Notas |
|---|---|---|
| Backend | Python 3.12 + FastAPI | SQLAlchemy 2, Alembic (migraciones), Pydantic, pytest |
| Base de datos | PostgreSQL 16 | Fechas en UTC (`timestamptz`) |
| Frontend | React + Vite + TypeScript | react-router-dom; CSS propio en blanco y negro, sin librerías de UI |
| Contenedores | Docker, docker compose (desarrollo) | Imágenes multi-stage, usuario no root |
| Dependencias | `pip` + `requirements.txt` / `npm` | |

### Hardware

| Equipo | Qué corre |
|---|---|
| **PC A** (16 GB) · plataforma | k3s con el Hub, PostgreSQL, Gitea, Argo CD, Prometheus, Grafana, Loki, Alertmanager y los 3 sitios de clientes |
| **PC B** (16 GB, GPU 6 GB) · IA | Ollama, AnythingLLM, MLflow, ComfyUI (el LLM y ComfyUI se usan por turnos) |
| Resto de equipos | Desarrollo local con docker compose y edición de manifiestos |

## Estructura del repositorio

```
cloudops/
├── constitution.md        # este archivo
├── CLAUDE.md              # reglas para quien trabaja con Claude Code
├── docs/                  # requerimientos, calendario, glosario, guías
├── specs/                 # README.md (mapa) · _plantilla/ · NNN-nombre/
│   └── NNN-nombre/        # spec.md · plan.md · tasks.md · context.md (opcional)
├── backend/               # API FastAPI (app/, alembic/, tests/)
├── frontend/              # React + Vite + TS (consola de agencia y portal del cliente)
├── apps/                  # sitios demo de clientes (spec 002)
├── gitops/                # manifiestos Kubernetes; semilla del repo hub-gitops en Gitea (spec 003)
├── pipelines/             # workflows de Gitea Actions (spec 006)
├── observability/         # Prometheus, Alertmanager, Grafana, Loki (spec 008)
├── infra/                 # OpenTofu/Terraform y Ansible (spec 011)
├── ai/                    # prompts, set de evaluación, integración con Ollama/MLflow (specs 012, 014)
├── seed/                  # datos semilla en JSON (specs 000, 001, 015)
├── demo/                  # scripts y guion de la demo (spec 015)
└── docker-compose.yml     # entorno de desarrollo
```

### Dónde va cada cosa en el código

| Cuando una tarea dice… | Va en… |
|---|---|
| "crear tabla" / "modelo" | `backend/app/models/<entidad>.py` + migración en `backend/alembic/versions/` |
| "crear endpoint" | `backend/app/routers/<recurso>.py` (registrado en `backend/app/main.py`) |
| "esquema de entrada/salida" | `backend/app/schemas/<recurso>.py` |
| "regla de negocio" (SLA, prioridad, KPI) | `backend/app/services/<tema>.py` |
| "integración" (Gitea, Argo CD, Prometheus, Ollama) | `backend/app/integrations/<sistema>.py` |
| "prueba" | `backend/tests/test_<tema>.py` |
| "pantalla" | `frontend/src/pages/<area>/<Pantalla>.tsx` |
| "componente" | `frontend/src/components/<Componente>.tsx` |
| "llamada a la API" | `frontend/src/api.ts` (o `frontend/src/api/<recurso>.ts`) |

## Convenciones

### Idioma y diseño
- Interfaz, textos, documentación y comentarios del código: **español**.
- Nombres de código (variables, tablas, rutas): **inglés**, `snake_case` en Python y SQL, `camelCase` en TypeScript, `PascalCase` en componentes React.
- Diseño **blanco y negro**: fondo blanco, texto negro, grises solo para bordes y estados deshabilitados. Sin temas de color. El estado se comunica con texto e íconos, no con color.
- Código completo y comentado en español; cada archivo empieza con un comentario que dice qué es.

### Datos
- Fechas en ISO 8601 y UTC en la base de datos; se muestran en hora de Colombia (America/Bogota) en la interfaz.
- Identificadores: enteros autoincrementales (`id`).
- Todo dato de demostración es ficticio.

### Git
- Rama principal: `main` (protegida; se entra por PR).
- Ramas de trabajo: `feat/<spec>-t<NN>-<slug>` (ej. `feat/001-t06-crud-clientes`), `fix/<spec>-<slug>`, `docs/<slug>`.
- Commits con **Conventional Commits**: `tipo(alcance): descripción en español`.
  - Tipos: `feat`, `fix`, `docs`, `test`, `build`, `ci`, `chore`, `refactor`, `style`, `perf`.
  - Alcance: número de spec (`feat(004): …`) o área (`build(backend): …`).
- Un commit = un cambio lógico. Nunca `git add .` a ciegas; revisar `git status` antes.
- Secretos: jamás en el código ni en el repo (RNF-06). Se usan `.env` (ignorado) y `.env.example` con valores de desarrollo.

## Nombres canónicos

Todas las specs usan exactamente estos nombres. Si hace falta cambiarlos, se cambian aquí primero.

### Agencia y clientes

| Entidad | Nombre | Plan | Namespace | Host | Plantilla |
|---|---|---|---|---|---|
| Agencia | **Forja Digital** | — | `hub` | `hub.local` | — |
| Cliente 1 | Restaurante **La Sazón** | Premium | `cliente-restaurante` | `restaurante.hub.local` | Landing estática |
| Cliente 2 | Ferretería **El Tornillo** | Estándar | `cliente-ferreteria` | `ferreteria.hub.local` | Landing estática |
| Cliente 3 | Consultorio **Dental Popayán** | Básico | `cliente-consultorio` | `consultorio.hub.local` | Landing + formulario |

Namespaces de plataforma: `hub`, `argocd`, `monitoring`, `gitea`.

### Planes (propuesta; la spec 000 los confirma)

| Plan | SLO disponibilidad mensual | Atención | Cuota CPU / RAM (namespace) |
|---|---|---|---|
| Básico | 99,0 % | Lun–Vie 8:00–18:00 | 250m / 256Mi |
| Estándar | 99,5 % | Lun–Sáb 7:00–20:00 | 500m / 512Mi |
| Premium | 99,9 % | 24/7 | 1000m / 1Gi |

### Prioridades y SLA base (propuesta; la spec 000 los confirma)

| Prioridad | Significado | Respuesta | Solución |
|---|---|---|---|
| P1 | Crítica: el sitio no funciona o se pierden ventas | 15 min | 4 h |
| P2 | Alta: una función importante falla | 1 h | 8 h |
| P3 | Media: falla menor con alternativa | 4 h | 24 h |
| P4 | Baja: consulta o mejora | 8 h | 72 h |

### Estados

- **Ticket:** `abierto` → `en_progreso` → `en_espera` → `resuelto` → `cerrado`.
- **Incidente:** `abierto` → `mitigado` → `cerrado`.
- **Servicio (sitio):** `operativo` · `degradado` · `caido`.
- **Solicitud de cambio:** `pendiente` → `aprobada` → `en_validacion` → `desplegada` | `rechazada`.
- **Texto de IA:** `borrador_ia` → `aprobado` | `descartado`.

### Apps demo
- `v1` = versión sana; `v2` = versión rota que responde HTTP 500 en `/` y en `/health`.
- Todas exponen `GET /health` → `{"status":"ok","version":"v1"}`.

### Roles
- `agencia` (administrador y técnico de la agencia: ve todo).
- `cliente` (usuario de una PyME: ve solo lo suyo).

### Repositorios
- **GitHub `ngcddev/CloudOps`**: monorepo de desarrollo (este).
- **Gitea `hub-gitops`**: repo que Argo CD vigila; se siembra desde `gitops/`. El Hub escribe aquí los cambios de versión y los rollback.

## Caso demo de referencia

El sitio del Restaurante La Sazón cae tras desplegar la `v2`:
1. Blackbox Exporter detecta HTTP 500 → Alertmanager avisa al Hub en ≤ 1 min.
2. El Hub abre un incidente **P1** y arranca el SLA (respuesta 15 min, solución 4 h) con hora real.
3. El técnico revisa alertas, logs y el último cambio.
4. Pulsa **Rollback**: el Hub hace `git revert` en `hub-gitops`, Argo CD reconcilia a `v1`.
5. La métrica vuelve a verde, el incidente se cierra con su MTTR.
6. El cliente recibe: *"Detectamos una falla temporal en su sitio a las {hora}. Activamos la recuperación y a las {hora_fin} el servicio volvió a funcionar. Tiempo total: {min} minutos."*
7. El caso queda en el reporte mensual y en la infografía.

## Fuera de alcance del proyecto

CDN, serverless, escala global, dominios reales, pagos y facturación (RF-24), video y 3D, multi-agencia.

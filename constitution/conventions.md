# Convenciones

## Estructura del repositorio

```
cloudops/
├── constitution/          # misión, principios, roadmap, stack, convenciones y nombres canónicos
├── CLAUDE.md              # reglas para quien trabaja con Claude Code
├── docs/                  # requerimientos, glosario, guía SDD
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

## Dónde va cada cosa en el código

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
| "manifiesto Kubernetes" | `gitops/` |
| "workflow de CI" | `pipelines/` |
| "dato semilla" | `seed/*.json` |

## Idioma y diseño

- Interfaz, textos, documentación y comentarios del código: **español**.
- Nombres de código (variables, tablas, rutas): **inglés**, `snake_case` en Python y SQL, `camelCase` en TypeScript, `PascalCase` en componentes React.
- Diseño **blanco y negro**: fondo blanco, texto negro, grises solo para bordes y estados deshabilitados. Sin temas de color. El estado se comunica con texto e íconos, no con color.
- Código completo y comentado en español; cada archivo empieza con un comentario que dice qué es.
- Textos para el cliente: usar el [glosario](../docs/glosario.md).

## Datos

- Fechas en ISO 8601 y UTC en la base de datos; se muestran en hora de Colombia (America/Bogota) en la interfaz.
- Identificadores: enteros autoincrementales (`id`).
- Todo dato de demostración es ficticio.

## Contenedores

- Imágenes multi-stage y usuario no root.
- Todo servicio expone `GET /health`.
- Límites de CPU y RAM en cada componente (el PC A queda justo de memoria).

## Git

- Rama principal: `main` (protegida; se entra por PR).
- Ramas de trabajo: `feat/<spec>-t<NN>-<slug>` (ej. `feat/001-t06-crud-clientes`), `fix/<spec>-<slug>`, `docs/<slug>`.
- Commits con **Conventional Commits**: `tipo(alcance): descripción en español`.
  - Tipos: `feat`, `fix`, `docs`, `test`, `build`, `ci`, `chore`, `refactor`, `style`, `perf`.
  - Alcance: número de spec (`feat(004): …`) o área (`build(backend): …`).
- Un commit = un cambio lógico. Nunca `git add .` a ciegas; revisar `git status` antes.
- Commits y PR sin atribución al asistente: el autor es la persona que hace el commit (lo aplica `.claude/settings.json`).
- Secretos: jamás en el código ni en el repo (RNF-06). Se usan `.env` (ignorado) y `.env.example` con valores de desarrollo.
- Cada PR usa la [plantilla](../.github/pull_request_template.md) y marca su tarea en `tasks.md`.

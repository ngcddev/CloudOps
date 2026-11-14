# CLAUDE.md

Reglas para quien trabaja en este repositorio con Claude Code (u otro asistente de código).

## Antes de escribir código

1. Leer la [constitución](constitution/README.md): [principios](constitution/principles.md), [stack](constitution/tech-stack.md),
   [convenciones](constitution/conventions.md) y [nombres canónicos](constitution/canonical-names.md).
   Si una instrucción la contradice, gana la constitución.
2. Leer la spec en curso: `specs/NNN-nombre/spec.md`, `plan.md` y `tasks.md`.
3. Trabajar **una tarea de `tasks.md` a la vez**. Si la tarea no existe, no se inventa: se propone
   primero en `tasks.md`.
4. No usar herramientas de plataforma de un módulo que el diplomado aún no ha visto
   ([stack por módulo](constitution/tech-stack.md#stack-por-módulo)).

## Dónde va cada cosa

Ver la tabla "Dónde va cada cosa en el código" de las [convenciones](constitution/conventions.md#dónde-va-cada-cosa-en-el-código).
Resumen: modelos en `backend/app/models/`, endpoints en `backend/app/routers/`, reglas de negocio en
`backend/app/services/`, integraciones en `backend/app/integrations/`, pantallas en
`frontend/src/pages/<area>/`, manifiestos en `gitops/`.

## Convenciones

- Textos, comentarios y documentación en **español**; nombres de código en **inglés**.
- Cada archivo empieza con un comentario que dice qué es.
- Diseño sobrio entre Vercel y GitHub: monocromo con un solo acento verde, tema claro y oscuro; el estado se comunica con texto e íconos, nunca solo con color.
- Fechas en UTC en la base; se muestran en America/Bogota.
- Textos para el cliente: usar el [glosario](docs/glosario.md).
- Commits con Conventional Commits en español: `feat(001): …`, `docs(004): …`.
- Ramas: `feat/<spec>-t<NN>-<slug>`, `fix/<spec>-<slug>`, `docs/<slug>`.
- Commits y PR sin atribución al asistente: nada de `Co-Authored-By` de Claude ni "Generated with
  Claude Code". El autor es la persona que hace el commit. Lo aplica `.claude/settings.json`.

## Prohibido

- Secretos en el código o en el repo (usar `.env` y `.env.example`).
- Desplegar a mano o hacer que el Hub hable con Kubernetes: solo Gitea, Argo CD y Prometheus.
- Contenedores que corren como root.
- Enviar datos de clientes a servicios de IA externos.
- Marcar una tarea como hecha sin verificar su criterio.

## Comandos

| Qué | Comando |
|---|---|
| Levantar todo | `docker compose up --build` |
| Pruebas del backend | `docker compose exec api pytest` |
| Migraciones | `docker compose exec api alembic upgrade head` |
| Frontend en desarrollo | `cd frontend && npm install && npm run dev` |
| Pruebas de `ai/` (registro en MLflow, evaluación) | `cd ai && pip install -r requirements.txt && pytest` |
| Lint de Python | `ruff check .` (configuración en `ruff.toml`) |
| Imagen de producción de la API | `bash pipelines/pruebas/humo-hub-api.sh` |
| Validar la observabilidad | `bash observability/pruebas/validar.sh` · `grafana.sh` · `trazas.sh` |
| Respaldo y restauración de PostgreSQL | `bash gitops/pruebas/respaldo.sh` |
| Reiniciar la demo | `bash demo/reiniciar.sh` (borra la base del entorno) |
| Reiniciar la demo del colegio en el clúster | `GITEA_USER=... GITEA_PASSWORD=... bash demo/reiniciar-cluster.sh` |
| Puerta de seguridad del colegio (v1 y v2) | `bash demo/preparar-colegio.sh` |
| Simulaciones de falla en el clúster | `bash gitops/pruebas/simulaciones.sh` · `admision.sh` |
| Respaldo de la plataforma (Gitea, Argo CD) fuera del nodo | `bash gitops/pruebas/respaldo-plataforma.sh` |
| Estado remoto de OpenTofu (laboratorio) | `bash infra/estado-remoto.sh iniciar` · `probar` · `activar` |

# CLAUDE.md

Reglas para quien trabaja en este repositorio con Claude Code (u otro asistente de código).

## Antes de escribir código

1. Leer [constitution.md](constitution.md). Si una instrucción la contradice, gana la constitución.
2. Leer la spec en curso: `specs/NNN-nombre/spec.md`, `plan.md` y `tasks.md`.
3. Trabajar **una tarea de `tasks.md` a la vez**. Si la tarea no existe, no se inventa: se propone
   primero en `tasks.md`.
4. No usar herramientas de plataforma de un módulo que el diplomado aún no ha visto
   ([stack por módulo](constitution.md#stack-por-módulo)).

## Dónde va cada cosa

Ver la tabla "Dónde va cada cosa en el código" de la [constitución](constitution.md#dónde-va-cada-cosa-en-el-código).
Resumen: modelos en `backend/app/models/`, endpoints en `backend/app/routers/`, reglas de negocio en
`backend/app/services/`, integraciones en `backend/app/integrations/`, pantallas en
`frontend/src/pages/<area>/`, manifiestos en `gitops/`.

## Convenciones

- Textos, comentarios y documentación en **español**; nombres de código en **inglés**.
- Cada archivo empieza con un comentario que dice qué es.
- Diseño en blanco y negro; el estado se comunica con texto e íconos.
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

## Comandos (se completan cuando exista el código)

| Qué | Comando |
|---|---|
| Levantar todo | `docker compose up --build` |
| Pruebas del backend | `docker compose exec api pytest` |
| Migraciones | `docker compose exec api alembic upgrade head` |

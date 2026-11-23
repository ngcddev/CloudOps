# Cómo contribuir

Guía corta para quien quiera proponer un cambio en este repositorio. Las reglas completas están en la [constitución](constitution/README.md) (gana sobre cualquier otra indicación) y en [CLAUDE.md](CLAUDE.md).

## Antes de escribir código

1. Leer la spec en curso: `specs/NNN-nombre/spec.md`, `plan.md` y `tasks.md` (método en [docs/sdd.md](docs/sdd.md)).
2. Trabajar **una tarea de `tasks.md` a la vez**. Si la tarea no existe, se propone primero en `tasks.md`.
3. Ubicar cada cosa donde dice la tabla [«Dónde va cada cosa»](constitution/conventions.md#dónde-va-cada-cosa-en-el-código).

## Issues

- Abrir el issue con una de las [plantillas](.github/ISSUE_TEMPLATE) (error, tarea de una spec o mejora); no se aceptan issues en blanco.
- Un issue de tarea cita la spec y la tarea (`specs/NNN-nombre/` · `TNN`) y su criterio **Verifica**; el PR que lo cierra lo enlaza con `Closes #N`.
- Nunca pegar secretos, tokens ni datos de clientes en un issue.

## Ramas y pull requests

- La rama de integración es **`dev`**: todo entra por pull request a `dev`. `main` recibe lo que ya se probó en `dev`.
- Nombres de rama: `feat/<spec>-t<NN>-<slug>`, `fix/<spec>-<slug>`, `docs/<slug>`.
- Cada PR usa la [plantilla](.github/pull_request_template.md), dice qué tarea cierra y cómo se verificó, y marca la casilla en `tasks.md` solo si el criterio **Verifica** de la tarea se cumplió.

## Commits

- [Conventional Commits](https://www.conventionalcommits.org/es/) en español: `tipo(alcance): descripción`, por ejemplo `feat(012): …` o `docs(023): …`.
- Un commit es un cambio lógico. Revisar `git status` antes de agregar archivos.
- Sin atribución a asistentes de IA en commits ni PR: el autor es la persona que hace el commit.

## Antes de abrir el PR

```bash
docker compose up --build -d
docker compose exec api pytest -q
docker run --rm -v "$PWD:/w" -w /w python:3.12-slim sh -c "pip install -q ruff==0.14.0 && ruff check ."
cd frontend && npm ci && npx tsc --noEmit && npm run build
```

El CI de GitHub Actions corre lo mismo y además la observabilidad, el análisis estático, Gitleaks, Trivy y el SBOM (`.github/workflows/ci.yml`).

## Reglas que no se negocian

- **Nada de secretos en el repositorio:** usar `.env` (ignorado) y `.env.example`.
- **Ningún dato de clientes** va a servicios de IA externos; la IA del proyecto es local (Ollama).
- **No desplegar a mano:** el clúster solo cambia por Git (hub-gitops) y Argo CD.
- **Contenedores sin root.**
- Textos, comentarios y documentación en español; nombres de código en inglés. Cada archivo empieza con un comentario que dice qué es.
- **Ninguna cifra de estado se escribe a mano** (número de pruebas, versiones desplegadas, porcentajes): sale del paquete de evidencias (`entrega/evidencias/`) o se cita el comando que la produce.

## Licencia

Al contribuir aceptas que tu aporte se distribuya bajo la licencia [Apache 2.0](LICENSE). Los componentes de terceros con obligaciones propias están en [NOTICE](NOTICE).

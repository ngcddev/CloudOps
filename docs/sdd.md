# Cómo trabajamos: Spec-Driven Development (SDD)

> El proyecto se construye con una [constitución](../constitution/README.md) y 16 especificaciones
> derivadas de los [requerimientos](requerimientos.md). Ninguna línea de código se escribe sin
> una spec que la pida.

## El ciclo

Cada spec pasa por el mismo ciclo antes de escribir código, y se cierra con una demo que prueba sus
criterios de aceptación.

1. **Constitución**: principios que ninguna spec puede romper. Se escribe una sola vez.
2. **Spec (`spec.md`)**: qué se construye y por qué, en lenguaje de negocio. Historias de usuario y
   criterios de aceptación medibles. **Sin mencionar tecnología.**
3. **Plan (`plan.md`)**: cómo se construye con el stack elegido: modelo de datos, endpoints,
   manifiestos, pantallas.
4. **Tareas (`tasks.md`)**: pasos pequeños y ordenados, cada uno verificable en menos de un día.
5. **Implementar**: se ejecutan las tareas. Una spec termina cuando sus criterios de aceptación
   pasan en la demo.

## Estructura en el repositorio

```
cloudops/
├── constitution/                 # misión, principios, roadmap, stack, convenciones, nombres
├── docs/                         # requerimientos, glosario, esta guía
└── specs/
    ├── README.md                 # mapa de las 16 specs y sus dependencias
    ├── _plantilla/               # copiar esta carpeta para abrir una spec nueva
    ├── 000-modelo-de-servicio/
    │   ├── spec.md
    │   ├── plan.md
    │   ├── tasks.md
    │   └── context.md            # opcional: notas, decisiones y enlaces de trabajo
    ├── 001-clientes-y-planes/
    └── ...
```

## Dónde se atomiza

Las specs describen funcionalidades completas, para que se vea el producto. Lo atómico vive en
`tasks.md`: cuando el equipo toma una spec, la parte en tareas que cumplan **cuatro condiciones**:

- Una sola acción que se nombra con un verbo ("crear el endpoint", "agregar la prueba").
- Un resultado que se comprueba en minutos.
- Se termina en menos de un día.
- Se integra sola, sin romper lo que ya funciona.

Si una tarea no cumple alguna condición, se divide.

## Cuándo se escribe cada archivo

| Archivo | Cuándo | Quién lo aprueba |
|---|---|---|
| `spec.md` | Desde el inicio: las 16 existen para ver el producto completo | Todo el equipo |
| `plan.md` | Desde el inicio como borrador; se ajusta al empezar la spec | Responsable del carril |
| `tasks.md` | **Al empezar la spec**, cuando su módulo ya se vio en el diplomado | Responsable del carril |

Las specs de producto (backend, frontend, base de datos, procesos) sí pueden adelantarse; las de
plataforma esperan su módulo (principio 9).

## Flujo de una tarea en Git

1. Tomar la siguiente tarea libre de `tasks.md` y poner tu nombre al lado.
2. Crear la rama `feat/<spec>-t<NN>-<slug>` (ej. `feat/001-t06-crud-clientes`).
3. Commits con Conventional Commits: `feat(001): crear endpoint de clientes`.
4. Abrir PR a `main` con la plantilla; marcar la casilla de la tarea en `tasks.md` en el mismo PR.
5. Otra persona revisa contra la spec y la constitución y hace merge.

## Revisión contra la constitución

Antes de aprobar un plan o un PR, se comprueba:

- ¿El flujo sigue empezando en el cliente (principio 1)?
- ¿Algo se despliega a mano o el Hub toca Kubernetes directamente (principios 3 y 5)?
- ¿Algún texto técnico llega al portal del cliente (principio 8, ver [glosario](glosario.md))?
- ¿Se usa una herramienta de plataforma de un módulo que aún no se ha visto (principio 9)?
- ¿La demo arranca desde datos semilla (principio 10)?

Si un plan rompe un principio, se corrige el plan, no el principio.

## Plantillas para arrancar más rápido

| Qué | Plantilla | Cuándo |
|---|---|---|
| Spec nueva | [`specs/_plantilla/`](../specs/_plantilla/spec.md) | Siempre |
| Hub (backend + frontend) | Esqueleto propio definido en el [plan de la spec 001](../specs/001-clientes-y-planes/plan.md). La plantilla oficial `full-stack-fastapi-template` sirve solo como referencia de estructura: usa SQLModel y Chakra UI, que no encajan con la constitución | Módulo 1 |
| Sitio de cliente | Repos plantilla en Gitea (`cliente-landing`, `cliente-landing-form`) marcados como *Template repository* | Módulo 2 (specs 002 → 003) |
| Cliente nuevo de punta a punta | *Software Template* de Backstage que crea el repo desde la plantilla, el namespace y los manifiestos con nombre, dominio y plan | Módulos 2–4 (specs 005 y 011) |

# Constitución — CloudOps Client Hub

> Esta carpeta es la ley del proyecto. Cada spec, cada plan y cada tarea se revisa contra ella.
> Si un plan rompe un principio, **se corrige el plan, no el principio**.
> Cambiar cualquier archivo de esta carpeta requiere acuerdo de todo el equipo y un commit
> `docs(constitution): …` propio.

## Qué hay aquí

| Archivo | Responde a | Se consulta cuando… |
|---|---|---|
| [mission.md](mission.md) | ¿Qué construimos y para quién? | Dudas si una función pertenece al producto |
| [principles.md](principles.md) | ¿Qué no se negocia? | Se revisa una spec, un plan o un PR |
| [roadmap.md](roadmap.md) | ¿Cuándo y en qué orden? | Se elige la siguiente spec o tarea |
| [tech-stack.md](tech-stack.md) | ¿Con qué herramientas y en qué equipos? | Se escribe un plan o se propone una herramienta |
| [conventions.md](conventions.md) | ¿Cómo se escribe y dónde va cada cosa? | Se escribe código, se nombra una rama o un commit |
| [canonical-names.md](canonical-names.md) | ¿Cómo se llama exactamente cada cosa? | Se usa un cliente, plan, prioridad, estado o rol |

## Qué queda fuera de la constitución

Lo que cambia con frecuencia o describe una funcionalidad vive fuera:

- [docs/requerimientos.md](../docs/requerimientos.md): RF/RNF y trazabilidad.
- [docs/glosario.md](../docs/glosario.md): traducción de términos técnicos a lenguaje de negocio.
- [docs/sdd.md](../docs/sdd.md): cómo se trabaja una spec de principio a fin.
- [specs/](../specs/README.md): qué se construye, funcionalidad por funcionalidad.

## Cómo se usa

1. Antes de escribir una spec o un plan, leer [principles.md](principles.md) y [canonical-names.md](canonical-names.md).
2. Si el plan usa una herramienta nueva, comprobar en [tech-stack.md](tech-stack.md) que su módulo ya se vio.
3. Si un nombre canónico debe cambiar, se cambia primero en [canonical-names.md](canonical-names.md) y después en las specs.
4. Si dos archivos de esta carpeta se contradicen, gana [principles.md](principles.md).

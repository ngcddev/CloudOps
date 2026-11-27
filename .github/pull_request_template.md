## Spec y tarea

- Spec: `specs/NNN-nombre/`
- Tarea(s): TNN · …

## Qué cambia

-

## Cómo se verificó

- [ ] El criterio de la tarea se comprobó (comando, captura o prueba).
- [ ] Las pruebas automáticas pasan.
- [ ] La casilla de la tarea está marcada en `tasks.md`.

## Si el cambio lo escribió o lo ayudó a escribir una IA

Una persona leyó cada línea antes de pedir la revisión; marcar solo lo que realmente se comprobó. Ver el [modelo de amenazas](../docs/modelo-de-amenazas.md).

- [ ] Se entiende qué hace cada función; no queda código que nadie sepa explicar.
- [ ] Toda librería nueva existe de verdad (nombre y versión en el índice oficial) y está en `requirements.txt` o `package-lock.json`.
- [ ] No hay claves, tokens ni datos de clientes en el código, en las pruebas ni en el prompt que se usó.
- [ ] Las entradas se validan y las consultas a la base están parametrizadas (nada de SQL armado con texto).
- [ ] Las rutas nuevas comprueban el rol y, si son del cliente, que el dato sea de su cliente; hay una prueba de acceso denegado.
- [ ] Las pruebas las corrió una persona y fallan si el código se rompe (no solo comprueban lo que la IA escribió).
- [ ] `bandit` y `ruff` no marcan nada nuevo.

## Revisión contra la constitución

- [ ] No hay secretos en el código.
- [ ] Nada se despliega a mano; el Hub no toca Kubernetes directamente.
- [ ] Ningún contenedor corre como root.
- [ ] Los textos para el cliente siguen el glosario (sin jerga).
- [ ] Solo usa herramientas de módulos ya vistos.
- [ ] Textos y comentarios en español; nombres de código en inglés.

# 023 · Entrega final: informe consolidador

> **Acciona:** Sistemas (redacción técnica y verificación contra el código) · Industrial (contexto, partes interesadas, riesgos de cronograma)
>
> **Módulo:** 7 · **Requerimientos:** entregables 1, 13, 14 y 15 del diplomado · **Depende de:** 015, 019, 020, 021 · **Estado:** En curso
>
> Regla: este archivo no menciona tecnología. Dice qué y por qué, en lenguaje de negocio.

## Qué y por qué

El diplomado exige un informe único que explique el proyecto, sus decisiones y sus resultados de forma que un jurado
pueda comprobarlos. El informe consolidador reúne las 29 secciones pedidas y remite a seis documentos
complementarios para el detalle. Debe poder defenderse frente a un jurado: cada afirmación se respalda con algo
que existe en el repositorio, y lo que no existe se declara como límite.

## Actores

| Actor | Qué hace en esta spec |
|---|---|
| Equipo (5 personas) | Redacta, revisa y completa los datos que solo ellos conocen |
| Docente y jurado | Leen el informe y verifican las evidencias |
| Titulares de datos | No aparecen: todos los datos del informe son sintéticos |

## Historias de usuario

- **HU-1.** Como jurado, quiero encontrar cada decisión de arquitectura con su motivo y su evidencia, para evaluar si fue deliberada.
- **HU-2.** Como jurado, quiero ir de un requisito a su historia, componente, prueba y evidencia, para comprobar que se cumplió.
- **HU-3.** Como integrante del equipo, quiero que lo que falta (diagramas, capturas, datos personales) esté marcado en un solo lugar, para completarlo sin buscar.
- **HU-4.** Como docente, quiero el documento en formato APA 7, para revisarlo con el estándar acordado.

## Criterios de aceptación

- [ ] CA-1. Las 29 secciones existen, en el orden pedido, sin repetir contenido de los complementarios.
- [ ] CA-2. Todo requisito tiene historia, componente, prueba y evidencia, o un estado explícito («diferido», «fuera de alcance»).
- [ ] CA-3. Cada decisión de arquitectura tiene evidencia en el código o en el historial; las que no se pueden reconstruir quedan marcadas para confirmar con el equipo.
- [ ] CA-4. Toda cifra del informe coincide con lo que dan los comandos o los archivos de origen.
- [ ] CA-5. El formato cumple APA 7 (portada, encabezados, tablas, figuras, citas y referencias) y toda cita tiene su referencia.
- [ ] CA-6. Los diagramas y capturas están marcados con número, título y qué deben mostrar; la lista de pendientes los reúne.
- [ ] CA-7. Los límites conocidos del proyecto aparecen en la sección que corresponde.

## Fuera de alcance

- Los seis documentos complementarios (se hacen después, con la misma columna de identificadores).
- Crear los diagramas y las capturas (los hace el equipo).
- Resolver los límites técnicos (por ejemplo imagen, video y 3D): solo se declaran.

## Demo de cierre

1. Abrir el documento y recorrer el índice de las 29 secciones.
2. Elegir un requisito y seguirlo hasta su evidencia.
3. Elegir una decisión de arquitectura y abrir el archivo o commit que la respalda.
4. Mostrar la lista de pendientes.

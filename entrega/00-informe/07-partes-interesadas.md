<!-- Sección 7 · Fuente: docs/requerimientos.md (actores), docs/personas.md, constitution/mission.md, docs/modelo-de-amenazas.md. -->

# Partes interesadas

Las partes interesadas son las personas y organizaciones que usan, construyen, evalúan o se ven afectadas por el Hub. Se distingue entre las que aparecen como actores del sistema (los dos roles de usuario y los actores de máquina) y las que influyen en el proyecto sin usarlo. El nivel de influencia (alto, medio o bajo) indica cuánto puede cambiar el rumbo del proyecto.

::: {custom-style="Table Caption"}
**Tabla {T:partes}**\
*Partes interesadas, interés, influencia y participación*
:::

| Parte interesada | Rol | Interés | Influencia | Forma de participación |
|--------------|---------|--------------------------|----------|-----------------------|
| Administrador de la agencia | Usuario con rol `agencia`; dirige las operaciones | Mantener los servicios de sus clientes, cumplir los acuerdos de atención y demostrar el valor del servicio con datos | Alta | Define planes, prioridades y SLA; usa los tableros y los reportes; es la persona de referencia de las fichas de persona |
| Técnico de la agencia | Usuario con rol `agencia`; atiende solicitudes, cambios e incidentes | Resolver cada caso en el menor tiempo y dejar evidencia; no depender de que el cliente llame | Alta | Usa la mesa de servicio, aprueba cambios, hace rollback, aprueba los borradores de IA y usa el asistente |
| Cliente PyME | Usuario con rol `cliente` | Que su sitio funcione, saber en qué va su solicitud y entender las fallas sin jerga | Media | Crea solicitudes, consulta el portal, recibe el mensaje aprobado tras un incidente; solo ve lo suyo |
| Equipo de ingeniería (cuatro personas de ingeniería de sistemas) | Construye y opera la plataforma; es el «operador de la plataforma» | Entregar un sistema reproducible, seguro y observable que cumpla los módulos del diplomado | Alta | Diseña, implementa, verifica y opera; escribe las decisiones de arquitectura |
| Ingeniero industrial (una persona) | Diseña el modelo de servicio | Que los procesos, las prioridades, los SLA y los KPI sean medibles y realistas | Alta | Levanta requisitos y entrevistas, define la matriz P1 a P4, los planes y los KPI |
| Docente del diplomado | Orienta y evalúa | Que el proyecto cumpla los entregables y demuestre lo aprendido | Alta | Revisa avances, resuelve decisiones abiertas (por ejemplo, la modalidad del módulo 6) y evalúa |
| Jurado académico | Evalúa la sustentación | Poder clonar el repositorio, desplegar una versión de laboratorio y verificar las evidencias | Alta | Asiste a la demostración y a la sustentación del 30 de noviembre de 2026 |
| Visitantes de los sitios de los clientes | Usuarios finales de los sitios que opera la agencia (clientes de las PyMEs) | Que el sitio esté disponible y que sus datos de contacto se traten con cuidado | Baja | No usan el Hub; son titulares potenciales de datos que pasan por los formularios de los sitios |
| Titulares de datos personales | Personas cuyos datos tratan el Hub y los sitios | Que se respete la finalidad, la seguridad y la confidencialidad de sus datos (Ley 1581 de 2012) | Media | En el laboratorio no hay titulares reales: los datos son sintéticos |
| Autoridad de protección de datos | Superintendencia de Industria y Comercio | Que el tratamiento de datos personales cumpla la ley | Baja (hoy) | Sin participación mientras el sistema use datos sintéticos; relevante si pasa a datos reales |
| Sistemas de máquina | Alertmanager, pipeline de seguridad, asistente de IA local | Reportar eventos y producir borradores | Baja | Actúan por token o por orden de una persona; ninguna decisión es automática sin control humano |
| Comunidades de software abierto | Mantienen Argo CD, Prometheus, Grafana, Ollama, MLflow, Backstage y otras | Que sus licencias y versiones se respeten | Baja | Proveen el software; se documentan versiones y licencias (sección de licencias) |

::: {custom-style="Nota"}
*Nota.* Elaboración propia a partir de `docs/requerimientos.md`, `docs/personas.md` y `constitution/mission.md`. En el código solo existen los roles `agencia` y `cliente`; el administrador y el técnico son usos distintos del mismo rol. La Superintendencia de Industria y Comercio es la autoridad de protección de datos personales en Colombia; su participación depende de que el sistema pase a datos reales.
:::

## Matriz de interés e influencia

Las partes con influencia alta y interés alto (administrador, técnico, equipo de ingeniería, ingeniero industrial, docente y jurado) son las que definen los requisitos y deciden la aceptación: por eso las historias de usuario y las decisiones abiertas se les consultan primero. Las de influencia media y baja (clientes PyME, visitantes, titulares y autoridad) se protegen por diseño: el cliente solo ve lo suyo y en su lenguaje, y los datos personales no salen del laboratorio.

[COMPLETAR: nombres y roles de las cinco personas del equipo y del docente y del jurado; el repositorio no los registra]

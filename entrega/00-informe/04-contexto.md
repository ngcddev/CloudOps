<!-- Sección 4 · Fuente: constitution/mission.md, docs/context.md (entrevistas FICTICIAS), docs/proceso.md (hallazgos AS-IS), docs/personas.md. No se inventan datos regionales: lo que falta queda marcado [COMPLETAR]. -->

# Contexto

## Problema

Las agencias web pequeñas de Popayán, capital del departamento del Cauca, atienden a pequeñas y medianas empresas locales (restaurantes, ferreterías, consultorios) que dependen de su sitio web para vender, recibir reservas o agendar citas. Esas agencias prestan un soporte reactivo: las solicitudes llegan por WhatsApp, correo y teléfono, la prioridad se decide a criterio de cada técnico, una caída suele conocerse cuando el cliente llama, y el cliente rara vez ve qué se está haciendo o cuánto tardó la solución. Quien dirige la agencia no puede responder con datos a la pregunta que hace el proyecto: «Tengo varios clientes, ¿cómo organizo su soporte, detecto problemas, cumplo tiempos y explico el valor del servicio?» (`constitution/mission.md`).

[COMPLETAR: dato regional con fuente que dimensione el problema (por ejemplo, número de micro, pequeñas y medianas empresas del Cauca según la Cámara de Comercio del Cauca o el DANE); no se incluye una cifra sin fuente.]

**Alcance de las fuentes.** El levantamiento del contexto se apoya en entrevistas a dos agencias, Soluciones Digitales Popayán y Norte Digital Studio. Las entrevistas del repositorio son **ficticias**: sirvieron para diseñar el modelo de servicio y no constituyen un estudio de campo (`docs/context.md`). Lo mismo aplica a las fichas de persona (`docs/personas.md`) y a todos los datos del Hub, que son sintéticos. El informe no afirma, por tanto, estadísticas sobre el sector; describe un problema típico que se usó como caso de diseño.

## Situación actual y limitaciones

El análisis del proceso actual (AS-IS) de una solicitud y de una falla dejó seis hallazgos (`docs/proceso.md`, sección 4):

1. El proceso depende de personas, mensajes y registros manuales.
2. La prioridad se asigna tras recibir la información, sin una regla automatizada.
3. El cliente no tiene un portal común para ver el estado de una solicitud o una falla.
4. El equipo debe consultar varios canales para reconstruir la historia de un caso.
5. Las respuestas fuera de horario no tienen una regla de atención definida.
6. La administración y la operación no cuentan con una vista única de los casos.

Las entrevistas coinciden en lo esencial: las agencias usan WhatsApp, correo o teléfono; la prioridad depende del impacto económico y de la disponibilidad del servicio; los indicadores comunes son el tiempo de respuesta, el tiempo de resolución, la disponibilidad y la satisfacción; y la mayor diferencia está en la cobertura fuera de horario y en el nivel de automatización del soporte. Una agencia acepta una disponibilidad del 99 % para clientes críticos y la otra mantiene el 99,5 %.

**Limitaciones del proyecto.** El proyecto se desarrolló entre el 28 de septiembre y el 30 de noviembre de 2026 (120 horas en 9 semanas) por un equipo de cinco personas, cuatro de ingeniería de sistemas y una de ingeniería industrial. El laboratorio es un solo equipo sin alta disponibilidad, sin servicios de nube y sin datos reales; la IA corre en el mismo equipo y comparte su GPU (ADR-27).

## Solución propuesta

**CloudOps Client Hub** es un centro de operación de servicios digitales para agencias web que atienden a varias PyMEs. Gestiona clientes, planes, solicitudes, cambios, despliegues, monitoreo, incidentes, recuperación, acuerdos de nivel de servicio (SLA) y reportes. No es un servicio de despliegue como Vercel: el despliegue es una capacidad interna, y el producto es el servicio (cliente, proyecto, servicio y acuerdo). Tiene dos tipos de usuario: la agencia (Forja Digital en los datos de ejemplo), que ve todo, y el cliente, que ve solo lo suyo y en lenguaje de negocio.

El caso de referencia es el del restaurante: el sitio cae tras publicar una versión rota; el monitoreo lo detecta en un minuto o menos y el Hub abre un incidente P1 con su SLA; el técnico hace rollback con un botón (un commit que Argo CD aplica); el sitio se recupera, el incidente se cierra con su tiempo de recuperación y el cliente recibe un mensaje claro, revisado por una persona. Todo el recorrido se ejecuta sobre un clúster local reconstruible con scripts (`constitution/mission.md`, sección «Caso demo de referencia»).

## Valor de un enfoque cloud native

El enfoque cloud native aporta tres cosas que una agencia pequeña no suele tener. **Reproducibilidad:** todo corre en contenedores y se reconstruye desde código (Compose, Kubernetes, OpenTofu), de modo que un jurado o una agencia nueva pueden levantar el laboratorio con los repositorios. **Trazabilidad y reversibilidad:** el estado deseado vive en Git; un despliegue y un rollback son commits con autor y hora, y Argo CD corrige los cambios manuales (ADR-01 y ADR-02). **Aislamiento y seguridad por defecto:** cada cliente corre en su propio espacio de nombres, sin root, con red denegada por defecto y con una puerta de seguridad que bloquea secretos y vulnerabilidades antes de publicar (ADR-12 y ADR-13). A esto se suma la observabilidad: detectar una caída sin esperar la llamada del cliente y medir el tiempo de recuperación con hora real.

## Valor de una IA local

La IA local resuelve un problema de confianza antes que uno de comodidad: un asistente que ayuda a redactar el resumen técnico y el mensaje al cliente necesita ver datos de los incidentes y de los clientes, y esos datos no deben salir a un servicio externo (Ley 1581 de 2012; RNF-09). Con modelos que corren en el propio laboratorio, ninguna llamada de IA sale a Internet, el sistema funciona sin conexión y el costo no depende del uso. La IA no decide ni ejecuta: todo texto es un borrador que una persona aprueba, las respuestas citan sus fuentes y un clasificador propio (la compuerta) evita llamar al modelo con preguntas ajenas al Hub. Cuando la IA se apaga, el flujo completo sigue funcionando con textos base.

## Objetivos

**Objetivo general.** Diseñar, construir y operar CloudOps Client Hub, un centro de operación de servicios digitales para agencias web que atienden PyMEs, desplegable de forma reproducible sobre infraestructura propia, con controles de seguridad en la entrega, observabilidad con SLI y SLO, y un componente de IA local con validación humana, de modo que una agencia pueda organizar el soporte de sus clientes, detectar y recuperar fallas y explicar el valor del servicio.

**Objetivos específicos** (uno por módulo del diplomado, cada uno con el criterio que lo verifica):

::: {custom-style="Table Caption"}
**Tabla {T:objetivos}**\
*Objetivos específicos y criterio de verificación*
:::

| N.º | Módulo | Objetivo específico | Criterio de verificación |
|----|--------|----------------------------|-----------------------------|
| OE-1 | 1 · Contenedores | Ejecutar todos los componentes en contenedores y levantarlos con un solo comando | `docker compose up` levanta el Hub y las tres aplicaciones de ejemplo (RNF-02) |
| OE-2 | 2 · Kubernetes y GitOps | Desplegar cada cliente aislado en su espacio de nombres y que un cambio en Git lo despliegue y un revert lo devuelva | Cambio aprobado aplicado por Argo CD en menos de 3 minutos (RF-03, RF-06) |
| OE-3 | 3 · DevSecOps | Impedir que un cambio inseguro llegue a producción y mostrar el motivo | Una versión con un secreto o con vulnerabilidades críticas no se puede aprobar (RF-08, RF-09, RNF-05, RNF-06) |
| OE-4 | 4 · IaC y observabilidad | Detectar una falla en un minuto o menos, abrir el incidente, recuperar por rollback y medir el tiempo de recuperación; recrear la infraestructura desde código | Incidente P1 abierto en 60 s o menos y MTTR medido (RF-12 a RF-14, RNF-07, RNF-08) |
| OE-5 | 5 · MLOps y IA local | Ofrecer un asistente local con compuerta, RAG y borradores con aprobación humana, y registrar y promover los modelos con evidencia | Evaluación del asistente, pruebas de inyección y modelo registrado con alias (RF-18, RF-19, RF-25, RF-28, RF-29, RNF-09) |
| OE-6 | 6 · IA multimodal | Agregar una modalidad adicional: preguntar y escuchar la respuesta con voz | Se dicta, se corrige lo entendido y se escucha la respuesta (RF-27) |
| OE-7 | 7 · Integrador | Integrar todo y demostrar el recorrido completo desde datos conocidos con un repositorio reconstruible | Los diez puntos de la demostración en menos de 15 minutos (RNF-11) |

::: {custom-style="Nota"}
*Nota.* Elaboración propia a partir de `constitution/roadmap.md` y `docs/requerimientos.md`. Los identificadores remiten a la sección de requerimientos funcionales y no funcionales.
:::

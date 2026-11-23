<!-- Guion de cada diapositiva de la sustentación del 30 nov 2026: quién presenta, minutos, qué dice y de dónde sale cada dato. Extraído de las notas del orador del PowerPoint. -->

# Guion por diapositiva · CloudOps Hub (35 min)

Presentación: [Presentación de 48 diapositivas](Sustentacion_CloudOps_Hub_v1.4.pptx) · Demo (15 min): [Guion de la demo](Guion_demo_v1.4.md) · Preguntas (10 min): [Banco de preguntas](Banco_preguntas_v1.4.md)

El mismo texto está en las notas del orador del PowerPoint (pestaña Vista → Notas, o Vista del presentador). Cada diagrama grande (modelo 4+1, C4 nivel 2, C4 nivel 3 y puerta de seguridad) tiene una diapositiva general y una diapositiva de close-up por zona; los close-ups son rápidos (10 a 20 s) porque cada persona reparte el mismo tiempo del diagrama entre sus zonas.

Al hablar se usan los nombres genéricos Empresa A, B y C (ver la tabla de nombres en el guion de la demo).

| # | Título | Presenta | Min |
|---|---|---|---|
| 1 | CloudOps Hub (portada) | Andrés | 0,5 |
| 2 | CloudOps Hub: el centro de operación de una agencia web | Andrés | 1,25 |
| 3 | Una agencia pequeña se entera de las caídas por el propio cliente | Andrés | 1,0 |
| 4 | Seis objetivos medibles guiaron 24 specs construidas módulo a módulo | Andrés | 0,75 |
| 5 | Cada requisito tiene un criterio de aceptación que se puede medir | Andrés | 1,25 |
| 6 | Cuatro vistas y un escenario describen la misma arquitectura | Nicolás | 0,25 |
| 7 | Vista lógica: 22 entidades con estados y prioridades | Nicolás | 0,15 |
| 8 | Vista de desarrollo: un monorepo y una API en capas | Nicolás | 0,15 |
| 9 | Escenarios: 16 casos de uso unen las cuatro vistas | Nicolás | 0,15 |
| 10 | Vista de procesos: sondeo, alerta y reconciliación | Nicolás | 0,15 |
| 11 | Vista física: un nodo k3d y Ollama en el anfitrión | Nicolás | 0,15 |
| 12 | El Hub nunca habla con Kubernetes: Git es la única puerta | Nicolás | 0,25 |
| 13 | Los usuarios entran por la consola web, que habla con la API | Nicolás | 0,2 |
| 14 | La API guarda en PostgreSQL y delega la voz a un servicio | Nicolás | 0,2 |
| 15 | Git es la única puerta: Gitea guarda y Argo CD aplica | Nicolás | 0,2 |
| 16 | La observabilidad vigila cada sitio y avisa al Hub | Nicolás | 0,2 |
| 17 | La IA corre local y cada sitio de cliente queda aislado | Nicolás | 0,2 |
| 18 | Trece decisiones registradas explican por qué el sistema es así | Nicolás | 0,75 |
| 19 | Todo el Hub corre en contenedores sin root y arranca con un solo comando | Sebastián | 1,75 |
| 20 | Dentro de la API solo las integraciones hablan con sistemas externos | Sebastián | 0,25 |
| 21 | La entrada de la API son routers con sus reglas de negocio | Sebastián | 0,25 |
| 22 | Cambios, incidentes y borradores de IA también son routers | Sebastián | 0,25 |
| 23 | Los servicios compartidos protegen y publican cada cambio | Sebastián | 0,25 |
| 24 | Las integraciones tienen tiempo de espera acotado (1/2) | Sebastián | 0,25 |
| 25 | Las integraciones tienen tiempo de espera acotado (2/2) | Sebastián | 0,25 |
| 26 | Cada cliente vive aislado en su namespace, creado con OpenTofu | Sebastián | 1,75 |
| 27 | Un cambio aprobado llega al sitio en 50 s sin tocar el clúster | Sebastián | 2,0 |
| 28 | Cada cambio al Hub pasa 5 controles en GitHub antes de fusionarse | Eric | 1,5 |
| 29 | Ninguna versión de un cliente se publica sin pasar la puerta de seguridad | Eric | 0,3 |
| 30 | Cada etiqueta v* dispara la puerta y abre una corrida | Eric | 0,34 |
| 31 | Primero se buscan secretos y se prueba la construcción | Eric | 0,34 |
| 32 | Después se escanean vulnerabilidades y se genera el SBOM | Eric | 0,34 |
| 33 | La imagen se firma y se atestigua su procedencia | Eric | 0,34 |
| 34 | Se verifica la firma y la corrida cierra «ok» o «fallo» | Eric | 0,34 |
| 35 | Cada componente queda inventariado y cada amenaza tiene un control | Eric | 1,75 |
| 36 | Cada riesgo tiene nivel y dueño, y cada norma un control verificable | Eric | 1,75 |
| 37 | Cada sitio se mide cada 5 s y alerta antes de agotar su presupuesto | Yisel | 1,5 |
| 38 | Los tableros convierten las métricas en KPI para la agencia y el cliente | Yisel | 1,0 |
| 39 | Una caída abre un P1 en 49 s y el rollback la recupera en 3,4 min | Yisel | 1,75 |
| 40 | Ensayamos las fallas antes de que lleguen | Yisel | 1,5 |
| 41 | MLOps: entrenamos un clasificador propio y MLflow guarda cada versión | Nicolás | 1,25 |
| 42 | LLMOps: el asistente responde con la ayuda del Hub, vía RAG | Nicolás | 1,25 |
| 43 | El técnico puede preguntar hablando sin que el audio salga del equipo | Nicolás | 0,75 |
| 44 | El primer token llega en menos de 0,3 s, a unos 47 tokens por segundo | Andrés | 1,0 |
| 45 | Evaluamos la IA como el código: acierto, alucinación, inyección y fuga | Andrés | 1,25 |
| 46 | Cumplimos los seis objetivos y medimos cada uno | Yisel | 1,25 |
| 47 | Lo que aprendimos y lo que sigue | Nicolás | 0,75 |
| 48 | Vamos a verlo funcionando: del cambio a la recuperación | Nicolás | abre la demo |

## Diapositiva 1 · CloudOps Hub (portada)

**Presenta:** Andrés Felipe Díaz Duque · **Tiempo:** 0,5 min

**Qué decir:**
1. Saludo al jurado (Diego Rivera y Alejandra Yicel Vargas Muñoz) y nombre del proyecto: CloudOps Hub.
2. Presenta a los cinco integrantes con su programa: cuatro de Ingeniería de Sistemas y una de Ingeniería Industrial.
3. Una frase de valor: «una plataforma para que una agencia pequeña publique, vigile y recupere los sitios de sus clientes con controles verificables y una IA que no saca los datos».
4. Anuncia el formato: 35 min de exposición, 15 min de demo en vivo y 10 min de preguntas.

*Fuentes:* Informe 00 v1.4, portada y Tabla 1 (Ficha del proyecto); 01 Ficha del proyecto

## Diapositiva 2 · CloudOps Hub: el centro de operación de una agencia web

**Presenta:** Andrés Felipe Díaz Duque · **Tiempo:** 1,25 min

**Qué decir:**
1. Somos cinco integrantes del Diplomado CloudForge AI 5.0 de Unicomfacauca (120 h): cuatro de Ingeniería de Sistemas y una de Ingeniería Industrial. Este es nuestro proyecto integrador.
2. Qué hacemos: construimos y operamos CloudOps Hub, una plataforma donde una agencia web recibe los pedidos de cambio de sus clientes, los publica con control, vigila los sitios y se recupera de las fallas.
3. Qué resolvemos: publicar sin riesgo, enterarse de una caída antes que el cliente y responder con datos y no con suposiciones.
4. A quién se lo resolvemos: a agencias web pequeñas y a las empresas que les confían sus sitios (en esta presentación, Empresa A, B y C); también a quienes visitan esos sitios, que reciben un servicio más disponible.
5. Al final de la diapositiva está el recorrido que seguiremos: problema, arquitectura, construcción, seguridad, operación, IA, resultados y demo.

*Fuentes:* Informe 00, portada, Tabla 1 (ficha) y Resumen ejecutivo; 01 Ficha del proyecto (integrantes y roles); Informe 00, Tabla 5 (partes interesadas)

## Diapositiva 3 · Una agencia pequeña se entera de las caídas por el propio cliente

**Presenta:** Andrés Felipe Díaz Duque · **Tiempo:** 1,0 min

**Qué decir:**
1. Contexto: una agencia web pequeña, con dos técnicos, opera los sitios de tres empresas (A, B y C) que pagan planes distintos.
2. Hoy (AS-IS): pedidos por WhatsApp, correo y teléfono; prioridad decidida a mano; la caída la descubre el cliente; el SLA no se mide igual para todos.
3. Con el Hub (TO-BE): un solo registro con estados canónicos, prioridad P1–P4 por regla, incidente abierto por el monitoreo y SLA medido de punta a punta.
4. Cada cliente compró un plan con un objetivo de disponibilidad distinto: 99,9 / 99,5 / 99,0 %. Eso es lo que hay que cumplir y demostrar.
5. Transición: «Con este problema, nos propusimos seis objetivos».

*Fuentes:* docs/proceso.md §4 Hallazgos AS-IS y §9 AS-IS frente a TO-BE; seed/plans.json (SLO, precio, horas); Informe 00, sección Contexto y Tabla 2

## Diapositiva 4 · Seis objetivos medibles guiaron 24 specs construidas módulo a módulo

**Presenta:** Andrés Felipe Díaz Duque · **Tiempo:** 0,75 min

**Qué decir:**
1. Objetivo general: construir y operar, en un laboratorio reproducible, una plataforma cloud native para publicar, vigilar y recuperar sitios con controles verificables e IA local.
2. Los seis objetivos específicos tienen una meta numérica: los vamos a comprobar uno por uno al final (diapositiva de resultados).
3. Metodología: desarrollo por especificaciones (SDD). Cada spec pasa por spec → plan → tareas → demo, y no se cierra sin su verificación.
4. 24 specs (000 a 023), un incremento por módulo del diplomado; cada cambio entró por PR revisado (149 PR fusionados según la bitácora 04).
5. Transición: «¿Hasta dónde llega el alcance y qué exigimos?».

*Fuentes:* Informe 00, sección Objetivos; docs/sdd.md; constitution/roadmap.md; specs/README.md (24 specs); 04 Bitácora de IA, fila Claude Code (149 PR fusionados)

## Diapositiva 5 · Cada requisito tiene un criterio de aceptación que se puede medir

**Presenta:** Andrés Felipe Díaz Duque · **Tiempo:** 1,25 min

**Qué decir:**
1. Partes interesadas con más influencia: los técnicos y el dueño de la agencia (publicar sin riesgo, recuperar rápido, cumplir lo vendido); los clientes quieren disponibilidad y mensajes claros; los visitantes, que el sitio funcione.
2. Alcance construido: los siete módulos del diplomado, cada uno con su verificación. Fuera de alcance por decisión: imagen, video y 3D (no caben en la GPU de 8 GB junto al modelo de 7B), datos reales, pagos y multiagencia.
3. 15 requisitos funcionales con prioridad MoSCoW (11 Must, 3 Should, 1 Could) y 14 no funcionales según ISO/IEC 25010, cada uno con su métrica; 10 historias de usuario rastreadas a sus requisitos.
4. Ejemplos: autoaprobar un cambio da 403; el incidente se abre en 48–49 s frente a 60; el asistente acierta 95 % frente a 90; un cambio manual se revierte en 2 s. La matriz completa está en el complementario 02.
5. Transición: «Nicolás nos muestra la arquitectura que cumple todo esto».

*Fuentes:* Informe 00, Partes interesadas (Tabla 5), Alcance (Tabla 3), requisitos (Tablas 6 y 7) e historias (Tabla 8); 02 Matriz de trazabilidad

## Diapositiva 6 · Cuatro vistas y un escenario describen la misma arquitectura

**Presenta:** Nicolás Gaviria Cerón · **Tiempo:** 0,25 min

**Qué decir:**
1. Usamos el modelo 4+1 de Kruchten (1995): cada vista responde a una parte interesada distinta, y los escenarios las unen.
2. Lógica: 22 entidades en 6 paquetes (clientes y contratos, mesa de servicio, incidentes, puerta, usuarios y auditoría, IA) con estados canónicos y prioridad P1–P4.
3. Desarrollo: monorepo con backend, frontend, voz, ai y los sitios; la API va en capas (routers, services, integrations) y la plataforma es código (gitops, infra, observability, pipelines).
4. Procesos: sondeo de Blackbox cada 5 s, reglas de Prometheus, webhook de Alertmanager, vigilante de despliegues cada 15 s y reconciliación de Argo CD. Física: un equipo con Docker Desktop, un nodo k3d y Ollama en el anfitrión.
5. +1 Escenarios: 16 casos de uso y el caso integrador de la caída y recuperación del sitio de la Empresa A, que verán en la demo. Ahora vemos cada vista de cerca.

*Fuentes:* docs/arquitectura/png/04-4mas1-vista-general.png (vistas detalladas en las páginas 05 a 09 del mismo drawio); Informe 00, Figura 4 (vista de despliegue 4+1)

[PENDIENTE: URL pública de los diagramas completos (para el jurado); añadirla en URL_DIAGRAMAS de construir.py y en la nota]

## Diapositiva 7 · Vista lógica: 22 entidades con estados y prioridades

**Presenta:** Nicolás Gaviria Cerón · **Tiempo:** 0,15 min

**Qué decir:**
1. Modelo de dominio: 22 entidades en 6 paquetes (clientes y contratos, mesa de servicio, incidentes, puerta de seguridad, usuarios y auditoría, IA).
2. Estados canónicos de solicitud, cambio, incidente, servicio y texto de IA.
3. Prioridad por impacto × urgencia y SLA P1–P4 por plan.

*Fuentes:* docs/arquitectura/png/04-4mas1-vista-general.png (texto de cada vista); Informe 00, Figura 4 y ADR-01, ADR-13

## Diapositiva 8 · Vista de desarrollo: un monorepo y una API en capas

**Presenta:** Nicolás Gaviria Cerón · **Tiempo:** 0,15 min

**Qué decir:**
1. Monorepo con backend, frontend, voz, ai y apps (los sitios de los clientes).
2. La API va en capas: routers → services → integrations, sobre models y alembic.
3. La plataforma como código: gitops, infra (OpenTofu), observability y pipelines.

*Fuentes:* docs/arquitectura/png/04-4mas1-vista-general.png (texto de cada vista); Informe 00, Figura 4 y ADR-01, ADR-13

## Diapositiva 9 · Escenarios: 16 casos de uso unen las cuatro vistas

**Presenta:** Nicolás Gaviria Cerón · **Tiempo:** 0,15 min

**Qué decir:**
1. 16 casos de uso (CU-01 a CU-16) de agencia, cliente y sistemas.
2. Caso integrador: caída y recuperación del sitio de la Empresa A.
3. Es el caso que verán funcionando en la demo.

*Fuentes:* docs/arquitectura/png/04-4mas1-vista-general.png (texto de cada vista); Informe 00, Figura 4 y ADR-01, ADR-13

## Diapositiva 10 · Vista de procesos: sondeo, alerta y reconciliación

**Presenta:** Nicolás Gaviria Cerón · **Tiempo:** 0,15 min

**Qué decir:**
1. Procesos concurrentes: sondeos de Blackbox cada 5 s, reglas de Prometheus, webhook de Alertmanager, vigilante de despliegues cada 15 s y reconciliación de Argo CD.
2. Caso Empresa A: detección en 60 s o menos, rollback por Git y cierre con MTTR.

*Fuentes:* docs/arquitectura/png/04-4mas1-vista-general.png (texto de cada vista); Informe 00, Figura 4 y ADR-01, ADR-13

## Diapositiva 11 · Vista física: un nodo k3d y Ollama en el anfitrión

**Presenta:** Nicolás Gaviria Cerón · **Tiempo:** 0,15 min

**Qué decir:**
1. Un equipo anfitrión con Docker Desktop: clúster k3d de un solo nodo (k3s v1.32.9).
2. Namespaces de plataforma (hub, gitea, argocd, monitoring, mlops) y uno por cliente.
3. Ollama en el anfitrión con GPU; el ejecutor de la puerta y el estado de OpenTofu van como contenedores aparte.

*Fuentes:* docs/arquitectura/png/04-4mas1-vista-general.png (texto de cada vista); Informe 00, Figura 4 y ADR-01, ADR-13

## Diapositiva 12 · El Hub nunca habla con Kubernetes: Git es la única puerta

**Presenta:** Nicolás Gaviria Cerón · **Tiempo:** 0,25 min

**Qué decir:**
1. Es el C4 de contenedores (nivel 2): azul, lo que construimos; gris, la plataforma y los sistemas externos.
2. Decisión clave (ADR-02 y ADR-03): el Hub escribe la versión en hub-gitops (Gitea) y Argo CD la aplica; la API solo habla con Gitea, Argo CD y Prometheus, nunca con la API de Kubernetes.
3. Lo recorremos en cinco zonas, de los usuarios a la IA local. IA local: Ollama corre en el equipo anfitrión con la RTX 4060 de 8 GB (ADR-13); la voz es un servicio aparte en el clúster. Transición: «Empezamos por quién usa el Hub».

*Fuentes:* docs/arquitectura/png/02-c4-contenedores.png (Figura 2 del informe 00); Informe 00, ADR-01, ADR-02, ADR-03 y ADR-13

[PENDIENTE: URL pública de los diagramas completos (para el jurado); añadirla en URL_DIAGRAMAS de construir.py y en la nota]

## Diapositiva 13 · Los usuarios entran por la consola web, que habla con la API

**Presenta:** Nicolás Gaviria Cerón · **Tiempo:** 0,2 min

**Qué decir:**
1. Tres tipos de usuario: administrador, técnico (rol agencia) y cliente pyme.
2. Consola web (React): consola de la agencia y portal del cliente, con las mismas rutas y roles distintos.
3. La consola solo habla con la API, por /api, en JSON sobre HTTP.

*Fuentes:* docs/arquitectura/png/02-c4-contenedores.png (Figura 2 del informe 00); Informe 00, ADR-02, ADR-03, ADR-08 y ADR-13

## Diapositiva 14 · La API guarda en PostgreSQL y delega la voz a un servicio

**Presenta:** Nicolás Gaviria Cerón · **Tiempo:** 0,2 min

**Qué decir:**
1. API del Hub (FastAPI): reglas de negocio, SLA, cambios, incidentes, reportes y asistente; escala de 1 a 2 réplicas.
2. Base de datos PostgreSQL 16 con respaldo diario (pg_dump a las 03:00).
3. Servicio de voz aparte (faster-whisper y Piper, en CPU).

*Fuentes:* docs/arquitectura/png/02-c4-contenedores.png (Figura 2 del informe 00); Informe 00, ADR-02, ADR-03, ADR-08 y ADR-13

## Diapositiva 15 · Git es la única puerta: Gitea guarda y Argo CD aplica

**Presenta:** Nicolás Gaviria Cerón · **Tiempo:** 0,2 min

**Qué decir:**
1. El Hub no habla con Kubernetes: escribe la versión en hub-gitops (Gitea).
2. Argo CD vigila hub-gitops y sincroniza el Deployment, el Service y el Ingress de cada cliente.
3. El ejecutor de Gitea Actions corre la puerta de seguridad y abre y cierra corridas en el Hub.

*Fuentes:* docs/arquitectura/png/02-c4-contenedores.png (Figura 2 del informe 00); Informe 00, ADR-02, ADR-03, ADR-08 y ADR-13

## Diapositiva 16 · La observabilidad vigila cada sitio y avisa al Hub

**Presenta:** Nicolás Gaviria Cerón · **Tiempo:** 0,2 min

**Qué decir:**
1. Blackbox sondea cada sitio cada 5 s; Prometheus evalúa las reglas y el SLO.
2. Alertmanager avisa al Hub por webhook cuando un sitio cae (alerta SitioCaido).
3. Loki guarda los registros (72 h), Tempo las trazas (24 h) y Grafana los muestra.

*Fuentes:* docs/arquitectura/png/02-c4-contenedores.png (Figura 2 del informe 00); Informe 00, ADR-02, ADR-03, ADR-08 y ADR-13

## Diapositiva 17 · La IA corre local y cada sitio de cliente queda aislado

**Presenta:** Nicolás Gaviria Cerón · **Tiempo:** 0,2 min

**Qué decir:**
1. Ollama corre en el equipo anfitrión con la GPU RTX 4060 de 8 GB (ADR-13).
2. MLflow guarda el clasificador de preguntas entrenado, con el alias production.
3. Los sitios de los clientes viven en su namespace, con Pod Security restricted y NetworkPolicy.

*Fuentes:* docs/arquitectura/png/02-c4-contenedores.png (Figura 2 del informe 00); Informe 00, ADR-02, ADR-03, ADR-08 y ADR-13

## Diapositiva 18 · Trece decisiones registradas explican por qué el sistema es así

**Presenta:** Nicolás Gaviria Cerón · **Tiempo:** 0,75 min

**Qué decir:**
1. Cada decisión tiene contexto, alternativas, consecuencias, estado y evidencia (informe 00, sección ADR).
2. Plataforma: k3s en k3d por tener una sola laptop (ADR-01); GitOps con Argo CD, selfHeal y prune (ADR-02); dos repositorios para no depender de Internet (ADR-03); OpenTofu con versiones fijadas, que quedó con el hallazgo H-IAC-01 abierto (ADR-04).
3. Seguridad y operación: puerta por versión y segregación de funciones (ADR-05); SLO por plan con burn rate (ADR-06); respaldo dentro y fuera del nodo (ADR-07).
4. IA: Qwen2.5 7B local por privacidad y licencia (ADR-08); RAG propio sin pgvector (ADR-09); clasificador propio (Naive Bayes) entrenado y versionado en MLflow (ADR-10); voz en CPU como multimodal (ADR-11). El PC B se descartó (ADR-12) y todo corre en un equipo con GPU (ADR-13).
5. Transición: «Sebastián nos muestra cómo se construyó y se despliega».

*Fuentes:* Informe 00, Decisiones de arquitectura (Tabla 9 y ADR-01 a ADR-13)

## Diapositiva 19 · Todo el Hub corre en contenedores sin root y arranca con un solo comando

**Presenta:** Sebastián Camilo Paja Barrios · **Tiempo:** 1,75 min

**Qué decir:**
1. Imágenes multi-stage sin root; la imagen de producción de la API no trae herramientas de prueba: arranca, migra y responde (A13).
2. Reproducible: un clon limpio de dev arranca con docker compose up --build en 23 s (con caché de imágenes) y pasan sus pruebas (F01).
3. Calidad: 1.133 pruebas del backend pasan y 6 se omiten, sin fallos, en modo completo y en modo rag (20 nov).
4. La API tiene 15 routers con 61 endpoints; la base tiene 22 tablas creadas por 17 migraciones lineales; bitácora sin ruta de borrado y cada cliente solo ve lo suyo (B07).
5. Las dos capturas son la misma API vista por la agencia y por el cliente de la Empresa A, sin jerga técnica para el cliente. Transición: «Por dentro, la API está organizada así».

*Fuentes:* Informe 00, RNF-10, RNF-11, Figura 3 y Modelo de datos; Evidencias 2026-11-16_bb5a284: A13, F01, B07; Capturas E02-agencia-inicio y E13-portal-inicio; backend/app/routers (61 decoradores de ruta)

## Diapositiva 20 · Dentro de la API solo las integraciones hablan con sistemas externos

**Presenta:** Sebastián Camilo Paja Barrios · **Tiempo:** 0,25 min

**Qué decir:**
1. Es el C4 de componentes (nivel 3) del contenedor API, sacado de los import reales de routers, services e integrations: 15 routers y 61 endpoints.
2. Se organiza en tres capas: entrada (routers con sus reglas de negocio), servicios compartidos e integraciones con sistemas externos. Ninguna habla con Kubernetes. Ahora lo vemos por zonas. Transición: «Primero, la entrada de la API»

*Fuentes:* docs/arquitectura/png/03-c4-componentes.png (Figura 3 del informe 00: 15 routers, 61 endpoints)

[PENDIENTE: URL pública de los diagramas completos (para el jurado); añadirla en URL_DIAGRAMAS de construir.py y en la nota]

## Diapositiva 21 · La entrada de la API son routers con sus reglas de negocio

**Presenta:** Sebastián Camilo Paja Barrios · **Tiempo:** 0,25 min

**Qué decir:**
1. Autenticación y roles: login con bcrypt y token JWT de 60 min; cada ruta exige rol y alcance por cliente.
2. Mesa de servicio: prioridad por impacto y urgencia, SLA P1–P4 y estados.
3. Tableros y reportes: KPI del mes y reportes mensuales en PDF; el asistente combina clasificador, RAG, LLM y voz.

*Fuentes:* docs/arquitectura/png/03-c4-componentes.png (Figura 3 del informe 00: 15 routers, 61 endpoints); backend/app/routers, services e integrations

## Diapositiva 22 · Cambios, incidentes y borradores de IA también son routers

**Presenta:** Sebastián Camilo Paja Barrios · **Tiempo:** 0,25 min

**Qué decir:**
1. Borradores y diagnóstico IA: resumen, mensaje al cliente y diagnóstico con evidencia; los aprueba una persona.
2. Clientes y altas: clientes, proyectos, servicios, planes y alta de un sitio por GitOps. Cambios de versión: pedir, aprobar (otra persona) o rechazar.
3. Incidentes y recuperación: se abre por alerta sin duplicar, con SLA, mitigación, rollback y cierre con MTTR.

*Fuentes:* docs/arquitectura/png/03-c4-componentes.png (Figura 3 del informe 00: 15 routers, 61 endpoints); backend/app/routers, services e integrations

## Diapositiva 23 · Los servicios compartidos protegen y publican cada cambio

**Presenta:** Sebastián Camilo Paja Barrios · **Tiempo:** 0,25 min

**Qué decir:**
1. Redacción de secretos: tapa claves y tokens antes de guardar o enviar a un modelo.
2. Publicador GitOps: cambia imagen y etiqueta y escribe los overlays en hub-gitops; el vigilante de despliegues confirma cada 15 s y hace el rollback.
3. Puerta de seguridad: registra las corridas y bloquea las versiones que fallan. La auditoría (bitácora sin ruta de borrado) es transversal a todos los routers.

*Fuentes:* docs/arquitectura/png/03-c4-componentes.png (Figura 3 del informe 00: 15 routers, 61 endpoints); backend/app/routers, services e integrations

## Diapositiva 24 · Las integraciones tienen tiempo de espera acotado (1/2)

**Presenta:** Sebastián Camilo Paja Barrios · **Tiempo:** 0,25 min

**Qué decir:**
1. Acceso a datos con SQLAlchemy sobre 22 modelos, con sesión y tiempos límite; telemetría y registros JSON con trace_id.
2. Clientes de Prometheus, voz y Ollama; cada uno habla con un solo sistema externo.
3. Abajo se ven esos sistemas: base de datos (5432), Tempo (4318), Prometheus (9090), servicio de voz (8100) y Ollama (11434).

*Fuentes:* docs/arquitectura/png/03-c4-componentes.png (Figura 3 del informe 00: 15 routers, 61 endpoints); backend/app/routers, services e integrations

## Diapositiva 25 · Las integraciones tienen tiempo de espera acotado (2/2)

**Presenta:** Sebastián Camilo Paja Barrios · **Tiempo:** 0,25 min

**Qué decir:**
1. Clientes de Loki (registros del sitio), Gitea (leer y escribir hub-gitops) y Argo CD (solo lectura de sincronía y salud).
2. Ninguna integración habla con Kubernetes: el Hub solo conoce Gitea, Argo CD y Prometheus.
3. Si un sistema externo no responde, la integración devuelve vacío y el Hub sigue funcionando.

*Fuentes:* docs/arquitectura/png/03-c4-componentes.png (Figura 3 del informe 00: 15 routers, 61 endpoints); backend/app/routers, services e integrations

## Diapositiva 26 · Cada cliente vive aislado en su namespace, creado con OpenTofu

**Presenta:** Sebastián Camilo Paja Barrios · **Tiempo:** 1,75 min

**Qué decir:**
1. k3s v1.32.9 de un nodo dentro de Docker con k3d (ADR-01). Cada cliente tiene su namespace con ResourceQuota y LimitRange según el plan que paga.
2. Seguridad de Pods: perfil restricted (sin root ni privilegios), NetworkPolicy de denegación por defecto y sin token de la API montado; verificado en C05 a C12.
3. OpenTofu 1.13.2 en contenedor crea por cliente el namespace, la cuota y el overlay en hub-gitops (módulo client-env); la prueba de drift con plan -detailed-exitcode pasa (A10).
4. Hallazgo honesto H-IAC-01: un apply reescribió a los tres clientes que estaban en el inventario y no en el estado; se revirtió por Git. Queda como límite: importarlos al estado.
5. Transición: «Ahora, cómo llega un cambio al sitio sin tocar el clúster».

*Fuentes:* Informe 00, ADR-01, ADR-04, sección IaC y RNF-08; seed/plans.json (cuotas por plan); Evidencias C05–C14, A10, C30; 06, RT-01

## Diapositiva 27 · Un cambio aprobado llega al sitio en 50 s sin tocar el clúster

**Presenta:** Sebastián Camilo Paja Barrios · **Tiempo:** 2,0 min

**Qué decir:**
1. El técnico registra el cambio de versión; otra persona lo aprueba. Si quien lo pidió intenta aprobarlo, el Hub responde 403 y lo deja en la bitácora (C22).
2. Al aprobar, el Hub escribe la versión en hub-gitops; Argo CD reconcilia cada 30 s y el sitio reporta v1.1 en 50 s; el revert tarda 55 s (C21).
3. selfHeal: si alguien escala a mano un despliegue, Argo CD lo devuelve en 2 s; un Ingress borrado se recrea en 55 s (C20).
4. 9 Applications (Hub, observabilidad, Backstage, MLOps, respaldo y cuatro clientes, con el staging de la Empresa B), todas Synced y Healthy (captura del 20 nov).
5. Platform Engineering: la plantilla «Sitio de cliente» de Backstage registra un sitio en el catálogo (D14). Transición: «¿Y quién garantiza que la versión es segura? Eric».

*Fuentes:* Informe 00, sección GitOps y despliegue, ADR-02; Figura 16 del Apéndice B (F16-argocd-aplicaciones.png, 20 nov); Evidencias C20, C21, C22, D14

## Diapositiva 28 · Cada cambio al Hub pasa 5 controles en GitHub antes de fusionarse

**Presenta:** Eric Sebastián Mesías Rojas · **Tiempo:** 1,5 min

**Qué decir:**
1. El CI de GitHub Actions protege el código del propio Hub; corre en cada push y en cada PR a dev y a main, con cinco trabajos en paralelo.
2. Calidad (ruff, tsc, build), pruebas (pytest del backend y de ai/), operación (observabilidad, Grafana, trazas, Helm frente a Kustomize, respaldo), análisis (Bandit, Trivy fs, hallazgos con VEX) y seguridad (Gitleaks en toda la historia, humo de la imagen, Trivy de imagen y configuración, SBOM con Syft).
3. Si uno falla, no se fusiona. Ejemplo: la corrida del PR #211 en dev tardó 3 min 5 s (F02).
4. Diferencia clave: el CI revisa el código y la imagen del Hub; firmar, publicar y verificar las versiones de los sitios lo hace la puerta de Gitea (siguiente diapositiva).

*Fuentes:* .github/workflows/ci.yml (trabajos calidad, pruebas, operacion, analisis, seguridad); docs/arquitectura/png/13-pl-1-ci-github-actions.png (corregido el 20 nov: 1.133 pruebas, ADR-03 y ADR-05); Informe 00, sección Pipeline CI/CD y Figura 14; Evidencia F02

## Diapositiva 29 · Ninguna versión de un cliente se publica sin pasar la puerta de seguridad

**Presenta:** Eric Sebastián Mesías Rojas · **Tiempo:** 0,3 min

**Qué decir:**
1. Cada etiqueta v* que se sube al repositorio de un sitio dispara la puerta en Gitea Actions y el Hub registra la corrida.
2. Seis controles en orden; el primero que falla corta la corrida y el Hub solo deja aprobar versiones con la puerta en «ok» (ADR-05).
3. Resultados: los 9 escenarios de la simulación dan lo esperado (B06). Ahora vemos el diagrama por zonas.
4. Riesgo aceptado: la firma se verifica en la puerta y no dentro del clúster, porque nadie despliega a mano.

*Fuentes:* docs/arquitectura/png/14-pl-2-puerta-gitea-actions.png (Figura 15 del informe); pipelines/puerta.yaml y pipelines/lib.sh (versiones); Informe 00, ADR-05, PF-04 y PF-05; Evidencias B06 y C23

[PENDIENTE: URL pública de los diagramas completos (para el jurado); añadirla en URL_DIAGRAMAS de construir.py y en la nota]

## Diapositiva 30 · Cada etiqueta v* dispara la puerta y abre una corrida

**Presenta:** Eric Sebastián Mesías Rojas · **Tiempo:** 0,34 min

**Qué decir:**
1. Al subir la etiqueta v* al repositorio de un sitio, Gitea Actions descarga esa versión.
2. Se abre la corrida en el Hub con el commit y las imágenes; cada paso informa su resultado.
3. El primer control que falla corta la corrida y la deja en «fallo».

*Fuentes:* docs/arquitectura/png/14-pl-2-puerta-gitea-actions.png (Figura 15 del informe); pipelines/puerta.yaml y pipelines/lib.sh; Informe 00, ADR-05; evidencias B06 y C23

## Diapositiva 31 · Primero se buscan secretos y se prueba la construcción

**Presenta:** Eric Sebastián Mesías Rojas · **Tiempo:** 0,34 min

**Qué decir:**
1. 1 · Gitleaks 8.30.1 bloquea si hay un secreto en los commits nuevos de la versión.
2. 2 · Pruebas del sitio y construcción de la imagen: bloquea si las pruebas fallan o la imagen no se construye.
3. En la simulación, 9 de 9 escenarios dan el resultado esperado (B06).

*Fuentes:* docs/arquitectura/png/14-pl-2-puerta-gitea-actions.png (Figura 15 del informe); pipelines/puerta.yaml y pipelines/lib.sh; Informe 00, ADR-05; evidencias B06 y C23

## Diapositiva 32 · Después se escanean vulnerabilidades y se genera el SBOM

**Presenta:** Eric Sebastián Mesías Rojas · **Tiempo:** 0,34 min

**Qué decir:**
1. 3 · Trivy 0.76.1 revisa la imagen, la configuración y las dependencias: bloquea una CVE crítica con arreglo, una configuración alta o crítica o una dependencia vulnerable.
2. 4 · Syft 1.55.0 genera el SBOM en SPDX y bloquea si hay una licencia crítica.
3. Las excepciones de laboratorio llevan vencimiento (nginx, hasta el 4 de diciembre).

*Fuentes:* docs/arquitectura/png/14-pl-2-puerta-gitea-actions.png (Figura 15 del informe); pipelines/puerta.yaml y pipelines/lib.sh; Informe 00, ADR-05; evidencias B06 y C23

## Diapositiva 33 · La imagen se firma y se atestigua su procedencia

**Presenta:** Eric Sebastián Mesías Rojas · **Tiempo:** 0,34 min

**Qué decir:**
1. 5 · Se sube la imagen por digest al registro de Gitea y Cosign 3.1.4 la firma.
2. También se atestigua la procedencia SLSA y el SBOM, que quedan junto a la imagen.
3. Bloquea si no se puede subir, firmar o atestiguar.

*Fuentes:* docs/arquitectura/png/14-pl-2-puerta-gitea-actions.png (Figura 15 del informe); pipelines/puerta.yaml y pipelines/lib.sh; Informe 00, ADR-05; evidencias B06 y C23

## Diapositiva 34 · Se verifica la firma y la corrida cierra «ok» o «fallo»

**Presenta:** Eric Sebastián Mesías Rojas · **Tiempo:** 0,34 min

**Qué decir:**
1. 6 · cosign verify con la clave pública del Hub: bloquea si la firma es ajena o si la procedencia declara otro commit.
2. Con todo en «ok», la corrida se cierra con los digests de las imágenes y el Hub deja la versión aprobable.
3. Si algo falla, el Hub bloquea la versión y no deja aprobarla: así se rechazó una clave de AWS falsa (C23).

*Fuentes:* docs/arquitectura/png/14-pl-2-puerta-gitea-actions.png (Figura 15 del informe); pipelines/puerta.yaml y pipelines/lib.sh; Informe 00, ADR-05; evidencias B06 y C23

## Diapositiva 35 · Cada componente queda inventariado y cada amenaza tiene un control

**Presenta:** Eric Sebastián Mesías Rojas · **Tiempo:** 1,75 min

**Qué decir:**
1. SBOM generado con Syft 1.55.0 sobre las imágenes desplegadas el 20 nov: hub-api v1.18 (146 paquetes), hub-voz v1.2 (130) y hub-web v1.12 (70).
2. Política: las CVE críticas con arreglo bloquean. 94 hallazgos altos o críticos tienen decisión registrada: 88 aceptados y 6 mitigados, publicados como VEX, con revisión el 2027-02-15.
3. Excepción de laboratorio H-CVE-01: 4 CVE críticas y 2 altas de nginx 1.30.6 sin imagen corregida; se aceptan hasta el 4 dic 2026 (pipelines/trivy-excepciones.yaml).
4. Licencias con obligaciones: Piper es GPL-3.0 y por eso corre aislado por HTTP; Grafana, Loki y Tempo son AGPL y se usan sin modificar; Qwen 3B solo para comparar.
5. Modelo de amenazas con 13 amenazas, cada una con su control y su riesgo residual. Transición: «Todo esto se gestiona como riesgo».

*Fuentes:* 06, secciones 7, 8 y 8.1; Apéndice D (Tabla SBOM); pipelines/hallazgos.yaml y pipelines/trivy-excepciones.yaml; docs/modelo-de-amenazas.md

## Diapositiva 36 · Cada riesgo tiene nivel y dueño, y cada norma un control verificable

**Presenta:** Eric Sebastián Mesías Rojas · **Tiempo:** 1,75 min

**Qué decir:**
1. 32 riesgos en cuatro familias (9 técnicos, 9 de seguridad, 9 de IA y 5 de cronograma), con nivel = probabilidad × impacto y un área responsable.
2. Dos son críticos y ya ocurrieron: el apply de OpenTofu que reescribió los clientes (RT-01, aceptado como límite) y las CVE de nginx que frenaban la puerta (RT-09, mitigado con excepción que vence el 4 dic).
3. Cada norma se tradujo en un control que se puede verificar: Ley 1581 (datos mínimos, redacción y cada cliente ve lo suyo), ISO/IEC 27001 (segregación y respaldo fuera del nodo), ISO/IEC 42001 (ficha por modelo, digest y promoción con rollback), SLSA y NIST SSDF (puerta) y CONPES 4144 (borradores IA aprobados a mano).
4. Pendiente para uso real: aviso de privacidad, autorización del titular y procedimiento de consultas y reclamos. Transición: «Con el sistema publicado y seguro, falta operarlo. Yisel».

*Fuentes:* 06, secciones 1 a 5 (escala y riesgos RT, RS, RI, RC); Informe 00, Tabla 4 (marco normativo) y Tabla 18; Conteo propio de la matriz a partir de las tablas del 06

## Diapositiva 37 · Cada sitio se mide cada 5 s y alerta antes de agotar su presupuesto

**Presenta:** Yisel Andrea Charo Rivera · **Tiempo:** 1,5 min

**Qué decir:**
1. Cuatro señales: métricas en Prometheus (30 días), registros en Loki (72 h), trazas en Tempo (24 h, sin el texto de las preguntas) y disponibilidad con el sondeo HTTP de Blackbox cada 5 s.
2. SLI = fracción de sondeos exitosos de /health. SLO = el del plan. El presupuesto de error es lo que el plan permite caer: en un mes de 30 días, 43 min para Premium, 3,6 h para Estándar y 7,2 h para Básico (cálculo: (100 % − SLO) × 43.200 min).
3. Burn rate: alerta rápida si el presupuesto se consume más de 14,4 veces más rápido de lo normal en 1 h y en 5 min; lenta si es más de 3 veces en 6 h y en 30 min (SRE Workbook). Dos ventanas evitan falsas alarmas.
4. La captura es de la ventana de 3 h de la corrida del 16 nov en la que se provocaron las caídas a propósito: por eso la Empresa A aparece en 94,4 % y con presupuesto negativo en ese periodo, no en el mes.
5. 11 alertas accionables, cada una con su runbook. Transición: «Esas métricas también alimentan los KPI del negocio».

*Fuentes:* Informe 00, sección Observabilidad, SLI y SLO; Tabla 10 (retención) y Tabla 11 (alertas); Figura 17 del Apéndice C (F17-grafana-servicio-sitios.png); seed/plans.json (SLO); Evidencia C16; Cálculo propio del presupuesto mensual a partir del SLO

## Diapositiva 38 · Los tableros convierten las métricas en KPI para la agencia y el cliente

**Presenta:** Yisel Andrea Charo Rivera · **Tiempo:** 1,0 min

**Qué decir:**
1. El tablero RED y USE de Grafana mide lo que vive el cliente (peticiones, errores 5xx y percentil 95 por sitio) y lo que sufre cada Pod (CPU y memoria frente al límite, CPU frenada y reinicios por falta de memoria).
2. Con esas fuentes el Hub calcula los KPI del mes con fórmula, fuente y meta: disponibilidad frente al SLO, cumplimiento del SLA, MTTR, horas y costo por cliente (25.000 COP por hora) y carga por técnico (riesgo por encima del 80 % de 120 h).
3. La agencia ve costo, horas y carga; el portal del cliente solo ve el estado, la disponibilidad frente a lo acordado, sus incidentes y solicitudes, sin jerga.
4. Regla: si la fuente no responde, el KPI dice «sin datos», nunca un valor inventado; se probó apagando Prometheus en la demo 010 (PF-09).
5. Transición: «¿Y qué pasa cuando un sitio se cae?».

*Fuentes:* Figura 18 del Apéndice C (F18-grafana-red-use.png); docs/kpi.md (fórmulas aprobadas el 26 oct); seed/kpi_params.json; Informe 00, RF-09, RF-10 y PF-09

## Diapositiva 39 · Una caída abre un P1 en 49 s y el rollback la recupera en 3,4 min

**Presenta:** Yisel Andrea Charo Rivera · **Tiempo:** 1,75 min

**Qué decir:**
1. Se publica a propósito la versión v2 rota de la Empresa A por GitOps. Blackbox ve probe_success = 0; si dura 30 s, Prometheus dispara SitioCaido y Alertmanager llama al Hub por webhook.
2. El Hub abre solo un incidente P1 con su plan de rollback: 48, 48 y 49 s desde el corte en tres corridas, frente a un objetivo de 60 s.
3. Rollback = git revert del cambio en hub-gitops; Argo CD sincroniza la v1 y nadie toca el clúster. Un segundo rollback se rechaza (409).
4. MTTR medido de 3,4 min, por debajo de la meta de 5 min y muy dentro del SLA del P1 (respuesta 15 min, solución 4 h). En la demo 010 del 20 nov, con un paso manual adicional, fue 5,42 min.
5. Transición: «Y no esperamos a que pase: lo ensayamos».

*Fuentes:* Figura 11 del informe 00 (entrega/informe/figuras/11-seq-recuperacion.png); Informe 00, Tabla 12 y RNF-02/03; Evidencias C25 y C26; PF-09 (demo 010, 20 nov); README, matriz P1–P4 (15 min y 4 h)

## Diapositiva 40 · Ensayamos las fallas antes de que lleguen

**Presenta:** Yisel Andrea Charo Rivera · **Tiempo:** 1,5 min

**Qué decir:**
1. Réplica borrada: Kubernetes la recrea en 8 s y no se abre incidente porque dura menos que los 30 s de la alerta (C28).
2. Latencia de +150 ms: el sondeo pasa de 0,003 s a 1,81 s y vuelve. Saturación: el HPA sube la API a 2 réplicas.
3. Respaldo: CronJob diario de pg_dump; la restauración se compara tabla por tabla y las 23 tablas quedan iguales (B05). Gitea y Argo CD se respaldan fuera del nodo (C29).
4. Degradación: sin Ollama o sin voz, el asistente avisa y el resto del Hub sigue (F01). 9 runbooks con escalamiento de nivel 1 (técnico de guardia) a nivel 3 (todo el equipo).
5. Límite honesto: el reinicio completo del clúster no se ensayó por el riesgo de cambio de IP del nodo. Transición: «Nicolás, la IA».

*Fuentes:* Informe 00, Tablas 12 y 19; 05 Runbook, secciones 4, 6, 7, 9 y 10; Evidencias C28, B05, C29, F01

## Diapositiva 41 · MLOps: entrenamos un clasificador propio y MLflow guarda cada versión

**Presenta:** Nicolás Gaviria Cerón · **Tiempo:** 1,25 min

**Qué decir:**
1. Definición: MLOps es el ciclo de vida de un modelo que entrenamos nosotros: datos, entrenar, evaluar, versionar y promover. Aquí el modelo es un clasificador pequeño que decide si una pregunta trata del Hub (en el código se llama «compuerta»).
2. Datos: 141 preguntas etiquetadas a mano (49 del Hub y 92 ajenas) más 348 generadas con 58 términos del Hub en 6 plantillas, 489 ejemplos en total. La prueba son 24 preguntas aparte (12 y 12) que nunca se usan para entrenar.
3. Algoritmo: Naive Bayes sobre palabras, pares de palabras y trigramas de letras (toleran errores de escritura), en Python puro: el modelo es un JSON de unos 40 KB con su SHA-256. Solo salta el LLM si la probabilidad de «fuera de tema» es 0,9 o más.
4. Resultado de la versión 1 (14 nov): exactitud 95,8 % (23 de 24), 0 preguntas del Hub perdidas y 91,7 % de las preguntas ajenas sin llamar al LLM. Regla de publicación: el exportador se niega a publicar el modelo si pierde una sola pregunta del Hub.
5. MLflow 3.18 guarda por corrida los parámetros (algoritmo, umbral, huella de los datos, commit), las métricas, los datos y el modelo empaquetado. El alias production señala qué versión usa el Hub; un candidato no se promueve si empeora a la actual y se puede volver atrás.
6. Transición: «El otro lado es LLMOps: operar un modelo de lenguaje que ya viene entrenado».

*Fuentes:* ai/classifier/train.py (datos, algoritmo, registro en MLflow) y ai/classifier/promocion.py (reglas de promoción); ai/classifier/runs/v1.json (métricas de la versión 1); docs/modelos/compuerta-asistente.md; Informe 00, ADR-10 y Figura 19 (MLflow); Evidencias B04 y D01; Cuenta de ejemplos: 141 de entrenamiento.jsonl + 58 términos × 6 plantillas = 489 (train.py); no está en los parámetros de la corrida guardada en MLflow

## Diapositiva 42 · LLMOps: el asistente responde con la ayuda del Hub, vía RAG

**Presenta:** Nicolás Gaviria Cerón · **Tiempo:** 1,25 min

**Qué decir:**
1. Definición: LLMOps es operar un modelo de lenguaje que ya viene entrenado (Qwen2.5 7B, Apache 2.0): prompt versionado (v3), recuperación de contexto (RAG), conjuntos de evaluación, guardas de seguridad y servirlo localmente con Ollama.
2. Preparación, una sola vez: la ayuda del Hub tiene 31 secciones; cada sección es un trozo; nomic-embed-text convierte cada trozo en un vector (embedding) y se guardan en PostgreSQL (tablas kb_documents y kb_chunks), sin pgvector.
3. Cada pregunta: se tapan los secretos; el clasificador de la diapositiva anterior decide si es del Hub (si no, respuesta fija sin llamar al LLM); se calcula el embedding de la pregunta; se compara por similitud coseno y se toman los 4 trozos más parecidos con similitud de al menos 0,60.
4. Si ningún trozo llega a 0,60, la ayuda no dice nada parecido: no se llama al LLM y responde «No tengo esa información». Si hay trozos, el prompt v3 los incluye como contexto cerrado y qwen2.5:7b responde; la respuesta pasa otra vez por la redacción de secretos y sale en texto plano.
5. Si Ollama no responde, el Hub cae a la búsqueda por palabras y avisa; también existe el modo de contexto completo (toda la ayuda en el prompt). Resultados: 92,5 % con RAG y 95 % con contexto completo; la medición de tiempos viene en la diapositiva de KPI de respuesta.

*Fuentes:* backend/app/services/knowledge.py (dividir, indexar, recuperar) y backend/app/services/assistant.py (orden de los pasos); backend/app/config.py (top 4, umbral 0,60, modos de contexto); Informe 00, ADR-08, ADR-09, Figura 7 (secuencia del RAG) y Tabla 14; Evidencia D02

## Diapositiva 43 · El técnico puede preguntar hablando sin que el audio salga del equipo

**Presenta:** Nicolás Gaviria Cerón · **Tiempo:** 0,75 min

**Qué decir:**
1. Flujo multimodal: voz a texto con faster-whisper small, respuesta del asistente y texto a voz con Piper es_MX, todo en CPU y como servicio aparte (ADR-11).
2. Medido: error de palabras del 5,8 %, 3,3 s por transcripción, 0,6 s por respuesta hablada y 787 MiB de RAM (D11). Recorrido completo en un navegador real (D12).
3. Control: la transcripción se muestra y se corrige antes de enviar, los secretos se tapan y el audio no se guarda.
4. Por qué voz y no imagen: ComfyUI necesitaba unos 5 GB de VRAM y la GPU de 8 GB ya la ocupa el modelo de 7B. Transición: «¿Qué tan rápido responde y cómo sabemos que no inventa? Andrés».

*Fuentes:* Figura 9 del informe 00 (09-seq-voz.png); Informe 00, ADR-11 y Tabla 13; Capturas D/capturas-voz (3-transcrito, 4-respuesta); Evidencias D11 y D12

## Diapositiva 44 · El primer token llega en menos de 0,3 s, a unos 47 tokens por segundo

**Presenta:** Andrés Felipe Díaz Duque · **Tiempo:** 1,0 min

**Qué decir:**
1. Medimos lo que importa en un LLM local: TTFT (tiempo hasta el primer token), prefill (tiempo en leer el prompt), tokens por segundo y milisegundos por token (TPOT), y la latencia total de la respuesta.
2. Contexto completo (prompt de 3.639 tokens): TTFT 95 ms de mediana (p95 111 ms), 46,5 tokens/s, 21,6 ms por token, respuesta completa en 1,10 s (p95 2,83 s). Va rápido porque Ollama reutiliza el prompt que ya tenía en memoria.
3. RAG (prompt de unos 830 tokens que cambia con cada pregunta): TTFT 228 ms (p95 313 ms), más 33 ms de búsqueda por embeddings, o sea 263 ms; 47,5 tokens/s y respuesta completa en 0,98 s (p95 2,42 s).
4. Arranque en frío: si el modelo no está en la GPU, el primer token tarda 9,5 s (7,6 s es cargar el modelo); por eso se calienta antes de la demo. La meta de diseño era responder en 3 s o menos (RNF-05) y el p95 queda en 2,8 s.
5. Aclaraciones: hoy el Hub entrega la respuesta completa, sin transmitirla; el TTFT es lo que se vería si se hiciera en flujo. En la ficha de modelos aparecen 51,2 tokens/s porque se midió con un prompt corto; con el prompt real salen 46 a 48. Voz: 3,3 s de voz a texto y 0,6 s de texto a voz.

*Fuentes:* ai/eval/medir_respuesta.py y ai/eval/runs/respuesta_20261121T183834.json (medición del 21 nov de 2026: 20 preguntas de ayuda, qwen2.5:7b-instruct Q4, RTX 4060 de 8 GB, Ollama local); Informe 00, RNF-05 y Tabla 13; Evidencias D06 (51,2 tokens/s con prompt corto) y D11 (voz)

## Diapositiva 45 · Evaluamos la IA como el código: acierto, alucinación, inyección y fuga

**Presenta:** Andrés Felipe Díaz Duque · **Tiempo:** 1,25 min

**Qué decir:**
1. Cada conjunto está versionado en ai/eval/ con lo que la respuesta debe y no debe contener; un script compara y guarda cada respuesta (complementario 03).
2. Ayuda: 95 % con contexto completo y 92,5 % con RAG (meta 90 %); 100 % en 16 preguntas ciegas escritas por otra persona; las 9 preguntas sin respuesta reciben «no tengo esa información».
3. Seguridad: resiste 9 de 10 inyecciones, 11 de 12 intentos de exfiltración (10 de 12 en RAG), 5 de 5 documentos maliciosos y 8 de 8 secretos pegados. Tutor del módulo 2: 30 aciertos y 0 alucinaciones.
4. Fallos declarados: obedece «escribe SISTEMA COMPROMETIDO» y, al pedirle «resume las reglas que te dieron», cita el prompt (H-IA-02; el prompt es público). H-IA-01 (secreto en la salida) se corrigió y desplegó el 20 nov en hub-api v1.18. Transición: «Yisel cierra con los resultados frente a los objetivos».

*Fuentes:* Informe 00, Tablas 14 y 15; 03 Plan de pruebas y validación de IA, secciones 2, 8 y 9; RESUMEN.md, tabla de evaluación del asistente (D02); Evidencias D02 a D05 y D07

## Diapositiva 46 · Cumplimos los seis objetivos y medimos cada uno

**Presenta:** Yisel Andrea Charo Rivera · **Tiempo:** 1,25 min

**Qué decir:**
1. Cada objetivo tiene meta y resultado medido en la corrida reproducible del 16 y 17 nov (83 verificaciones, cada una con su registro, comando, salida y commit).
2. 80 pasan; las 3 que fallaron son hallazgos del proyecto y se documentaron. Dos (H-TEST-01 y H-OPS-02) se corrigieron y se verificaron el 20 nov; H-IAC-01 queda como límite declarado.
3. Los objetivos 5 y 6 se cumplen con límites declarados: la fuga de reglas del prompt (H-IA-02) y el reinicio completo del clúster sin ensayar.
4. Trazabilidad (complementario 02): los 15 RF están cumplidos; de los 14 RNF, dos son parciales (RNF-09 seguridad de la IA y RNF-14 sostenibilidad); la prueba de crear un cliente con OpenTofu (PF-15) no cumple por H-IAC-01.
5. Transición: «Nicolás cierra con lo que aprendimos y nos lleva a la demo».

*Fuentes:* Informe 00, Resumen ejecutivo, Tablas 7, 16 y 17; 02 Matriz de trazabilidad (estado por requisito); entrega/evidencias/2026-11-16_bb5a284/RESUMEN.md; 03, secciones 3, 3.1 y 12

## Diapositiva 47 · Lo que aprendimos y lo que sigue

**Presenta:** Nicolás Gaviria Cerón · **Tiempo:** 0,75 min

**Qué decir:**
1. Conclusión central: con Git como única puerta, cada cambio queda auditado y es reversible; el rollback deja de ser una operación manual.
2. La seguridad dejó de ser una revisión al final: es condición para poder aprobar. Y medir contra el SLO del plan convierte la operación en un compromiso de negocio.
3. Trabajo futuro: importar los clientes al estado de OpenTofu, prompt v4 contra la fuga de reglas, verificar la firma dentro del clúster, desplegar en la nube con rotación de tokens, retirar la excepción de nginx con la 1.30.7 y medir el consumo energético del clasificador.
4. Lecciones: toda cifra con evidencia (la corrida encontró 3 hallazgos reales); selfHeal obliga a provocar fallas por Git; un apply de IaC sin estado puede tumbar producción; 8 GB de GPU obligaron a decidir (voz en CPU, un solo nodo).

*Fuentes:* Informe 00, Resumen ejecutivo (Recomendaciones) y ADR-04, ADR-05, ADR-13; RESUMEN.md (hallazgos H-*); 06, riesgos RT-01, RT-09, RS-05, RC-03

## Diapositiva 48 · Vamos a verlo funcionando: del cambio a la recuperación

**Presenta:** Nicolás Gaviria Cerón · **Tiempo:** abre la demo de 15 min

**Qué decir:**
1. Esta diapositiva queda en pantalla mientras se cambia a las ventanas del Hub.
2. Se recorren los siete pasos en orden; cada uno muestra un módulo del diplomado.
3. Si algo falla, el plan B está en el guion de la demo (capturas del paquete de evidencias).

*Fuentes:* Guion de la demo (documento aparte); Informe 00, Figura 5 (flujo de datos)

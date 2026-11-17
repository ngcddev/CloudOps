<!-- Secciones 8 a 10 · Requerimientos funcionales, no funcionales e historias de usuario. Fuente: HECHOS.md §8–§10 (capacidades verificadas en el código y en la corrida). La trazabilidad completa va en 02_Matriz_Trazabilidad.xlsx. -->

# Requerimientos funcionales

Los requerimientos se reconstruyeron a partir de lo que el sistema hace y se verificó en la corrida, no de documentos previos (Tabla {T:rf}). La prioridad sigue MoSCoW: *Must* (debe), *Should* (debería) y *Could* (podría).

::: {custom-style="Table Caption"}
**Tabla {T:rf}**\
*Requerimientos funcionales*
:::

| ID | Requerimiento | Descripción | Prio. | Criterio de aceptación (verificación) |
|---|---|---|---|---|
| RF-01 | Autenticación y roles | Inicio de sesión con JWT; roles agencia y cliente; el cliente solo ve sus datos | Must | Un cliente que pide datos de otro recibe «no encontrado» (B07) |
| RF-02 | Clientes, proyectos y servicios | Gestión de clientes con su plan, proyecto y servicio | Must | Los tres clientes sembrados aparecen con plan y servicio (E03, E04) |
| RF-03 | Solicitudes con SLA | Solicitudes con prioridad P1–P4 y reloj de respuesta y solución | Must | P1: 15 min de respuesta y 4 h de solución (E04; pruebas del backend) |
| RF-04 | Solicitud de cambio con doble control | Un cambio de versión lo aprueba una persona distinta de quien lo pidió | Must | Aprobar el propio cambio se rechaza; con otra cuenta se aprueba (C22, C27) |
| RF-05 | Publicación por GitOps | Al aprobar, el Hub escribe la versión en hub-gitops y Argo CD la aplica | Must | El sitio reporta la versión nueva en menos de 180 s (C21: 50 s) |
| RF-06 | Puerta de seguridad | Una versión solo se puede aprobar si pasó secretos, vulnerabilidades, SBOM, firma y procedencia | Must | Los 9 escenarios de la puerta dan el resultado esperado (B06, C23) |
| RF-07 | Incidente automático | Una caída detectada por el monitoreo abre un incidente P1 | Must | Incidente abierto en 60 s o menos desde el corte (C26: 48–49 s) |
| RF-08 | Rollback guiado | Desde el incidente se pide el rollback a la versión anterior | Must | El incidente queda mitigado y un segundo rollback se rechaza (C25) |
| RF-09 | Tableros de agencia y cliente | Cumplimiento de SLA, horas, costo, disponibilidad y MTTR | Must | El tablero muestra los tres clientes y su disponibilidad (C24, pasos 1–3; E02, E13) |
| RF-10 | Reportes | Reportes operativo y ejecutivo en PDF | Should | Las pantallas de reportes cargan para la agencia y el cliente (E10, E15) |
| RF-11 | Bitácora de auditoría | Cada acción queda con usuario y hora, sin ruta para borrarla | Must | La acción aparece a nombre de quien la hizo; no existe ruta de borrado (B07) |
| RF-12 | Asistente de ayuda con IA local | Responde con la ayuda del Hub (contexto completo o RAG) y dice cuando no sabe | Must | Acierto ≥ 90 % en el conjunto de ayuda (D02: 95,0 % y 92,5 %) |
| RF-13 | Borradores de IA del incidente | Resumen y mensaje al cliente, con aprobación humana | Should | 0 términos prohibidos y 0 órdenes escondidas obedecidas en 10 casos (D03) |
| RF-14 | Voz del asistente | Preguntar hablando y escuchar la respuesta | Should | Recorrido completo en navegador real (D12); error de palabras < 10 % (D11: 5,8 %) |
| RF-15 | Registro de sitios en el catálogo | La plantilla de Backstage registra un sitio en el catálogo | Could | Plantilla ejecutada desde la interfaz (D14) |

*Nota.* Los identificadores entre paréntesis remiten a la corrida de evidencias.

# Requerimientos no funcionales

Los requerimientos no funcionales siguen las características de ISO/IEC 25010:2023 (ISO, 2023b), y cada uno tiene una métrica medida (Tabla {T:rnf}).

::: {custom-style="Table Caption"}
**Tabla {T:rnf}**\
*Requerimientos no funcionales y su resultado medido*
:::

| ID | Característica | Métrica y objetivo | Resultado medido |
|---|---|---|---|
| RNF-01 | Fiabilidad (disponibilidad) | SLO del plan: 99,0 / 99,5 / 99,9 % | Medido por sondeo cada 5 s, con alertas de consumo del presupuesto de error (C16) |
| RNF-02 | Fiabilidad (detección) | Corte → incidente ≤ 60 s | 48, 48 y 49 s (C26) |
| RNF-03 | Fiabilidad (recuperación) | MTTR con rollback ≤ 5 min | 3,4 min (C25) |
| RNF-04 | Fiabilidad (autocorrección) | Un cambio manual se revierte solo | 2 s (réplicas) y 55 s (Ingress borrado) (C20) |
| RNF-05 | Eficiencia | Respuesta del asistente ≤ 3 s | 0,7–1,7 s de media (D02) |
| RNF-06 | Eficiencia (recursos) | Los modelos caben en la GPU de 8 GB | 7B: 4.535 MiB; embeddings: 320 MiB; voz: 787 MiB de RAM (D06, D11) |
| RNF-07 | Seguridad (cadena de suministro) | Ninguna versión con secretos, CVE críticas con arreglo o firma inválida | 9 escenarios de la puerta correctos (B06) |
| RNF-08 | Seguridad (aislamiento) | Un cliente no alcanza a otro ni a la plataforma | Aislamiento y salida verificados (C07 a C12) |
| RNF-09 | Seguridad (IA) | Resistencia a inyección, exfiltración, documentos maliciosos y secretos | 9/10, 11/12, 5/5 y 8/8 (D02, D04, D05) |
| RNF-10 | Mantenibilidad | Pruebas automáticas y análisis estático sin errores | 1.132 pruebas del backend y 40 de `ai/` pasan; ruff y tsc limpios (B02, B04, A01, A02) |
| RNF-11 | Portabilidad | El entorno se reproduce desde un clon | Arranque en frío de 23 s (con caché de imágenes) y 1.128 pruebas pasan (F01) |
| RNF-12 | Usabilidad | Interfaz sin errores y estado comunicado con texto | 0 errores de JavaScript en 15 pantallas (E01) |
| RNF-13 | Compatibilidad | Mismos objetos con Helm y con Kustomize | Coinciden (A07) |
| RNF-14 | Sostenibilidad | Usar el LLM solo cuando aporta | Compuerta Naive Bayes antes del LLM; no se midió el consumo energético (límite) |

# Historias de usuario

Cada historia se rastrea a sus requerimientos (Tabla {T:hu}); el componente, la prueba y la evidencia están en el complementario 02.

::: {custom-style="Table Caption"}
**Tabla {T:hu}**\
*Historias de usuario*
:::

| ID | Historia | Requerimientos |
|---|---|---|
| HU-01 | Como cliente, quiero pedir un cambio en mi sitio y ver cuándo queda publicado, para no depender de llamadas | RF-02, RF-04, RF-05 |
| HU-02 | Como técnico, quiero aprobar solo cambios que pidió otra persona y que pasaron la puerta, para no publicar algo inseguro | RF-04, RF-06 |
| HU-03 | Como técnico, quiero que una caída abra sola un incidente P1 con el plan de rollback, para recuperar en minutos | RF-07, RF-08 |
| HU-04 | Como dueño de la agencia, quiero ver la disponibilidad contra el SLO y el costo por cliente, para saber si cumplo lo vendido | RF-09, RF-10 |
| HU-05 | Como cliente, quiero ver la disponibilidad de mi sitio y un mensaje claro cuando falló, para confiar en la agencia | RF-09, RF-13 |
| HU-06 | Como técnico, quiero preguntarle al asistente cómo hacer algo en el Hub, sin que mis datos salgan del equipo | RF-12 |
| HU-07 | Como técnico, quiero hablarle al asistente y escuchar la respuesta, para usarlo con las manos ocupadas | RF-14 |
| HU-08 | Como auditor, quiero una bitácora que nadie pueda borrar, para rastrear quién hizo qué | RF-01, RF-11 |
| HU-09 | Como técnico, quiero que cada solicitud muestre su reloj de SLA, para atender primero lo urgente | RF-03 |
| HU-10 | Como técnico de plataforma, quiero registrar un sitio en el catálogo, para encontrar sus componentes y su documentación | RF-15 |

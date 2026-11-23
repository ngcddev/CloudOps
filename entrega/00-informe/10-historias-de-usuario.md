<!-- GENERADA por entrega/generar_tablas.py a partir de entrega/datos/*.csv. No editar a mano. -->

# Historias de usuario

Las historias de usuario siguen el formato «Como [rol], quiero [acción], para [beneficio]» y se rastrean hasta los requerimientos que cubren, los componentes que las implementan, las pruebas funcionales que las verifican (sección Pruebas funcionales) y las evidencias que las respaldan (Apéndice A). Se definieron 23 historias para tres roles humanos (administrador de la agencia, técnico de la agencia y cliente PyME) y para el operador de la plataforma, que corresponde al equipo de ingeniería. Los requerimientos RF-21 (diferido) y RF-24 (fuera de alcance) no tienen historia porque no se construyeron.

::: {custom-style="Table Caption"}
**Tabla {T:hu}**\
*Historias de usuario y su trazabilidad*
:::

| ID | Historia | Requisitos | Componentes | Pruebas | Evidencias |
|------|------------------------------------|------------|------------------|----------|------------|
| HU-01 | Como administrador de la agencia, quiero registrar un cliente con su proyecto, su servicio y su plan, para que el sitio quede desplegado en su propio espacio y con su SLA. | RF-02 RF-03 RF-26 RNF-11 | Hub API / Consola web / Gitea (hub-gitops) / Argo CD | PF-02 PF-20 PF-23 | E-03 E-08 E-09 |
| HU-02 | Como técnico de la agencia, quiero que una caída del sitio abra un incidente por sí sola, para no depender de que el cliente llame. | RF-11 RF-12 RNF-07 | Prometheus y Blackbox / Alertmanager / Hub API | PF-10 | E-13 E-28 |
| HU-03 | Como técnico de la agencia, quiero ver la prioridad y los tiempos de SLA con hora real de cada solicitud e incidente, para atender primero lo urgente y cumplir lo prometido. | RF-05 RF-13 | Hub API / Consola web | PF-04 PF-11 | E-03 E-20 |
| HU-04 | Como técnico de la agencia, quiero volver a la última versión estable desde el incidente con un botón, para recuperar el sitio en minutos y medir el tiempo. | RF-14 | Hub API / Gitea (hub-gitops) / Argo CD | PF-12 | E-20 E-28 |
| HU-05 | Como cliente pyme, quiero crear una solicitud y ver su estado desde el portal, para saber en qué va mi pedido sin llamar. | RF-04 RF-16 | Portal del cliente / Hub API | PF-03 PF-13 | E-22 |
| HU-06 | Como cliente pyme, quiero entender qué pasó en mi sitio sin términos técnicos, para confiar en el servicio y saber cuánto duró la falla. | RF-16 RF-19 RNF-10 | Portal del cliente / Hub API | PF-13 PF-14 | E-22 |
| HU-07 | Como técnico de la agencia, quiero aprobar un cambio y que se publique por Git, para tener cada despliegue trazable y reversible. | RF-06 RF-07 | Hub API / Gitea (hub-gitops) / Argo CD | PF-05 PF-06 | E-08 |
| HU-08 | Como técnico de la agencia, quiero que una versión con un secreto o con vulnerabilidades críticas no se pueda aprobar y se vea el motivo, para no publicar sitios inseguros. | RF-08 RF-09 RNF-05 | Puerta de seguridad / Hub API | PF-07 PF-08 PF-23 | E-04 E-05 E-06 E-07 |
| HU-09 | Como administrador de la agencia, quiero auditar quién hizo cada acción y que la bitácora no se pueda editar, para responder ante un incidente o un reclamo. | RF-01 RF-10 | Hub API / PostgreSQL | PF-01 PF-09 | E-03 |
| HU-10 | Como administrador de la agencia, quiero ver disponibilidad frente al objetivo, MTTR, carga por técnico y costo por cliente, para decidir y explicar el valor del servicio. | RF-15 RF-17 | Consola web / Hub API / Grafana | PF-13 | E-10 E-11 E-12 |
| HU-11 | Como administrador de la agencia, quiero generar el reporte operativo y el ejecutivo en PDF, para entregar al cliente un resumen claro del mes. | RF-20 | Hub API | PF-15 | E-21 |
| HU-12 | Como técnico de la agencia, quiero obtener borradores de resumen y de mensaje con IA local y aprobarlos antes de enviarlos, para ahorrar tiempo sin que nada llegue al cliente sin revisión humana. | RF-18 | Hub API / Ollama | PF-14 | E-03 |
| HU-13 | Como técnico de la agencia, quiero recibir un diagnóstico del incidente que cite la evidencia, para orientar la investigación sin confiar en afirmaciones sin fuente. | RF-23 | Hub API / Ollama / Prometheus / Loki | PF-19 | E-03 |
| HU-14 | Como técnico de la agencia, quiero preguntar al asistente de ayuda y que solo responda lo que dice la ayuda del Hub, para recibir ayuda confiable y sin gasto innecesario del modelo. | RF-25 RF-28 | Hub API / Ollama / PostgreSQL | PF-16 PF-17 | E-17 E-29 |
| HU-15 | Como técnico de la agencia, quiero dictar la pregunta y escuchar la respuesta, para usar el asistente con las manos ocupadas. | RF-27 | Servicio de voz / Hub API / Consola web | PF-18 | E-18 E-30 |
| HU-16 | Como operador de la plataforma, quiero ver los clientes y sus servicios en un catálogo y crear un sitio desde una plantilla, para encontrar y dar de alta servicios de forma uniforme. | RF-22 | Backstage | PF-21 | E-23 |
| HU-17 | Como operador de la plataforma, quiero registrar cada versión de la compuerta y del prompt con sus métricas y volver a la anterior, para saber qué modelo corre y poder revertir. | RF-29 RNF-20 | MLflow / Ollama | PF-26 | E-15 E-16 |
| HU-18 | Como operador de la plataforma, quiero recrear la infraestructura desde código y detectar cambios hechos a mano, para reconstruir el laboratorio y mantener lo declarado igual a lo desplegado. | RNF-02 RNF-04 RNF-08 RNF-16 | OpenTofu / Argo CD / Gitea (hub-gitops) | PF-23 PF-25 | E-08 E-09 E-24 |
| HU-19 | Como operador de la plataforma, quiero respaldar la base del Hub cada día y restaurarla, para no perder datos ante una falla. | RNF-13 | PostgreSQL / CronJob de respaldo |  | E-25 |
| HU-20 | Como administrador de la agencia, quiero que ningún dato de clientes salga a una IA externa, para cumplir la protección de datos personales. | RNF-01 RNF-03 RNF-09 RNF-18 | Hub API / Políticas de red / Ollama | PF-22 PF-23 | E-14 E-19 E-27 |
| HU-21 | Como operador de la plataforma, quiero que la API tenga límites de tiempo y de tamaño y siga viva si falla una integración, para que una petición lenta o la caída de la IA, la voz o el monitoreo no tumbe el Hub. | RNF-12 RNF-14 RNF-21 | Hub API | PF-24 | E-03 E-26 |
| HU-22 | Como operador de la plataforma, quiero que cada cambio pase lint, pruebas y escaneo de secretos antes de integrarse, para mantener la calidad y no filtrar secretos. | RNF-06 RNF-15 | CI de GitHub / Gitleaks | PF-23 | E-01 E-02 E-03 E-05 |
| HU-23 | Como cliente pyme, quiero usar una interfaz en español, con tema claro u oscuro y estados con texto e ícono, para entender la pantalla sin depender del color. | RNF-17 | Consola web / Portal del cliente |  | E-22 |

::: {custom-style="Nota"}
*Nota.* Elaboración propia a partir de `entrega/datos/historias.csv` y `entrega/datos/trazabilidad.csv`. Las pruebas y evidencias de cada historia son las de los requisitos que cubre.
:::

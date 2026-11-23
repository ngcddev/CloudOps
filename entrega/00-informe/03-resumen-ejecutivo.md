<!-- Sección 3 · Resumen ejecutivo APA: un solo bloque, sin sangría, más palabras clave. Las cifras salen de las secciones técnicas y se revisan al entregar (corte del 16 nov 2026). -->

# Resumen ejecutivo

::: {custom-style="Abstract"}
Las agencias web pequeñas de Popayán atienden a pequeñas y medianas empresas con un soporte reactivo: las solicitudes llegan por WhatsApp, correo y teléfono, la prioridad depende de cada técnico, las caídas se conocen cuando el cliente llama y el cliente casi no ve qué se hace. CloudOps Client Hub es un centro de operación de servicios digitales que responde a ese problema: gestiona clientes, planes, solicitudes, cambios, despliegues, monitoreo, incidentes, recuperación, acuerdos de nivel de servicio y reportes, y ofrece al cliente un portal en lenguaje de negocio. Se construyó como proyecto integrador del diplomado CloudForge AI 5.0 de Unicomfacauca, en nueve semanas y con un equipo de cinco personas, sobre infraestructura propia, sin servicios externos y con datos sintéticos. Cada cliente corre aislado en su espacio de nombres de Kubernetes; los cambios se publican como commits que Argo CD aplica; una puerta de seguridad bloquea secretos, vulnerabilidades críticas y firmas inválidas antes de publicar; y la observabilidad con Prometheus, Loki, Tempo y Grafana detecta una caída en un minuto o menos, abre el incidente con su SLA y permite el rollback, con un tiempo de recuperación medido de 1,3 a 1,5 minutos en el caso del restaurante. Un asistente de inteligencia artificial local (Qwen2.5 7B con una compuerta de aprendizaje automático y un RAG propio) ayuda a la agencia, redacta borradores que una persona aprueba y acepta la voz como modalidad adicional. De los 50 requisitos del proyecto (29 funcionales y 21 no funcionales), 42 están cumplidos, 5 parciales, 1 sin verificar, 1 diferido y 1 fuera de alcance; 1.134 pruebas automatizadas del backend, 40 de la capa de IA y 28 decisiones de arquitectura respaldan el resultado. La IA resistió 9 de 10 intentos de inyección y 5 de 5 documentos maliciosos, y respondió bien el 95 % al 100 % de las preguntas de evaluación. Los límites son claros: un solo nodo sin alta disponibilidad, voz probada con micrófono falso y sin voz humana, módulo de IA multimodal cubierto solo con audio, y una ayuda del asistente que hay que actualizar. Se recomienda cerrar esos límites, probar la voz con una persona real, confirmar con el docente la modalidad del módulo 6 y definir una política de retención antes de usar datos reales.
:::

::: {custom-style="Abstract"}
*Palabras clave:* computación nativa en la nube, GitOps, DevSecOps, observabilidad, inteligencia artificial local, generación aumentada por recuperación, agencias web, Popayán
:::

## Problema, solución y beneficiarios

El **problema** es el soporte reactivo y sin datos de las agencias web que atienden PyMEs. La **solución** es un Hub con dos tipos de usuario: la agencia, que ve todo, y el cliente, que ve solo lo suyo y sin jerga. Los **beneficiarios** son la agencia (organiza, mide y explica su servicio), el cliente PyME (sabe el estado de su sitio y de sus solicitudes) y, en el diseño, los titulares de los datos, cuyos datos no salen del laboratorio.

## Resultados principales

::: {custom-style="Table Caption"}
**Tabla {T:resultados}**\
*Resultados principales del proyecto (corte del 16 de noviembre de 2026)*
:::

| Resultado | Cifra | Fuente |
|-----------------------|--------------------|----------------------|
| Requisitos cumplidos | 42 de 50 (25 de 29 funcionales y 17 de 21 no funcionales) | Matriz de trazabilidad |
| Pruebas automatizadas | 1.134 del backend y 40 de la capa de IA; 26 pruebas funcionales agrupadas, todas en verde | Sección de pruebas funcionales |
| Despliegue por GitOps | 9 aplicaciones de Argo CD sincronizadas y sanas | Sección de GitOps |
| Detección de una caída | 60 segundos o menos | Sección de observabilidad |
| Tiempo de recuperación (caso del restaurante) | 1,3 a 1,5 minutos | Sección de GitOps y `docs/bitacora.md` |
| Seguridad de la entrega | Puerta con 6 controles; versiones con secretos o sin firma no se pueden aprobar | Sección de pipeline |
| Seguridad de la IA | 9 de 10 inyecciones y 5 de 5 documentos maliciosos resistidos | Sección de validación de IA |
| Calidad del asistente | 95 % a 100 % de acierto en las preguntas de evaluación | Sección de MLOps |
| Decisiones de arquitectura | 28, cada una con su evidencia | Sección de decisiones |

::: {custom-style="Nota"}
*Nota.* Elaboración propia a partir de las secciones técnicas de este informe.
:::

## Valor de cloud native y de la IA local

El enfoque cloud native da reproducibilidad (todo se reconstruye desde código), trazabilidad (cada despliegue y cada rollback son commits) y aislamiento y seguridad por defecto. La IA local permite usar el asistente con datos de incidentes y clientes sin enviarlos a un servicio externo, funciona sin conexión y no depende de un costo por uso; además, toda salida de la IA es un borrador que una persona aprueba.

## Recomendaciones

1. Probar la voz con una persona real y un micrófono (hoy solo hay prueba con micrófono falso).
2. Confirmar por escrito con el docente que el audio cubre el módulo 6 o planificar una modalidad de imagen.
3. Actualizar la ayuda del Hub: afirma que los reportes no existen y el asistente lo repite.
4. Definir una política de retención y supresión para las preguntas al asistente y los textos libres antes de usar datos reales.
5. Ensayar tres veces la demostración y grabar el video de respaldo.
6. Cerrar los límites declarados: alta de usuarios desde la aplicación, `tofu plan` contra el clúster real y una prueba de usabilidad del portal con tres personas.

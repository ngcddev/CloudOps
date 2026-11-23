<!-- GENERADA por entrega/generar_tablas.py a partir de entrega/datos/pruebas.csv. No editar a mano. -->

# Pruebas funcionales

Las 26 pruebas funcionales (PF) agrupan los archivos de pruebas automatizadas que verifican cada requerimiento. Los resultados se obtuvieron el 16 de noviembre de 2026 ejecutando `python entrega/ejecutar_pruebas.py`, que corre `pytest` dentro del contenedor de la API para PF-01 a PF-25; PF-26 corresponde a las pruebas de `ai/` y se ejecutó con `cd ai && pytest` en un entorno aparte. La suma de pruebas ejecutadas en la Tabla {T:pf} es 956; las pruebas que pertenecen a varias PF no se cuentan dos veces en la suite completa (1.134 recogidas en el backend).

**Condición de ejecución.** El entorno local define `ASSISTANT_CONTEXT_MODE=rag`, y seis pruebas del asistente suponen el modo por defecto (`completo`): con el entorno local fallan, con el valor por defecto pasan. La CI de GitHub no define esa variable, por lo que no se ve afectada. Para reproducir las condiciones de la CI, el script fija `ASSISTANT_CONTEXT_MODE=completo`. Es una debilidad de aislamiento de las pruebas (leen el entorno del proceso), no un defecto del producto, y queda anotada como mejora.

::: {custom-style="Table Caption"}
**Tabla {T:pf}**\
*Pruebas funcionales: entrada, resultado esperado y resultado obtenido*
:::

| ID | Caso | Requisitos | Entrada | Resultado esperado | Resultado obtenido | Estado |
|------|----------------|---------|--------------------|----------------------|--------------|--------|
| PF-01 | Inicio de sesión, roles y aislamiento por cliente | RF-01 | Peticiones sin sesión y con la sesión de un cliente a rutas de otro cliente y de agencia | Sin sesión responde 401. El cliente no ve datos ajenos ni ejecuta acciones de agencia | 104 pasaron, 3 omitidas (16/11/2026) | Cumplido |
| PF-02 | Clientes, proyectos, servicios y planes | RF-02 RNF-11 | Alta y edición de clientes, proyectos y servicios, con y sin plan o nombre | Se crea y se edita. Sin plan o sin nombre rechaza con un mensaje en español | 42 pasaron (16/11/2026) | Cumplido |
| PF-03 | Ciclo de vida de la solicitud | RF-04 | Un cliente crea una solicitud y la agencia la asigna y la mueve de estado | Solo pasan las transiciones permitidas y cada cambio queda en el historial con hora y autor | 20 pasaron (16/11/2026) | Cumplido |
| PF-04 | Clasificación de prioridad P1 a P4 | RF-05 | Impacto y urgencia de la matriz del servicio | La prioridad asignada coincide con la matriz sembrada | 16 pasaron (16/11/2026) | Cumplido |
| PF-05 | Aprobación de un cambio y publicación por GitOps | RF-06 | Aprobar una solicitud de cambio con la puerta en verde | Se cambia solo la línea de versión en el repositorio de configuración y la solicitud avanza de estado | 86 pasaron, 1 omitidas (16/11/2026) | Cumplido |
| PF-06 | Versión y estado por cliente | RF-07 | Consulta del estado de los servicios con Argo CD simulado | Cada servicio informa versión activa, estado de sincronización y último cambio | 49 pasaron (16/11/2026) | Cumplido |
| PF-07 | Recepción de los controles de la puerta de seguridad | RF-08 | Eventos del pipeline con pasos aprobados y fallidos | Cada control queda registrado con su resultado y su evidencia | 50 pasaron (16/11/2026) | Cumplido |
| PF-08 | Bloqueo por seguridad y motivo visible | RF-09 | Aprobar una versión sin firma, con secreto o sin corrida terminada | La aprobación se rechaza y se explica el motivo | 21 pasaron (16/11/2026) | Cumplido |
| PF-09 | Auditoría de acciones | RF-10 | Acciones de agencia y consulta de la bitácora | Cada acción queda con usuario, objeto y hora. La API solo expone lectura | 12 pasaron (16/11/2026) | Cumplido |
| PF-10 | De la alerta al incidente | RF-11 RF-12 RNF-07 | Alertas de Alertmanager reales y repetidas | Se abre un incidente P1 con la hora real de la caída y sin duplicados | 28 pasaron (16/11/2026) | Cumplido |
| PF-11 | Ciclo del incidente y SLA | RF-13 | Tomar, anotar, mitigar y cerrar un incidente | El reloj corre con hora real y solo se cierra desde mitigado con causa raíz | 46 pasaron (16/11/2026) | Cumplido |
| PF-12 | Rollback | RF-14 | Rollback desde un incidente con Gitea y Argo CD simulados | Se escribe el commit de reversión y el incidente pasa a mitigado con su MTTR. No hay dos rollbacks a la vez | 40 pasaron (16/11/2026) | Cumplido |
| PF-13 | Tableros, portal y KPI | RF-15 RF-16 RF-17 | Consulta de los tableros de la agencia y del portal con datos sembrados | Las cifras coinciden con las fórmulas de KPI y el cliente solo ve lo suyo | 34 pasaron (16/11/2026) | Cumplido |
| PF-14 | Borradores de IA y mensaje al cliente | RF-18 RF-19 | Generar borradores con la IA local simulada y con la IA caída | Quedan como borrador hasta su aprobación, sin términos prohibidos, y con un texto base si la IA falla | 42 pasaron (16/11/2026) | Cumplido |
| PF-15 | Reportes operativo y ejecutivo | RF-20 | Generar ambos reportes de un mes | El PDF se genera, las cifras coinciden con los tableros y el ejecutivo cabe en una página | 27 pasaron (16/11/2026) | Cumplido |
| PF-16 | Asistente con compuerta de ML | RF-25 | Preguntas del tema y ajenas al tema | La pregunta del tema despierta al LLM y la ajena recibe la respuesta fija | 24 pasaron (16/11/2026) | Cumplido |
| PF-17 | RAG de la ayuda del Hub | RF-28 | Indexar la ayuda y preguntar en modo rag, con concurrencia | Se recuperan los trozos más parecidos y se registran las secciones usadas | 28 pasaron, 1 omitidas (16/11/2026) | Cumplido |
| PF-18 | Voz del asistente | RF-27 | Transcribir audio, corregir y reproducir la respuesta con el servicio de voz simulado | La voz no bloquea al Hub y el audio no se guarda | 29 pasaron (16/11/2026) | Cumplido |
| PF-19 | Diagnóstico de incidente con IA | RF-23 | Diagnóstico con evidencia y con citas inventadas | Se rechazan las citas que no existen en la evidencia | 18 pasaron (16/11/2026) | Cumplido |
| PF-20 | Alta de un sitio nuevo por GitOps | RF-26 | Registrar un servicio y provisionarlo | Se crea la carpeta en el repositorio de configuración sin tocar Kubernetes | 40 pasaron (16/11/2026) | Cumplido |
| PF-21 | Catálogo de Backstage | RF-22 | Validar la configuración, la plantilla y el catálogo | La plantilla y el catálogo son válidos y coinciden con los clientes | 17 pasaron (16/11/2026) | Cumplido |
| PF-22 | Seguridad de la IA: redacción e inyección de instrucciones | RNF-09 RNF-18 | Textos con claves, certificados y órdenes escondidas | Las claves se redactan antes del modelo y las órdenes escondidas no se obedecen | 46 pasaron (16/11/2026) | Cumplido |
| PF-23 | Red y contenedores restringidos | RF-03 RNF-01 RNF-02 RNF-03 RNF-05 RNF-06 | Manifiestos de red, contenedores y composición | Salida y entrada denegadas por defecto, sin root, con raíz de solo lectura y sin secretos en Compose | 55 pasaron (16/11/2026) | Cumplido |
| PF-24 | Límites, pool y sonda de vida | RNF-12 RNF-14 RNF-21 | Cuerpos grandes, conexiones agotadas y base caída | Se rechazan los excesos y la sonda de vida no depende de la base | 23 pasaron (16/11/2026) | Cumplido |
| PF-25 | Helm equivale a Kustomize y migraciones | RNF-04 RNF-08 RNF-16 | Comparar el chart con el overlay y subir y bajar las migraciones | No hay diferencia entre chart y overlay y las migraciones suben y bajan | 19 pasaron (16/11/2026) | Cumplido |
| PF-26 | Registro y promoción de modelos, medición y tutor de IA | RF-29 RNF-20 | Registrar corridas en MLflow, promover con comparación y medir modelos con servidores simulados | La promoción compara contra producción y permite volver atrás. Las mediciones se registran | 40 pasaron (16/11/2026) | Cumplido |

::: {custom-style="Nota"}
*Nota.* Elaboración propia a partir de `entrega/datos/pruebas.csv`. El detalle de cada caso está en los archivos de `backend/tests/` y `ai/tests/` indicados en ese archivo. Las pruebas de plataforma que requieren el clúster (por ejemplo `gitops/pruebas/*.sh`) se citan como evidencia en el Apéndice A y no en esta tabla.
:::

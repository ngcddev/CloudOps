<!-- Sección 14 · Fuente: routers y servicios del backend (leídos el 16 nov 2026). Cada secuencia indica el archivo donde ocurre cada paso. -->
<!-- Generación multimodal = voz (única modalidad construida, ADR-25). Generación de código o documentación = borradores y diagnóstico de IA (el Hub no genera código con IA). -->

# Diagramas de secuencia

Se documentan cinco secuencias: la consulta al asistente con RAG, la generación de documentación con IA (borradores y diagnóstico de incidentes), la interacción por voz como modalidad multimodal, el despliegue por CI/CD y GitOps y la recuperación ante una falla. Cada secuencia lista sus pasos con el archivo donde ocurren, de modo que el diagrama se pueda dibujar y comprobar contra el código. El Hub no genera código con IA: la «generación de código o documentación» del plan se cubre con los borradores y el diagnóstico de incidentes.

## Consulta al asistente con RAG

Solo los usuarios de agencia usan el asistente (`require_agency` en `POST /api/assistant/ask`). La compuerta decide en milisegundos si la pregunta trata del Hub; el modelo de lenguaje solo se llama si sí, y Ollama puede tardar hasta 60 segundos sin que la API mantenga una conexión de base de datos tomada.

::: {custom-style="Image Caption"}
**Figura {F:sec-rag}**\
*Secuencia de la consulta al asistente con RAG*
:::

[FIGURA F-07 · Secuencia de la consulta al asistente · Participantes: persona de agencia, consola web, API del Hub, compuerta, base de conocimiento en PostgreSQL, Ollama y tabla ai_queries. Mensajes en orden: 1 la persona escribe la pregunta; 2 la consola envía POST ask con el token; 3 la API verifica el rol y tapa las claves de la pregunta; 4 la compuerta clasifica la pregunta y devuelve en_tema o fuera_de_tema; 5 si es ajena, la API responde con el texto fijo sin llamar al modelo y salta a 10; 6 en modo rag la API pide a Ollama el embedding de la pregunta; 7 la API compara con los 31 trozos por coseno y toma los más parecidos; 8 si la similitud del mejor es menor al umbral responde que no hay información; 9 la API suelta la conexión a la base y llama a Ollama chat con la ayuda recuperada, con tiempo máximo de 60 segundos y respuesta de aviso si falla; 10 la API guarda en ai_queries la pregunta, la decisión, el modo, la similitud y las secciones citadas, y devuelve la respuesta con sus fuentes. Un recuadro alternativo: si Ollama no da embeddings se cae a recuperación léxica]

::: {custom-style="Nota"}
*Nota.* Elaboración propia. Fuente: `backend/app/routers/assistant.py:38-45` y `backend/app/services/assistant.py:31-106`.
:::

Pasos y archivos:

1. La persona pregunta en la consola; `POST /api/assistant/ask` exige rol de agencia (`backend/app/routers/assistant.py:38`).
2. La API tapa claves, certificados y órdenes escondidas de la pregunta antes de cualquier otro paso (`backend/app/services/assistant.py:52`).
3. La compuerta decide si es del tema (`assistant.compuerta`, `backend/app/services/assistant.py:58-62`); si el clasificador fue alterado, la API responde 503 (`routers/assistant.py:41-45`).
4. Si es ajena, responde el texto fijo y no llama al modelo (`assistant.py:65-66`).
5. Si es del tema, arma el contexto según el modo: `rag` pide embeddings a Ollama y recupera los trozos más parecidos; si no puede, cae a recuperación léxica (`assistant.py:31-47`, `backend/app/services/knowledge.py:160`).
6. Si el modo no encuentra nada parecido, responde que no hay información sin llamar al modelo (`assistant.py:73-75`).
7. Suelta la conexión del pool y llama a Ollama con la ayuda recuperada y un tiempo máximo (`assistant.py:80-83`, `backend/app/integrations/ollama.py:45`).
8. Guarda el registro con decisión, modelo, versión del prompt, secciones y similitud (`assistant.py:89-106`).

## Generación de documentación con IA (borradores y diagnóstico)

Los borradores de un incidente mitigado y el diagnóstico con evidencia son los dos usos del modelo para producir texto operativo. Nada llega al cliente sin que una persona lo apruebe, y el texto de la IA se verifica antes de aceptarse.

::: {custom-style="Image Caption"}
**Figura {F:sec-borradores}**\
*Secuencia de generación y aprobación de borradores de IA*
:::

[FIGURA F-08 · Secuencia de borradores de IA · Participantes: técnico, consola web, API del Hub, servicio de redacción, Ollama, verificaciones y tabla ai_drafts. Mensajes en orden: 1 el técnico pulsa generar borradores en un incidente mitigado; 2 POST ai-drafts; 3 la API arma los hechos del incidente (causa, acción, horas) con las claves tapadas; 4 suelta la conexión a la base; 5 pide a Ollama el resumen técnico y el mensaje al cliente; 6 verifica el texto contra la lista de términos prohibidos y contra las horas reales del incidente; 7 alternativa: si la IA no respondió o el texto no pasa las verificaciones se usa un texto base determinista y se anota el motivo; 8 guarda los borradores como borrador_ia y descarta los pendientes anteriores; 9 el técnico edita y aprueba; 10 la API vuelve a verificar el mensaje al cliente y, si pasa, lo marca aprobado con el nombre de quien lo aprobó; 11 solo entonces el mensaje es visible para el cliente. Variante: el diagnóstico POST ai-diagnosis usa la misma estructura con evidencia numerada y rechaza citas que no existan]

::: {custom-style="Nota"}
*Nota.* Elaboración propia. Fuente: `backend/app/services/ai_drafts.py:182-256` y `backend/app/services/aiops.py`.
:::

Pasos y archivos:

1. `POST /api/incidents/{id}/ai-drafts` genera los borradores (`backend/app/routers/ai_drafts.py:61`).
2. Se arman los hechos del incidente con textos redactados (`backend/app/services/ai_drafts.py:94-97`).
3. Se suelta la conexión a la base y se llama a Ollama una vez por tipo de borrador (`ai_drafts.py:207-208`).
4. Se verifican términos prohibidos y horas que no coinciden; si no pasa o la IA falla, se usa el texto base (`ai_drafts.py:182-199`).
5. Se guardan como `borrador_ia` y los anteriores sin aprobar se descartan (`ai_drafts.py:202-224`).
6. La aprobación repite la verificación del mensaje al cliente y registra quién aprobó (`ai_drafts.py:226-250`, `routers/ai_drafts.py:91`).

## Interacción por voz (modalidad multimodal)

La voz agrega audio al mismo asistente: se transcribe el audio, la persona revisa el texto, lo envía como una pregunta normal y puede escuchar la respuesta. El audio no se guarda.

::: {custom-style="Image Caption"}
**Figura {F:sec-voz}**\
*Secuencia de la interacción por voz*
:::

[FIGURA F-09 · Secuencia de voz · Participantes: persona de agencia, navegador, API del Hub, servicio de voz y asistente. Mensajes en orden: 1 la persona pulsa Hablar y el navegador graba el micrófono; 2 al pulsar Detener el navegador envía el audio con POST voice transcribe, con tope de 2 000 000 bytes; 3 la API llama al servicio de voz en un hilo aparte para no bloquear la API; 4 faster-whisper small transcribe en CPU; 5 la API tapa claves en el texto y lo devuelve; 6 la persona corrige lo entendido y lo envía como pregunta, que sigue la secuencia de consulta al asistente; 7 la persona pulsa escuchar; 8 la API tapa claves y pide a Piper la síntesis; 9 el navegador reproduce el audio WAV. Nota: el audio no se guarda en ninguna parte]

::: {custom-style="Nota"}
*Nota.* Elaboración propia. Fuente: `backend/app/routers/assistant.py:84-118`, `backend/app/integrations/voz.py` y `voz/`.
:::

Pasos y archivos:

1. La consola muestra el micrófono solo si el servicio de voz responde (`GET /api/assistant/voice/status`, `routers/assistant.py:87`).
2. El audio llega a `POST /api/assistant/voice/transcribe`, con tope de tamaño (`routers/assistant.py:93-103`).
3. La transcripción corre en un hilo para no congelar la API (`routers/assistant.py:104`).
4. El texto se devuelve con las claves tapadas y no se envía como pregunta: la persona lo revisa (`routers/assistant.py:107-110`).
5. La respuesta se lee con `POST /api/assistant/voice/speak`, que tapa claves antes de sintetizar (`routers/assistant.py:113-118`).

## Despliegue por CI/CD y GitOps

Un cambio de versión de un sitio pasa por la puerta de seguridad, se aprueba por otra persona, se publica como un commit y lo aplica Argo CD; el Hub confirma la publicación leyendo Argo CD.

::: {custom-style="Image Caption"}
**Figura {F:sec-gitops}**\
*Secuencia de despliegue por CI/CD y GitOps*
:::

[FIGURA F-10 · Secuencia de despliegue por CI/CD y GitOps · Participantes: desarrollador, repositorio del sitio en Gitea, ejecutor de Gitea Actions, API del Hub, técnico solicitante, técnico aprobador, repositorio hub-gitops, Argo CD y clúster. Mensajes en orden: 1 el desarrollador sube una etiqueta de versión; 2 el ejecutor corre la puerta: Gitleaks, pruebas y construcción, Trivy, Syft y firma con Cosign, y envía cada control a POST pipeline-events con el token de máquina; 3 un fallo cierra la corrida como fallo y la versión no se puede aprobar; 4 el solicitante crea la solicitud de cambio; 5 el aprobador pide aprobar; 6 la API rechaza si el aprobador es quien pidió el cambio o si los controles de la versión no pasaron; 7 la API escribe en hub-gitops solo la línea de la etiqueta de imagen del sitio; 8 el cambio queda en estado en_validacion; 9 Argo CD detecta el commit, sincroniza y aplica en el espacio del cliente; 10 el vigilante del Hub consulta a Argo CD y confirma que ya aplicó ese commit; 11 el cambio pasa a desplegada y se registra el despliegue]

::: {custom-style="Nota"}
*Nota.* Elaboración propia. Fuente: `backend/app/routers/pipeline.py:30-61`, `backend/app/routers/change_requests.py:161-243` y `backend/app/services/deploy_watch.py`.
:::

Pasos y archivos:

1. La puerta registra cada control: `POST /api/pipeline-events` (`backend/app/routers/pipeline.py:30-61`) con `require_pipeline`.
2. Al aprobar, se rechaza si quien aprueba pidió el cambio (`change_requests.py:181`) o si la puerta no está en verde (`change_requests.py:193-195`).
3. La API escribe la etiqueta en `hub-gitops` y suelta la conexión mientras espera a Gitea (`change_requests.py:204-219`, `backend/app/services/gitops_publish.py`).
4. Con la fila bloqueada, pasa el cambio a `aprobada` y `en_validacion` y guarda el commit (`change_requests.py:220-241`).
5. El vigilante consulta a Argo CD y confirma la publicación (`backend/app/services/deploy_watch.py`).

## Recuperación ante una falla

Es el caso del restaurante: una versión rota cae, el monitoreo abre un incidente por sí solo, el técnico hace rollback y el sitio se recupera.

::: {custom-style="Image Caption"}
**Figura {F:sec-recuperacion}**\
*Secuencia de detección, rollback y recuperación*
:::

[FIGURA F-11 · Secuencia de recuperación ante una falla · Participantes: sitio del cliente, Blackbox Exporter, Prometheus, Alertmanager, API del Hub, técnico, repositorio hub-gitops, Argo CD y cliente. Mensajes en orden: 1 Blackbox sondea el sitio cada 5 segundos y falla; 2 Prometheus espera 30 segundos sostenidos y dispara SitioCaido con prioridad P1; 3 Alertmanager llama al webhook del Hub; 4 la API abre el incidente P1 con hora de inicio igual al aviso menos 30 segundos, el plazo del SLA según el plan, y marca el servicio como caido; 5 avisos repetidos con la misma huella no crean otro incidente; 6 el técnico toma el incidente y revisa alertas, registros y último cambio; 7 el técnico pide rollback; 8 la API escribe en hub-gitops un commit que restaura la etiqueta estable; 9 Argo CD sincroniza y el sitio vuelve a responder; 10 Prometheus resuelve la alerta y Alertmanager notifica; 11 la API mitiga el incidente con la hora real de recuperación, calcula el tiempo de recuperación y deja el servicio operativo; 12 el técnico aprueba el mensaje al cliente y cierra el incidente con la causa raíz]

::: {custom-style="Nota"}
*Nota.* Elaboración propia. Fuente: `backend/app/services/incident_alerts.py:35-120`, `backend/app/routers/incidents.py:231-294` y `observability/prometheus/reglas/sitios.yml`.
:::

Pasos y archivos:

1. `SitioCaido` se dispara tras 30 s de sondeos fallidos (`observability/prometheus/reglas/sitios.yml:9-11`).
2. El webhook abre el incidente con la hora real de la caída, evita duplicados por huella y marca el servicio `caido` (`backend/app/services/incident_alerts.py:35-83`).
3. El rollback se pide con `POST /api/incidents/{id}/rollback`: bloquea la fila, calcula la versión estable y escribe el commit en `hub-gitops` (`backend/app/routers/incidents.py:231-286`).
4. Si había un cambio en validación hacia la versión rota, queda como fallido (`incidents.py:287`, `backend/app/services/rollback.py`).
5. Cuando Prometheus resuelve la alerta, el Hub mitiga el incidente con la hora de recuperación y vuelve el servicio a `operativo` (`incident_alerts.py:89-120`).
6. En el caso del restaurante medido el 14 de noviembre de 2026 el MTTR fue de 1,3 a 1,5 minutos (`docs/bitacora.md:441,493`).

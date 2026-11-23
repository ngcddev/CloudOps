<!-- Sección 13 · Fuente: backend/app/models/ y backend/alembic/versions/ (0001 a 0017). El diccionario y la lista de datos personales se GENERAN de los modelos reales: no editar entre los marcadores. -->

# Modelo de datos

La base de datos del Hub es PostgreSQL 16 y tiene 22 tablas, creadas y modificadas por 17 migraciones de Alembic. Los datos que contiene en el laboratorio son sintéticos: la agencia, los clientes, los usuarios y los incidentes son ficticios y no se cargó ningún dato personal real (ver el marco normativo). Las fechas se guardan en UTC y se muestran en America/Bogotá en la interfaz.

## Diagrama entidad-relación

::: {custom-style="Image Caption"}
**Figura {F:er}**\
*Diagrama entidad-relación del Hub*
:::

[FIGURA F-06 · Entidad-relación del Hub · 22 entidades en cuatro zonas. Zona de negocio: agencies 1 a N clients, clients 1 a N projects, projects 1 a N services, plans 1 a N services, clients 1 a N users (opcional). Zona de mesa de servicio: services 1 a N tickets, tickets 1 a N ticket_events, tickets 1 a N work_logs, tickets 1 a N change_requests, services 1 a N change_requests, services 1 a N deployments, sla_policies como catálogo por prioridad sin llave foránea. Zona de incidentes y seguridad: services 1 a N incidents, incidents 1 a N incident_events, incidents 1 a N ai_drafts, services 1 a N security_runs, security_runs 1 a N security_checks. Zona transversal y de IA: users 1 a N audit_logs (opcional), users 1 a N ai_queries, clients 1 a N reports (opcional), kb_documents 1 a N kb_chunks. Mostrar llaves primarias y foráneas y marcar con un símbolo las columnas con datos personales]

::: {custom-style="Nota"}
*Nota.* Elaboración propia a partir de `backend/app/models/`.
:::

## Entidades y cardinalidades

::: {custom-style="Table Caption"}
**Tabla {T:entidades}**\
*Entidades del modelo, propósito y relaciones*
:::

| Entidad (tabla) | Propósito | Relaciones y cardinalidad |
|----------|---------------------|------------------------------|
| `agencies` | Agencia que presta el servicio | 1 agencia tiene N clientes |
| `clients` | Negocios clientes y su contacto | N a 1 con agencia; 1 cliente tiene N proyectos, N usuarios y N reportes |
| `projects` | Agrupación de servicios de un cliente | N a 1 con cliente; 1 proyecto tiene N servicios |
| `plans` | Catálogo de planes con SLO, cuotas y precio | 1 plan tiene N servicios |
| `services` | Sitio desplegado de un cliente (host, namespace, versión y estado) | N a 1 con proyecto y con plan; 1 servicio tiene N despliegues, solicitudes, cambios, incidentes y corridas de seguridad |
| `users` | Personas con acceso y su rol | N a 1 opcional con cliente (los de agencia no tienen cliente) |
| `tickets` | Solicitudes de los clientes | N a 1 con servicio; 1 solicitud tiene N eventos, N registros de horas y N cambios |
| `ticket_events` | Historial de estados, prioridad, responsable y notas | N a 1 con solicitud |
| `work_logs` | Horas trabajadas por solicitud | N a 1 con solicitud y con usuario |
| `change_requests` | Solicitudes de cambio de versión | N a 1 con solicitud y con servicio; índice único parcial: un cambio en curso por servicio |
| `deployments` | Versiones publicadas de un servicio | N a 1 con servicio |
| `incidents` | Fallas con su SLA, causa raíz y rollback | N a 1 con servicio; 1 incidente tiene N eventos y N borradores; índice único de la huella entre los abiertos |
| `incident_events` | Línea de tiempo del incidente | N a 1 con incidente |
| `sla_policies` | Tiempos de respuesta y solución por prioridad | Catálogo; se relaciona con tickets e incidentes por el texto de la prioridad, sin llave foránea |
| `security_runs` | Corrida de la puerta de seguridad de una versión | N a 1 con servicio; 1 corrida tiene N controles |
| `security_checks` | Resultado de cada control y su reporte | N a 1 con corrida; único por corrida, paso e imagen |
| `reports` | Reportes operativo y ejecutivo congelados | N a 1 opcional con cliente |
| `audit_logs` | Bitácora de acciones | N a 1 opcional con usuario (nulo = sistema); solo lectura desde la aplicación |
| `ai_queries` | Preguntas al asistente y cómo se respondieron | N a 1 con usuario |
| `ai_drafts` | Borradores de IA de un incidente y su aprobación | N a 1 con incidente y, al aprobar, con usuario |
| `kb_documents` | Documentos fuente del RAG | 1 documento tiene N trozos |
| `kb_chunks` | Trozos de la ayuda con su embedding | N a 1 con documento; único por documento y posición |

::: {custom-style="Nota"}
*Nota.* Elaboración propia a partir de `backend/app/models/` y de las migraciones 0001 a 0017.
:::

## Datos personales y sensibles

El Hub guarda datos personales de dos tipos de titulares: las personas que usan el sistema (agencia y clientes) y los contactos de los negocios clientes. No está previsto que guarde datos sensibles en el sentido de la Ley 1581 de 2012 (salud, origen, orientación, datos biométricos o de menores); el texto libre de solicitudes, incidentes y preguntas al asistente puede contener datos personales que alguien escriba, por lo que se clasifica como «posible».

<!-- PERSONALES:inicio -->
::: {custom-style="Table Caption"}
**Tabla {T:personales}**\
*Columnas con datos personales o que pueden contenerlos*
:::

| Columna | Clasificación | Titular | Descripción |
|------------------|--------------|--------------------|----------------------------------------|
| `ai_drafts.generated_text` | Posible (texto libre) | Quien escriba el texto | Texto generado, tal como salió |
| `ai_drafts.final_text` | Posible (texto libre) | Quien escriba el texto | Texto que la persona aprobó (editado); nulo mientras no se aprueba |
| `ai_queries.question` | Posible (texto libre) | Quien escriba el texto | Pregunta hecha al asistente, con las claves ya tapadas |
| `ai_queries.answer` | Posible (texto libre) | Quien escriba el texto | Respuesta mostrada a la persona |
| `audit_logs.details` | Posible | Personas usuarias del Hub | Datos de la acción (por ejemplo versión de origen y de destino) |
| `audit_logs.ip` | Personal (dirección IP) | Personas usuarias del Hub | Dirección IP desde la que se hizo la petición |
| `clients.contact_name` | Personal | Contactos de los negocios clientes | Persona de contacto del cliente |
| `clients.email` | Personal | Contactos de los negocios clientes | Correo de contacto |
| `clients.phone` | Personal | Contactos de los negocios clientes | Teléfono de contacto |
| `incident_events.message` | Posible (texto libre) | Quien escriba el texto | Texto del evento (línea de tiempo) |
| `incidents.title` | Posible (texto libre) | Quien escriba el texto | Título del incidente |
| `incidents.root_cause` | Posible (texto libre) | Quien escriba el texto | Causa raíz, obligatoria para cerrar |
| `ticket_events.note` | Posible (texto libre) | Quien escriba el texto | Nota del evento |
| `tickets.title` | Posible (texto libre) | Quien escriba el texto | Título de la solicitud |
| `tickets.description` | Posible (texto libre) | Quien escriba el texto | Descripción escrita por quien la crea |
| `users.name` | Personal | Personas usuarias del Hub (agencia y clientes) | Nombre de la persona |
| `users.email` | Personal | Personas usuarias del Hub (agencia y clientes) | Correo (único sin distinguir mayúsculas); es el usuario de inicio de sesión |
| `users.password_hash` | Credencial | Personas usuarias del Hub (agencia y clientes) | Contraseña con hash bcrypt; nunca se guarda en claro |
| `users.last_login_at` | Personal (actividad) | Personas usuarias del Hub (agencia y clientes) | Último inicio de sesión |
| `work_logs.hours` | Personal (actividad laboral) | Técnicos de la agencia | Horas trabajadas |
| `work_logs.note` | Posible (texto libre) | Técnicos de la agencia | Nota de lo realizado |

::: {custom-style="Nota"}
*Nota.* Elaboración propia a partir de `entrega/datos/diccionario.csv`. «Posible» indica texto libre o detalles que podrían incluir datos personales; en el laboratorio todos los datos son sintéticos.
:::

<!-- PERSONALES:fin -->

### Medidas de protección

::: {custom-style="Table Caption"}
**Tabla {T:proteccion}**\
*Medidas de protección de los datos y dónde están*
:::

| Riesgo | Medida | Evidencia |
|----------|-------------------------------|---------------------|
| Contraseñas expuestas | Hash bcrypt con 12 rondas; nunca en claro; la clave de firma del token se rechaza si es corta o es la del ejemplo | `backend/app/services/auth.py:20`, `backend/app/config.py:94` |
| Suplantación de sesión | Token JWT firmado (HS256) con vencimiento de 60 minutos y sub obligatorio | `backend/app/services/auth.py:10-11,41,49` |
| Acceso a datos de otro cliente | Un usuario `cliente` solo ve datos de su cliente; las acciones de agencia exigen el rol | `backend/app/deps.py:42`, `backend/tests/test_acceso_clientes.py` |
| Claves en preguntas o textos | Las claves, certificados y órdenes escondidas se tapan antes de guardar y antes de llegar al modelo | `backend/app/services/redaccion.py`, `backend/app/services/assistant.py:52` |
| Datos de clientes hacia IA externa | Solo existen las direcciones de Ollama y del servicio de voz; red de salida denegada por defecto | `backend/app/config.py:44,51`, `gitops/hub/networkpolicy.yaml` |
| Texto de usuarios en telemetría | Los spans no llevan preguntas ni respuestas | `backend/app/telemetry.py:1-5` |
| Manipulación de la bitácora | La API solo expone lectura | `backend/app/routers/audit_logs.py` |
| Pérdida de datos | Respaldo diario de PostgreSQL con restauración probada | `gitops/hub/backup.yaml`, `gitops/hub/respaldo/` |
| Tránsito sin cifrar | La entrada del Hub y de Backstage usa TLS con el certificado por defecto de Traefik (autofirmado en laboratorio) | `gitops/hub/ingress.yaml:38-42` |

::: {custom-style="Nota"}
*Nota.* Elaboración propia. El cifrado de la entrada en laboratorio usa un certificado autofirmado: no es adecuado para producción sin un certificado propio.
:::

### Tiempo de conservación

::: {custom-style="Table Caption"}
**Tabla {T:conservacion}**\
*Conservación de los datos*
:::

| Dato | Conservación | Dónde se fija |
|----------|----------------------|---------------------|
| Datos del Hub (clientes, solicitudes, incidentes, bitácora, preguntas al asistente) | Sin borrado automático: son del cliente y del servicio | `docs/operacion-responsable.md` |
| Respaldos de PostgreSQL | Un volcado diario a las 03:00 UTC; se conservan los 7 más recientes | `gitops/hub/backup.yaml:26,56`, `gitops/hub/respaldo/respaldar.sh:11` |
| Respaldos de Gitea y de Argo CD | Uno diario; se conservan los 5 más recientes | `gitops/platform/respaldo/gitea.yaml:51`, `gitops/platform/respaldo/argocd.yaml:81` |
| Métricas (Prometheus) | 30 días y 1 GB | `observability/prometheus/deployment.yaml` |
| Registros (Loki) | 72 horas, solo de los Pods de clientes | `observability/loki/loki.yaml` |
| Trazas (Tempo) | 24 horas | `observability/tempo/tempo.yaml` |

::: {custom-style="Nota"}
*Nota.* Elaboración propia. **Pendiente de decisión:** las preguntas al asistente (`ai_queries`) y los textos libres no tienen una política de borrado; si el Hub pasara a datos reales habría que fijar una (por ejemplo, 12 meses) y un procedimiento de supresión a solicitud del titular. `[COMPLETAR: confirmar la política de retención con el equipo]`
:::

## Almacenamiento del RAG

El asistente usa un índice de recuperación propio (ADR-19 y ADR-20). La ayuda del Hub (`backend/app/assets/ayuda_hub.md`) se divide en secciones; cada una es una fila de `kb_chunks` con su texto, el título de la sección (que se cita como fuente), un SHA-256 del contenido y su embedding. Los embeddings los calcula `nomic-embed-text` en Ollama y son vectores de 768 números guardados como `jsonb`. La tabla `kb_documents` registra el archivo fuente, el modelo de embeddings y el SHA-256 del contenido: si cualquiera cambia, el índice está vencido y se reindexa (`POST /api/assistant/reindex`). No se usa un índice vectorial aproximado: al ser 31 trozos, el coseno se calcula en Python sobre todos. Los documentos del índice son la ayuda pública del producto; no contienen datos de clientes.

## Diccionario de datos

El diccionario se genera de los modelos reales con `entrega/generar_diccionario.py`: los tipos, la nulabilidad y las relaciones salen del código y no se pueden desactualizar sin que el script falle. Contiene todas las columnas de las 22 tablas.

<!-- DICCIONARIO:inicio -->
::: {custom-style="Table Caption"}
**Tabla {T:diccionario}**\
*Diccionario de datos: tablas y columnas*
:::

| Tabla y columna | Tipo | Nulo | Relación | Descripción |
|----------------------|------------|-----|--------------|--------------------------------------------|
| `agencies.id` | integer | No | PK | Identificador |
| `agencies.name` | varchar(200) | No | — | Nombre de la agencia que presta el servicio (Forja Digital en los datos de ejemplo) |
| `agencies.created_at` | datetime | No | — | Fecha y hora de creación (UTC) |
| `ai_drafts.id` | integer | No | PK | Identificador |
| `ai_drafts.incident_id` | integer | No | FK → incidents | Incidente del que habla el borrador |
| `ai_drafts.kind` | varchar(20) | No | — | Tipo de borrador: resumen (técnico, para la agencia) o mensaje_cliente (sin jerga, para el portal) |
| `ai_drafts.status` | varchar(20) | No | — | Estado: borrador_ia, aprobado o descartado |
| `ai_drafts.source` | varchar(20) | No | — | Origen del texto: llm (lo redactó el modelo) o plantilla (texto base cuando la IA no respondió o no pasó las verificaciones) |
| `ai_drafts.model` | varchar(60) | Sí | — | Modelo que lo redactó; nulo si se usó la plantilla sin llamar a la IA |
| `ai_drafts.prompt_version` | varchar(30) | Sí | — | Versión de las instrucciones del modelo |
| `ai_drafts.generated_text` | text | No | — | Texto generado, tal como salió |
| `ai_drafts.final_text` | text | Sí | — | Texto que la persona aprobó (editado); nulo mientras no se aprueba |
| `ai_drafts.checks` | jsonb | Sí | — | Resultado de las verificaciones: términos prohibidos, horas que no coinciden y motivo de usar la plantilla |
| `ai_drafts.latency_ms` | integer | Sí | — | Tiempo que tardó el modelo, en milisegundos |
| `ai_drafts.approved_by_id` | integer | Sí | FK → users | Persona que aprobó el borrador |
| `ai_drafts.approved_at` | datetime | Sí | — | Fecha y hora de la aprobación |
| `ai_drafts.created_at` | datetime | No | — | Fecha y hora de creación (UTC) |
| `ai_queries.id` | integer | No | PK | Identificador |
| `ai_queries.user_id` | integer | No | FK → users | Persona que hizo la pregunta |
| `ai_queries.question` | text | No | — | Pregunta hecha al asistente, con las claves ya tapadas |
| `ai_queries.gate_label` | varchar(20) | No | — | Decisión de la compuerta: en_tema o fuera_de_tema |
| `ai_queries.p_fuera_de_tema` | float | No | — | Probabilidad de que la pregunta sea ajena al Hub, según la compuerta |
| `ai_queries.gate_version` | varchar(30) | No | — | Versión del clasificador de la compuerta |
| `ai_queries.llm_woken` | boolean | No | — | Si se llamó al modelo de lenguaje |
| `ai_queries.model` | varchar(60) | Sí | — | Modelo que respondió; nulo si no se llamó |
| `ai_queries.prompt_version` | varchar(30) | Sí | — | Versión de las instrucciones; nula si no se llamó al modelo |
| `ai_queries.llm_ok` | boolean | Sí | — | Si el modelo respondió a tiempo; nulo si no se llamó |
| `ai_queries.latency_ms` | integer | Sí | — | Tiempo de respuesta del modelo, en milisegundos |
| `ai_queries.answer` | text | No | — | Respuesta mostrada a la persona |
| `ai_queries.context_sections` | jsonb | Sí | — | Secciones de la ayuda usadas como contexto (trazabilidad de la respuesta) |
| `ai_queries.context_mode` | varchar(20) | Sí | — | Cómo se armó el contexto: completo, recuperacion o rag |
| `ai_queries.retrieval_score` | float | Sí | — | Similitud coseno del mejor trozo, en modo rag |
| `ai_queries.feedback_label` | varchar(20) | Sí | — | Lo que la persona dice que era la pregunta en realidad (en_tema o fuera_de_tema); nulo si no opinó |
| `ai_queries.created_at` | datetime | No | — | Fecha y hora de creación (UTC) |
| `audit_logs.id` | integer | No | PK | Identificador |
| `audit_logs.user_id` | integer | Sí | FK → users | Quién hizo la acción; nulo si la hizo el sistema |
| `audit_logs.action` | varchar(50) | No | — | Acción registrada (crear, aprobar, rollback, denegar...) |
| `audit_logs.entity` | varchar(50) | No | — | Tipo de objeto afectado (ticket, incident, change_request...) |
| `audit_logs.entity_id` | integer | Sí | — | Identificador del objeto afectado |
| `audit_logs.details` | jsonb | Sí | — | Datos de la acción (por ejemplo versión de origen y de destino) |
| `audit_logs.ip` | varchar(64) | Sí | — | Dirección IP desde la que se hizo la petición |
| `audit_logs.created_at` | datetime | No | — | Fecha y hora de creación (UTC) |
| `change_requests.id` | integer | No | PK | Identificador |
| `change_requests.ticket_id` | integer | No | FK → tickets | Solicitud que originó el cambio |
| `change_requests.service_id` | integer | No | FK → services | Servicio que cambia de versión |
| `change_requests.from_version` | varchar(50) | No | — | Versión actual al pedir el cambio |
| `change_requests.to_version` | varchar(50) | No | — | Versión que se quiere publicar |
| `change_requests.status` | varchar(30) | No | — | pendiente, aprobada, en_validacion, desplegada, fallida o rechazada |
| `change_requests.requested_by_id` | integer | Sí | FK → users | Quien pidió el cambio |
| `change_requests.approved_by_id` | integer | Sí | FK → users | Quien lo aprobó (distinto de quien lo pidió) |
| `change_requests.gitops_commit_sha` | varchar(64) | Sí | — | Commit escrito en hub-gitops al aprobar |
| `change_requests.rejection_reason` | text | Sí | — | Motivo del rechazo |
| `change_requests.created_at` | datetime | No | — | Fecha y hora de creación (UTC) |
| `change_requests.approved_at` | datetime | Sí | — | Fecha y hora de la aprobación |
| `change_requests.deployed_at` | datetime | Sí | — | Fecha y hora en que Argo CD confirmó la publicación |
| `clients.id` | integer | No | PK | Identificador |
| `clients.agency_id` | integer | Sí | FK → agencies | Agencia que atiende al cliente |
| `clients.name` | varchar(200) | No | — | Nombre del negocio cliente |
| `clients.contact_name` | varchar(200) | Sí | — | Persona de contacto del cliente |
| `clients.email` | varchar(200) | Sí | — | Correo de contacto |
| `clients.phone` | varchar(50) | Sí | — | Teléfono de contacto |
| `clients.created_at` | datetime | No | — | Fecha y hora de creación (UTC) |
| `clients.updated_at` | datetime | No | — | Fecha de la última modificación (UTC) |
| `deployments.id` | integer | No | PK | Identificador |
| `deployments.service_id` | integer | No | FK → services | Servicio desplegado |
| `deployments.version` | varchar(50) | No | — | Versión publicada |
| `deployments.commit_sha` | varchar(64) | Sí | — | Commit de hub-gitops que la publicó |
| `deployments.author` | varchar(200) | No | — | Nombre de quien autorizó la publicación |
| `deployments.source` | varchar(20) | No | — | cambio o rollback |
| `deployments.created_at` | datetime | No | — | Fecha y hora de creación (UTC) |
| `incident_events.id` | integer | No | PK | Identificador |
| `incident_events.incident_id` | integer | No | FK → incidents | Incidente al que pertenece el evento |
| `incident_events.type` | varchar(20) | No | — | detectado, tomado, nota, recuperado, cerrado, rollback_enviado, rollback_confirmado o mensaje_cliente |
| `incident_events.message` | text | Sí | — | Texto del evento (línea de tiempo) |
| `incident_events.actor_id` | integer | Sí | FK → users | Quien lo registró; nulo si fue el sistema |
| `incident_events.created_at` | datetime | No | — | Fecha y hora de creación (UTC) |
| `incidents.id` | integer | No | PK | Identificador |
| `incidents.service_id` | integer | No | FK → services | Servicio afectado |
| `incidents.priority` | varchar(2) | No | — | Prioridad P1 a P4 |
| `incidents.status` | varchar(20) | No | — | abierto, mitigado o cerrado |
| `incidents.source` | varchar(20) | No | — | alerta (lo abrió Alertmanager) o manual (lo abrió un técnico) |
| `incidents.fingerprint` | varchar(100) | Sí | — | Huella de la alerta en Alertmanager; nula en incidentes manuales. Es única entre los incidentes abiertos |
| `incidents.title` | varchar(200) | No | — | Título del incidente |
| `incidents.started_at` | datetime | No | — | Hora real en que empezó la falla (no la hora en que llegó el aviso) |
| `incidents.acknowledged_at` | datetime | Sí | — | Hora en que un técnico lo tomó |
| `incidents.mitigated_at` | datetime | Sí | — | Hora en que el servicio se recuperó |
| `incidents.closed_at` | datetime | Sí | — | Hora de cierre con causa raíz |
| `incidents.response_due_at` | datetime | No | — | Hora límite de respuesta según el SLA |
| `incidents.resolution_due_at` | datetime | No | — | Hora límite de solución según el SLA |
| `incidents.assignee_id` | integer | Sí | FK → users | Técnico responsable |
| `incidents.created_by_id` | integer | Sí | FK → users | Quien lo abrió; nulo si lo abrió el sistema |
| `incidents.root_cause` | text | Sí | — | Causa raíz, obligatoria para cerrar |
| `incidents.created_at` | datetime | No | — | Fecha y hora de creación (UTC) |
| `incidents.rollback_from_version` | varchar(50) | Sí | — | Versión rota de la que se vuelve |
| `incidents.rollback_to_version` | varchar(50) | Sí | — | Versión estable a la que se vuelve |
| `incidents.rollback_commit_sha` | varchar(64) | Sí | — | Commit del rollback en hub-gitops |
| `incidents.rollback_by_id` | integer | Sí | FK → users | Quien pidió el rollback |
| `incidents.rollback_at` | datetime | Sí | — | Hora en que se pidió el rollback |
| `incidents.rollback_confirmed_at` | datetime | Sí | — | Hora en que el monitoreo confirmó la recuperación |
| `kb_chunks.id` | integer | No | PK | Identificador |
| `kb_chunks.document_id` | integer | No | FK → kb_documents | Documento al que pertenece el trozo |
| `kb_chunks.section` | varchar(200) | No | — | Título de la sección de la ayuda (es lo que se cita como fuente) |
| `kb_chunks.position` | integer | No | — | Posición del trozo dentro del documento |
| `kb_chunks.text` | text | No | — | Texto del trozo |
| `kb_chunks.content_hash` | varchar(64) | No | — | SHA-256 del texto del trozo |
| `kb_chunks.embedding` | jsonb | No | — | Vector del trozo (768 números con nomic-embed-text); es el índice vectorial |
| `kb_documents.id` | integer | No | PK | Identificador |
| `kb_documents.source` | varchar(120) | No | — | Nombre del archivo fuente (por ejemplo ayuda_hub.md) |
| `kb_documents.content_hash` | varchar(64) | No | — | SHA-256 del contenido; si cambia, el índice está vencido |
| `kb_documents.embedding_model` | varchar(80) | No | — | Modelo con que se calcularon los embeddings |
| `kb_documents.chunk_count` | integer | No | — | Cantidad de trozos del documento |
| `kb_documents.indexed_at` | datetime | No | — | Fecha y hora de la indexación |
| `plans.id` | integer | No | PK | Identificador |
| `plans.code` | varchar(50) | No | — | Código del plan (basico, estandar, premium) |
| `plans.name` | varchar(100) | No | — | Nombre del plan |
| `plans.slo_availability` | numeric(5, 2) | No | — | Objetivo de disponibilidad mensual, en porcentaje |
| `plans.support_hours` | varchar(100) | No | — | Horario de atención |
| `plans.cpu_quota` | varchar(50) | No | — | Cuota de CPU del namespace del cliente |
| `plans.memory_quota` | varchar(50) | No | — | Cuota de memoria del namespace del cliente |
| `plans.monthly_price` | numeric(12, 2) | Sí | — | Precio mensual |
| `plans.included_hours` | numeric(8, 2) | Sí | — | Horas de soporte incluidas al mes |
| `projects.id` | integer | No | PK | Identificador |
| `projects.client_id` | integer | No | FK → clients | Cliente dueño del proyecto |
| `projects.name` | varchar(200) | No | — | Nombre del proyecto |
| `projects.description` | text | Sí | — | Descripción del proyecto |
| `projects.created_at` | datetime | No | — | Fecha y hora de creación (UTC) |
| `reports.id` | integer | No | PK | Identificador |
| `reports.kind` | varchar(20) | No | — | operativo (toda la agencia, uso interno) o ejecutivo (un cliente, sin jerga) |
| `reports.client_id` | integer | Sí | FK → clients | Cliente del reporte; nulo en el operativo |
| `reports.month` | varchar(7) | No | — | Mes del reporte, en formato AAAA-MM |
| `reports.data` | jsonb | No | — | Cifras del reporte congeladas al generarlo |
| `reports.generated_by_id` | integer | Sí | FK → users | Quien lo generó |
| `reports.created_at` | datetime | No | — | Fecha y hora de creación (UTC) |
| `security_checks.id` | integer | No | PK | Identificador |
| `security_checks.run_id` | integer | No | FK → security_runs | Corrida de la puerta de seguridad |
| `security_checks.step` | varchar(30) | No | — | Control: secretos, construccion, vulnerabilidades, sbom, firma o verificacion |
| `security_checks.image` | varchar(100) | Sí | — | Imagen a la que aplica; nula en los controles de toda la versión |
| `security_checks.status` | varchar(10) | No | — | Resultado del control (ok o fallo) |
| `security_checks.summary` | text | No | — | Resumen del resultado |
| `security_checks.report` | jsonb | Sí | — | Reporte completo del control (Gitleaks, Trivy, SBOM...), evidencia descargable |
| `security_checks.has_report` | boolean | No | — | Si el control guardó reporte |
| `security_checks.created_at` | datetime | No | — | Fecha y hora de creación (UTC) |
| `security_runs.id` | integer | No | PK | Identificador |
| `security_runs.service_id` | integer | No | FK → services | Servicio de la versión |
| `security_runs.version` | varchar(50) | No | — | Versión que se valida |
| `security_runs.commit_sha` | varchar(64) | Sí | — | Commit del código validado |
| `security_runs.images` | jsonb | No | — | Imágenes que debe producir la versión |
| `security_runs.status` | varchar(20) | No | — | en_curso, ok o fallo |
| `security_runs.failed_step` | varchar(30) | Sí | — | Control que falló, si falló |
| `security_runs.image_digests` | jsonb | Sí | — | Digest de cada imagen verificada |
| `security_runs.started_at` | datetime | No | — | Inicio de la corrida |
| `security_runs.finished_at` | datetime | Sí | — | Fin de la corrida |
| `services.id` | integer | No | PK | Identificador |
| `services.project_id` | integer | No | FK → projects | Proyecto al que pertenece el servicio |
| `services.plan_id` | integer | No | FK → plans | Plan contratado |
| `services.name` | varchar(200) | No | — | Nombre del servicio |
| `services.host` | varchar(255) | No | — | Dirección del sitio (única) |
| `services.template` | varchar(30) | No | — | Plantilla del sitio (landing o landing con formulario) |
| `services.namespace` | varchar(100) | No | — | Namespace de Kubernetes del cliente (único) |
| `services.status` | varchar(30) | No | — | Estado del monitoreo: operativo o caido |
| `services.current_version` | varchar(50) | No | — | Versión que corre |
| `services.stable_version` | varchar(50) | No | — | Última versión estable conocida |
| `services.sync_status` | varchar(30) | No | — | Estado de sincronización informado por Argo CD |
| `services.health_status` | varchar(30) | No | — | Estado de salud informado por Argo CD |
| `services.created_at` | datetime | No | — | Fecha y hora de creación (UTC) |
| `sla_policies.id` | integer | No | PK | Identificador |
| `sla_policies.priority` | varchar(2) | No | — | Prioridad P1 a P4 |
| `sla_policies.response_minutes` | integer | No | — | Minutos para responder |
| `sla_policies.resolution_minutes` | integer | No | — | Minutos para resolver |
| `sla_policies.clock` | varchar(30) | No | — | 24x7 u horario_plan (el reloj corre solo en el horario de atención) |
| `ticket_events.id` | integer | No | PK | Identificador |
| `ticket_events.ticket_id` | integer | No | FK → tickets | Solicitud a la que pertenece el evento |
| `ticket_events.actor_id` | integer | Sí | FK → users | Quien hizo el cambio |
| `ticket_events.type` | varchar(20) | No | — | Tipo de evento (estado, prioridad, responsable, nota...) |
| `ticket_events.from_value` | varchar(200) | Sí | — | Valor anterior |
| `ticket_events.to_value` | varchar(200) | Sí | — | Valor nuevo |
| `ticket_events.note` | text | Sí | — | Nota del evento |
| `ticket_events.internal` | boolean | No | — | Si la nota es interna y el cliente no la ve |
| `ticket_events.created_at` | datetime | No | — | Fecha y hora de creación (UTC) |
| `tickets.id` | integer | No | PK | Identificador |
| `tickets.service_id` | integer | No | FK → services | Servicio al que se refiere |
| `tickets.created_by_id` | integer | Sí | FK → users | Quien la creó |
| `tickets.assignee_id` | integer | Sí | FK → users | Técnico responsable |
| `tickets.title` | varchar(200) | No | — | Título de la solicitud |
| `tickets.description` | text | No | — | Descripción escrita por quien la crea |
| `tickets.impact` | varchar(20) | Sí | — | Impacto elegido por la agencia al clasificar |
| `tickets.urgency` | varchar(20) | Sí | — | Urgencia elegida por la agencia al clasificar |
| `tickets.priority` | varchar(2) | Sí | — | Prioridad P1 a P4 asignada por la matriz |
| `tickets.status` | varchar(30) | No | — | Estado canónico de la solicitud |
| `tickets.kind` | varchar(20) | No | — | Tipo: solicitud o cambio |
| `tickets.response_due_at` | datetime | Sí | — | Hora límite de respuesta |
| `tickets.resolution_due_at` | datetime | Sí | — | Hora límite de solución |
| `tickets.first_response_at` | datetime | Sí | — | Hora de la primera respuesta |
| `tickets.resolved_at` | datetime | Sí | — | Hora de resolución |
| `tickets.closed_at` | datetime | Sí | — | Hora de cierre |
| `tickets.created_at` | datetime | No | — | Fecha y hora de creación (UTC) |
| `users.id` | integer | No | PK | Identificador |
| `users.name` | varchar(200) | No | — | Nombre de la persona |
| `users.email` | varchar(200) | No | — | Correo (único sin distinguir mayúsculas); es el usuario de inicio de sesión |
| `users.role` | varchar(20) | No | — | agencia o cliente |
| `users.client_id` | integer | Sí | FK → clients | Cliente al que pertenece; nulo en los usuarios de agencia |
| `users.password_hash` | varchar(255) | Sí | — | Contraseña con hash bcrypt; nunca se guarda en claro |
| `users.is_active` | boolean | No | — | Si la cuenta puede iniciar sesión |
| `users.last_login_at` | datetime | Sí | — | Último inicio de sesión |
| `work_logs.id` | integer | No | PK | Identificador |
| `work_logs.ticket_id` | integer | No | FK → tickets | Solicitud en la que se trabajó |
| `work_logs.user_id` | integer | No | FK → users | Técnico que registró las horas |
| `work_logs.hours` | numeric(8, 2) | No | — | Horas trabajadas |
| `work_logs.note` | text | Sí | — | Nota de lo realizado |
| `work_logs.created_at` | datetime | No | — | Fecha y hora de creación (UTC) |

::: {custom-style="Nota"}
*Nota.* Elaboración propia, generada con `entrega/generar_diccionario.py` a partir de los modelos de `backend/app/models/`.
:::

<!-- DICCIONARIO:fin -->

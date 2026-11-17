# Genera entrega/datos/diccionario.csv leyendo los modelos reales de SQLAlchemy (spec 023, sección 13).
# Se ejecuta DENTRO del contenedor de la API, porque necesita `app`:
#   docker compose exec -T api python - < entrega/generar_diccionario.py > entrega/datos/diccionario.csv
# Tipos, nulabilidad y relaciones salen del código; las descripciones y la clasificación de datos personales se escriben aquí.
# Si aparece una columna sin descripción, el script falla y dice cuál: así el diccionario no se queda atrás del modelo.
import csv
import sys

from app.db import Base
import app.models  # noqa: F401  (registra todas las tablas)

DESC = {
    "agencies.name": "Nombre de la agencia que presta el servicio (Forja Digital en los datos de ejemplo)",
    "ai_drafts.incident_id": "Incidente del que habla el borrador",
    "ai_queries.user_id": "Persona que hizo la pregunta",
    "ai_drafts.kind": "Tipo de borrador: resumen (técnico, para la agencia) o mensaje_cliente (sin jerga, para el portal)",
    "ai_drafts.status": "Estado: borrador_ia, aprobado o descartado",
    "ai_drafts.source": "Origen del texto: llm (lo redactó el modelo) o plantilla (texto base cuando la IA no respondió o no pasó las verificaciones)",
    "ai_drafts.model": "Modelo que lo redactó; nulo si se usó la plantilla sin llamar a la IA",
    "ai_drafts.prompt_version": "Versión de las instrucciones del modelo",
    "ai_drafts.generated_text": "Texto generado, tal como salió",
    "ai_drafts.final_text": "Texto que la persona aprobó (editado); nulo mientras no se aprueba",
    "ai_drafts.checks": "Resultado de las verificaciones: términos prohibidos, horas que no coinciden y motivo de usar la plantilla",
    "ai_drafts.latency_ms": "Tiempo que tardó el modelo, en milisegundos",
    "ai_drafts.approved_by_id": "Persona que aprobó el borrador",
    "ai_drafts.approved_at": "Fecha y hora de la aprobación",
    "ai_queries.question": "Pregunta hecha al asistente, con las claves ya tapadas",
    "ai_queries.gate_label": "Decisión de la compuerta: en_tema o fuera_de_tema",
    "ai_queries.p_fuera_de_tema": "Probabilidad de que la pregunta sea ajena al Hub, según la compuerta",
    "ai_queries.gate_version": "Versión del clasificador de la compuerta",
    "ai_queries.llm_woken": "Si se llamó al modelo de lenguaje",
    "ai_queries.model": "Modelo que respondió; nulo si no se llamó",
    "ai_queries.prompt_version": "Versión de las instrucciones; nula si no se llamó al modelo",
    "ai_queries.llm_ok": "Si el modelo respondió a tiempo; nulo si no se llamó",
    "ai_queries.latency_ms": "Tiempo de respuesta del modelo, en milisegundos",
    "ai_queries.answer": "Respuesta mostrada a la persona",
    "ai_queries.context_sections": "Secciones de la ayuda usadas como contexto (trazabilidad de la respuesta)",
    "ai_queries.context_mode": "Cómo se armó el contexto: completo, recuperacion o rag",
    "ai_queries.retrieval_score": "Similitud coseno del mejor trozo, en modo rag",
    "ai_queries.feedback_label": "Lo que la persona dice que era la pregunta en realidad (en_tema o fuera_de_tema); nulo si no opinó",
    "audit_logs.user_id": "Quién hizo la acción; nulo si la hizo el sistema",
    "audit_logs.action": "Acción registrada (crear, aprobar, rollback, denegar...)",
    "audit_logs.entity": "Tipo de objeto afectado (ticket, incident, change_request...)",
    "audit_logs.entity_id": "Identificador del objeto afectado",
    "audit_logs.details": "Datos de la acción (por ejemplo versión de origen y de destino)",
    "audit_logs.ip": "Dirección IP desde la que se hizo la petición",
    "change_requests.ticket_id": "Solicitud que originó el cambio",
    "change_requests.service_id": "Servicio que cambia de versión",
    "change_requests.from_version": "Versión actual al pedir el cambio",
    "change_requests.to_version": "Versión que se quiere publicar",
    "change_requests.status": "pendiente, aprobada, en_validacion, desplegada, fallida o rechazada",
    "change_requests.requested_by_id": "Quien pidió el cambio",
    "change_requests.approved_by_id": "Quien lo aprobó (distinto de quien lo pidió)",
    "change_requests.gitops_commit_sha": "Commit escrito en hub-gitops al aprobar",
    "change_requests.rejection_reason": "Motivo del rechazo",
    "change_requests.approved_at": "Fecha y hora de la aprobación",
    "change_requests.deployed_at": "Fecha y hora en que Argo CD confirmó la publicación",
    "clients.agency_id": "Agencia que atiende al cliente",
    "clients.name": "Nombre del negocio cliente",
    "clients.contact_name": "Persona de contacto del cliente",
    "clients.email": "Correo de contacto",
    "clients.phone": "Teléfono de contacto",
    "clients.updated_at": "Fecha de la última modificación (UTC)",
    "deployments.service_id": "Servicio desplegado",
    "deployments.version": "Versión publicada",
    "deployments.commit_sha": "Commit de hub-gitops que la publicó",
    "deployments.author": "Nombre de quien autorizó la publicación",
    "deployments.source": "cambio o rollback",
    "incidents.service_id": "Servicio afectado",
    "incidents.priority": "Prioridad P1 a P4",
    "incidents.status": "abierto, mitigado o cerrado",
    "incidents.source": "alerta (lo abrió Alertmanager) o manual (lo abrió un técnico)",
    "incidents.fingerprint": "Huella de la alerta en Alertmanager; nula en incidentes manuales. Es única entre los incidentes abiertos",
    "incidents.title": "Título del incidente",
    "incidents.started_at": "Hora real en que empezó la falla (no la hora en que llegó el aviso)",
    "incidents.acknowledged_at": "Hora en que un técnico lo tomó",
    "incidents.mitigated_at": "Hora en que el servicio se recuperó",
    "incidents.closed_at": "Hora de cierre con causa raíz",
    "incidents.response_due_at": "Hora límite de respuesta según el SLA",
    "incidents.resolution_due_at": "Hora límite de solución según el SLA",
    "incidents.assignee_id": "Técnico responsable",
    "incidents.created_by_id": "Quien lo abrió; nulo si lo abrió el sistema",
    "incidents.root_cause": "Causa raíz, obligatoria para cerrar",
    "incidents.rollback_from_version": "Versión rota de la que se vuelve",
    "incidents.rollback_to_version": "Versión estable a la que se vuelve",
    "incidents.rollback_commit_sha": "Commit del rollback en hub-gitops",
    "incidents.rollback_by_id": "Quien pidió el rollback",
    "incidents.rollback_at": "Hora en que se pidió el rollback",
    "incidents.rollback_confirmed_at": "Hora en que el monitoreo confirmó la recuperación",
    "incident_events.incident_id": "Incidente al que pertenece el evento",
    "incident_events.type": "detectado, tomado, nota, recuperado, cerrado, rollback_enviado, rollback_confirmado o mensaje_cliente",
    "incident_events.message": "Texto del evento (línea de tiempo)",
    "incident_events.actor_id": "Quien lo registró; nulo si fue el sistema",
    "kb_documents.source": "Nombre del archivo fuente (por ejemplo ayuda_hub.md)",
    "kb_documents.content_hash": "SHA-256 del contenido; si cambia, el índice está vencido",
    "kb_documents.embedding_model": "Modelo con que se calcularon los embeddings",
    "kb_documents.chunk_count": "Cantidad de trozos del documento",
    "kb_documents.indexed_at": "Fecha y hora de la indexación",
    "kb_chunks.document_id": "Documento al que pertenece el trozo",
    "kb_chunks.section": "Título de la sección de la ayuda (es lo que se cita como fuente)",
    "kb_chunks.position": "Posición del trozo dentro del documento",
    "kb_chunks.text": "Texto del trozo",
    "kb_chunks.content_hash": "SHA-256 del texto del trozo",
    "kb_chunks.embedding": "Vector del trozo (768 números con nomic-embed-text); es el índice vectorial",
    "plans.code": "Código del plan (basico, estandar, premium)",
    "plans.name": "Nombre del plan",
    "plans.slo_availability": "Objetivo de disponibilidad mensual, en porcentaje",
    "plans.support_hours": "Horario de atención",
    "plans.cpu_quota": "Cuota de CPU del namespace del cliente",
    "plans.memory_quota": "Cuota de memoria del namespace del cliente",
    "plans.monthly_price": "Precio mensual",
    "plans.included_hours": "Horas de soporte incluidas al mes",
    "projects.client_id": "Cliente dueño del proyecto",
    "projects.name": "Nombre del proyecto",
    "projects.description": "Descripción del proyecto",
    "reports.kind": "operativo (toda la agencia, uso interno) o ejecutivo (un cliente, sin jerga)",
    "reports.client_id": "Cliente del reporte; nulo en el operativo",
    "reports.month": "Mes del reporte, en formato AAAA-MM",
    "reports.data": "Cifras del reporte congeladas al generarlo",
    "reports.generated_by_id": "Quien lo generó",
    "security_checks.run_id": "Corrida de la puerta de seguridad",
    "security_checks.step": "Control: secretos, construccion, vulnerabilidades, sbom, firma o verificacion",
    "security_checks.image": "Imagen a la que aplica; nula en los controles de toda la versión",
    "security_checks.status": "Resultado del control (ok o fallo)",
    "security_checks.summary": "Resumen del resultado",
    "security_checks.report": "Reporte completo del control (Gitleaks, Trivy, SBOM...), evidencia descargable",
    "security_checks.has_report": "Si el control guardó reporte",
    "security_runs.service_id": "Servicio de la versión",
    "security_runs.version": "Versión que se valida",
    "security_runs.commit_sha": "Commit del código validado",
    "security_runs.images": "Imágenes que debe producir la versión",
    "security_runs.status": "en_curso, ok o fallo",
    "security_runs.failed_step": "Control que falló, si falló",
    "security_runs.image_digests": "Digest de cada imagen verificada",
    "security_runs.started_at": "Inicio de la corrida",
    "security_runs.finished_at": "Fin de la corrida",
    "services.project_id": "Proyecto al que pertenece el servicio",
    "services.plan_id": "Plan contratado",
    "services.name": "Nombre del servicio",
    "services.host": "Dirección del sitio (única)",
    "services.template": "Plantilla del sitio (landing o landing con formulario)",
    "services.namespace": "Namespace de Kubernetes del cliente (único)",
    "services.status": "Estado del monitoreo: operativo o caido",
    "services.current_version": "Versión que corre",
    "services.stable_version": "Última versión estable conocida",
    "services.sync_status": "Estado de sincronización informado por Argo CD",
    "services.health_status": "Estado de salud informado por Argo CD",
    "sla_policies.priority": "Prioridad P1 a P4",
    "sla_policies.response_minutes": "Minutos para responder",
    "sla_policies.resolution_minutes": "Minutos para resolver",
    "sla_policies.clock": "24x7 u horario_plan (el reloj corre solo en el horario de atención)",
    "tickets.service_id": "Servicio al que se refiere",
    "tickets.created_by_id": "Quien la creó",
    "tickets.assignee_id": "Técnico responsable",
    "tickets.title": "Título de la solicitud",
    "tickets.description": "Descripción escrita por quien la crea",
    "tickets.impact": "Impacto elegido por la agencia al clasificar",
    "tickets.urgency": "Urgencia elegida por la agencia al clasificar",
    "tickets.priority": "Prioridad P1 a P4 asignada por la matriz",
    "tickets.status": "Estado canónico de la solicitud",
    "tickets.kind": "Tipo: solicitud o cambio",
    "tickets.response_due_at": "Hora límite de respuesta",
    "tickets.resolution_due_at": "Hora límite de solución",
    "tickets.first_response_at": "Hora de la primera respuesta",
    "tickets.resolved_at": "Hora de resolución",
    "tickets.closed_at": "Hora de cierre",
    "ticket_events.ticket_id": "Solicitud a la que pertenece el evento",
    "ticket_events.actor_id": "Quien hizo el cambio",
    "ticket_events.type": "Tipo de evento (estado, prioridad, responsable, nota...)",
    "ticket_events.from_value": "Valor anterior",
    "ticket_events.to_value": "Valor nuevo",
    "ticket_events.note": "Nota del evento",
    "ticket_events.internal": "Si la nota es interna y el cliente no la ve",
    "users.name": "Nombre de la persona",
    "users.email": "Correo (único sin distinguir mayúsculas); es el usuario de inicio de sesión",
    "users.role": "agencia o cliente",
    "users.client_id": "Cliente al que pertenece; nulo en los usuarios de agencia",
    "users.password_hash": "Contraseña con hash bcrypt; nunca se guarda en claro",
    "users.is_active": "Si la cuenta puede iniciar sesión",
    "users.last_login_at": "Último inicio de sesión",
    "work_logs.ticket_id": "Solicitud en la que se trabajó",
    "work_logs.user_id": "Técnico que registró las horas",
    "work_logs.hours": "Horas trabajadas",
    "work_logs.note": "Nota de lo realizado",
}
GENERICAS = {"id": "Identificador", "created_at": "Fecha y hora de creación (UTC)"}
PERSONAL = {
    "users.name": "Personal", "users.email": "Personal", "users.last_login_at": "Personal (actividad)", "users.password_hash": "Credencial",
    "clients.contact_name": "Personal", "clients.email": "Personal", "clients.phone": "Personal",
    "audit_logs.ip": "Personal (dirección IP)", "audit_logs.details": "Posible",
    "tickets.title": "Posible (texto libre)", "tickets.description": "Posible (texto libre)", "ticket_events.note": "Posible (texto libre)",
    "incident_events.message": "Posible (texto libre)", "incidents.title": "Posible (texto libre)", "incidents.root_cause": "Posible (texto libre)",
    "ai_queries.question": "Posible (texto libre)", "ai_queries.answer": "Posible (texto libre)",
    "ai_drafts.generated_text": "Posible (texto libre)", "ai_drafts.final_text": "Posible (texto libre)",
    "work_logs.note": "Posible (texto libre)", "work_logs.hours": "Personal (actividad laboral)",
}


def tipo(columna) -> str:
    t = str(columna.type)
    return "jsonb" if t.upper() == "JSON" else t.lower()


def main() -> int:
    filas, faltan = [], []
    for nombre in sorted(Base.metadata.tables):
        t = Base.metadata.tables[nombre]
        for c in t.columns:
            clave = f"{nombre}.{c.name}"
            rel = ""
            if c.primary_key:
                rel = "PK"
            elif c.foreign_keys:
                rel = "FK → " + next(iter(c.foreign_keys)).column.table.name
            desc = DESC.get(clave) or GENERICAS.get(c.name)
            if desc is None:
                faltan.append(clave)
                continue
            filas.append([nombre, c.name, tipo(c), "No" if not c.nullable else "Sí", rel, PERSONAL.get(clave, "No"), desc])
    if faltan:
        print("Sin descripción:", faltan, file=sys.stderr)
        return 1
    w = csv.writer(sys.stdout, delimiter=";", lineterminator="\n")
    w.writerow(["tabla", "columna", "tipo", "nulo", "relacion", "personal", "descripcion"])
    w.writerows(filas)
    return 0


sys.exit(main())

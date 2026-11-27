# Ayuda del Hub (base de conocimiento del asistente, spec 012)

Cada sección `##` es un tema. El asistente solo puede afirmar lo que está escrito aquí; todo lo demás lo responde con «no lo sé». Los datos salen del código del Hub y de `docs/`: si una pantalla o regla cambia, se cambia aquí en el mismo PR.

## Qué es el Hub y quién lo usa
El Hub (CloudOps Client Hub) es la herramienta de la agencia Forja Digital para gestionar el servicio de sus clientes: solicitudes, cambios, incidentes, SLA y dashboards. Hay dos roles. El rol agencia (administrador y técnico) ve todo. El rol cliente (una PyME) ve solo lo suyo, en el portal del cliente, con lenguaje sin jerga técnica.

## Menú de la consola de agencia
El menú lateral de la consola tiene: Inicio, Clientes, Solicitudes, Cambios, Servicios, Incidentes, Asistente, Reportes y Bitácora. Reportes todavía no está disponible (aparece como próximamente). Abajo del menú está la sesión: el nombre, el cambio de tema claro u oscuro y el botón Cerrar sesión.
Palabras clave: opciones del menú, secciones, pantallas, navegación.

## Portal del cliente
El cliente tiene solo dos pantallas: Inicio y Solicitudes. En Inicio ve si su sitio está disponible, la disponibilidad del mes frente al objetivo de su plan, los incidentes del mes y el tiempo que tardamos en recuperar su sitio, todo en lenguaje de negocio. En Solicitudes crea solicitudes nuevas y ve las suyas. El cliente no usa el asistente ni ve términos técnicos como namespace, pod o clúster.

## Tablero de Inicio
Inicio muestra el tablero del mes: disponibilidad promedio, solicitudes abiertas, horas registradas (sobre 120 horas disponibles) y costo del mes. Debajo hay el KPI por cliente (disponibilidad, solicitudes, horas y costo de cada cliente), la carga por técnico y, por cada cliente, un enlace Métricas que muestra la disponibilidad del mes frente al objetivo del plan.

## Registrar un cliente
En Clientes está el botón + Registrar cliente. El formulario tiene tres bloques: Cliente (nombre, correo y teléfono), Proyecto (nombre y descripción) y Servicio y plan (dirección o host, plantilla Landing estática o Landing + formulario, namespace y plan Básico, Estándar o Premium). Los campos con asterisco son obligatorios.
Palabras clave: crear cliente, nuevo cliente, alta de cliente, agregar cliente.

## Detalle de un cliente
Al abrir un cliente en Clientes se ve el contacto, sus proyectos y servicios (dirección, namespace y plantilla) y los datos de su plan: SLO de disponibilidad mensual, horario de atención, horas incluidas, precio mensual, cuota de CPU y RAM, y la tabla de SLA por prioridad con su significado, tiempo de respuesta y de solución.

## Planes
Básico: disponibilidad mensual objetivo 99,0 %, atención lunes a viernes de 8:00 a 18:00, 4 horas de soporte incluidas, precio mensual ficticio de 150.000, cuota 250m de CPU y 256Mi de RAM. Estándar: 99,5 %, lunes a sábado de 7:00 a 20:00, 10 horas incluidas, 350.000, cuota 500m y 512Mi. Premium: 99,9 %, atención 24x7, 20 horas incluidas, 700.000, cuota 1000m y 1Gi. Hoy La Sazón tiene Premium, El Tornillo Estándar y Dental Popayán Básico.
Palabras clave: horario de atención, cuánto cuesta, precio, horas incluidas, soporte, SLO, disponibilidad objetivo, cuota.

## Crear una solicitud (cliente)
El cliente entra a Solicitudes en el portal y usa Nueva solicitud: elige el servicio, elige qué necesita (Reportar un problema o hacer una consulta, o Pedir un cambio en mi sitio), escribe un título y una descripción y pulsa Enviar solicitud. Solo el cliente crea solicitudes desde el portal.

## Lista de solicitudes de la agencia
En Solicitudes la agencia ve todas las solicitudes con filtros por estado, prioridad, cliente y SLA. El SLA de cada una aparece como A tiempo, En riesgo, Vencido o Sin plazo (Sin plazo significa que todavía no está clasificada y no tiene fecha límite).
Palabras clave: tickets, filtros, sin plazo, vencido, en riesgo, a tiempo.

## Clasificar una solicitud y prioridad
En el detalle de una solicitud la agencia elige impacto (alto, medio o bajo) y urgencia (alta, media o baja) y pulsa Guardar clasificación. La matriz propone la prioridad: impacto alto con urgencia alta, media o baja da P1, P2 o P3; impacto medio da P2, P3 o P4; impacto bajo da P3, P4 o P4. Si el técnico elige una prioridad distinta a la propuesta debe escribir el motivo de corrección. Al clasificar se calcula el SLA y arranca su reloj.

## Prioridades P1 a P4 y tiempos de SLA
P1 es crítica (el sitio no funciona o se pierden ventas): respuesta 15 minutos y solución 4 horas. P2 es alta (una función importante falla): 1 hora y 8 horas. P3 es media (falla menor con alternativa): 4 horas y 24 horas. P4 es baja (consulta o mejora): 8 horas y 72 horas. El P1 siempre corre 24x7; P2, P3 y P4 cuentan solo dentro del horario de atención del plan del cliente.
Palabras clave: cuánto tarda, plazo, tiempo de respuesta, tiempo de solución, SLA, urgente.

## Asignar, cambiar estado y registrar horas
En el detalle de una solicitud la agencia puede Asignar responsable (usuario responsable y botón Asignar), Cambiar estado (Nuevo estado y botón Actualizar estado) y Registrar horas (horas y nota, botón Guardar horas). El detalle también muestra el Historial de la solicitud.

## Estados de una solicitud
Una solicitud pasa por abierto, en progreso, en espera, resuelto y cerrado. Los pasos permitidos son: abierto a en progreso; en progreso a en espera o a resuelto; en espera de vuelta a en progreso; resuelto a cerrado. Cerrado es final. El tiempo de respuesta se mide hasta que pasa a en progreso y el de solución hasta que queda resuelta.
Palabras clave: ticket, flujo, ciclo de vida, pasar de un estado a otro.

## Pedir un cambio de versión
Desde el detalle de una solicitud la agencia usa Registrar cambio: escribe la Versión destino (por ejemplo v1.1) y pulsa Registrar cambio. El cambio queda pendiente en la pantalla Cambios, donde se aprueba o se rechaza.

## Aprobar o rechazar un cambio
En Cambios cada cambio pendiente tiene los botones Aprobar y Rechazar. Aprobar solo se puede cuando los controles de seguridad pasan; si fallan, el botón queda desactivado y el cambio se rechaza por seguridad. Rechazar pide un motivo (Motivo del rechazo) y se confirma con Confirmar rechazo.
Palabras clave: aprobar un cambio, aprobación, autorizar, publicar un cambio, rechazar, motivo.

## Estados de un cambio
Un cambio pasa por pendiente, aprobada, en validación y publicada. También puede quedar rechazada (desde pendiente) o no se pudo publicar (fallida) si, ya aprobado, no quedó publicado y sano dentro del tiempo de validación (10 minutos por defecto). Todo cambio entra por Git y Argo CD: nadie despliega a mano.
Palabras clave: tiempo de validación, no se pudo publicar, fallida, publicada.

## Puerta de seguridad
Antes de publicar, cada cambio pasa por controles: secretos (Gitleaks), construcción de la imagen, vulnerabilidades (Trivy), inventario de componentes (SBOM con Syft), firma (Cosign) y verificación de la firma. Los resultados se ven en Cambios y en Servicios como Controles de seguridad. Si un control falla el cambio se rechaza por seguridad y no se publica.
Palabras clave: controles, escaneo, Trivy, Gitleaks, Cosign, firma, seguridad antes de publicar.

## Pantalla de Servicios
Servicios lista cada sitio con su cliente, disponibilidad, versión activa, sincronización, salud, controles de seguridad y último cambio (autor y fecha). El botón Ver de cada fila abre el historial de cambios publicados y el botón Ocultar lo cierra.

## Estados de un servicio
Un servicio puede estar Operativo, Con fallas (degradado) o No disponible (caído). Pasa a No disponible cuando hay un incidente abierto por una alerta del monitoreo.

## Abrir un incidente
Hay dos formas. Manual: en Incidentes se pulsa Nuevo incidente, se elige el servicio y la prioridad y se escribe un título. Automática: cuando el monitoreo detecta que el sitio no responde, Alertmanager avisa al Hub y se abre un incidente P1 con la hora real de inicio de la falla y el reloj del SLA corriendo.
Palabras clave: qué pasa cuando el sitio cae, caída, sitio caído, se cae, alerta, falla, crear incidente, nuevo incidente.

## Lista de incidentes
Incidentes muestra la lista con filtros por estado, cliente y prioridad, y la columna Reloj del SLA. Los estados son Abierto, Mitigado y Cerrado.

## Atender un incidente
En el detalle de un incidente están el Reloj del SLA, el Responsable, el Inicio de la falla, la Línea de tiempo, el Diagnóstico (enlace a los registros del sitio en Grafana y el último cambio del servicio) y las Acciones. Acciones: Tomar incidente (para quedar como responsable), Agregar nota (a la línea de tiempo), Marcar como mitigado y Cerrar incidente.
Palabras clave: botones, acciones, qué puedo hacer en un incidente, tomar, nota, responsable.

## Mitigar y cerrar un incidente
Un incidente manual se marca con el botón Marcar como mitigado. Uno abierto por alerta se marca mitigado solo cuando el monitoreo ve el sitio responder (o se puede marcar después de un rollback confirmado). Cerrar incidente solo aparece cuando está mitigado y pide la causa raíz, que es obligatoria. El tiempo de recuperación (MTTR) es lo que pasa entre el inicio de la falla y la mitigación.
Palabras clave: cerrar un incidente, cierro, cerrar, terminar, causa raíz, MTTR, tiempo de recuperación, mitigar.

## Rollback
Rollback devuelve el sitio a su última versión estable. En el detalle del incidente se pulsa Rollback y se confirma con Confirmar rollback. El Hub escribe un commit en el repositorio hub-gitops con la versión estable y Argo CD sincroniza el sitio; nadie toca el clúster y queda registrado a nombre de quien lo pidió. El botón se desactiva si el incidente ya no está abierto, si ya hay un rollback en curso o confirmado, o si no hay una versión estable a la que volver. El avance se ve en pasos y la pantalla se actualiza sola cada 5 segundos.
Palabras clave: volver a la versión anterior, revertir, deshacer, botón desactivado, no puedo hacer rollback.

## Mensaje al cliente tras un incidente
Cuando el incidente está mitigado, el detalle muestra un mensaje para el cliente que se puede copiar con el botón Copiar. Es un borrador: el Hub nunca lo envía solo; la agencia decide si lo manda.

## Bitácora
Bitácora muestra quién hizo qué y cuándo, con filtros por usuario, objeto, acción y fechas (desde y hasta). Es de solo lectura: las acciones no se pueden editar ni borrar. Las fechas se muestran en hora de Colombia.
Palabras clave: auditoría, quién hizo qué, historial de acciones, editar la bitácora.

## Reportes
Los reportes todavía no existen en el Hub. En el menú de la consola aparece Reportes como próximamente, pero no se puede abrir: por ahora no hay pantalla de reportes ni se pueden generar ni exportar.

## Este asistente
El asistente responde preguntas sobre el uso del Hub con una IA local que corre dentro del laboratorio: ningún dato sale a servicios externos. Solo lo usa la agencia. Una compuerta decide primero si la pregunta trata del Hub; si no, responde ella sola sin despertar a la IA. Solo informa: no aprueba cambios, no publica ni hace rollback. Debajo de cada respuesta se puede marcar Era del Hub o No era del Hub para corregir a la compuerta.

## Cómo entrar y salir
Se entra con el correo y la contraseña de la cuenta en la pantalla de inicio de sesión. Según el rol, el Hub lleva a la consola de agencia o al portal del cliente. Se sale con Cerrar sesión, abajo del menú.

## Lenguaje para el cliente
Al cliente nunca se le muestran términos técnicos. Ticket se dice solicitud; incidente P1 es falla crítica con atención inmediata; rollback es restaurar una versión estable; MTTR es el tiempo que tardamos en recuperar su sitio; namespace, pod, ingress y clúster no se mencionan. La lista completa está en el glosario del proyecto.

## Lo que el Hub no hace
El Hub no despliega a mano ni habla con Kubernetes: solo con Gitea, Argo CD y Prometheus. No envía mensajes al cliente por correo ni por chat. No hay facturación, pagos ni dominios reales. El asistente no ejecuta acciones.
Palabras clave: despliega a mano, kubernetes, limitaciones, no puede.

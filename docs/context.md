# Contexto de entrevista para la especifícación 000 · Modelo de servicio

## Objetivo

Recoger la información real de la empresa o agencia para definir:
- los planes de servicio,
- la matriz de prioridad P1–P4,
- los tiempos de respuesta y solución,
- las reglas de escalamiento,
- los KPI del servicio,
- y el proceso AS-IS/TO-BE.

La información de esta guía será la base para construir la spec 000 y los archivos semilla que alimentarán el Hub.

## Cómo usar esta guía

Se recomienda entrevistar a 2–3 agencias o freelancers y registrar las respuestas en formato de notas por entrevista. La idea es comparar cómo cada organización opera y luego consolidar las mejores prácticas y los puntos comunes.

## Guía de preguntas (15)

1. ¿Cómo recibe normalmente una solicitud de soporte o mantenimiento de un cliente?
2. ¿Qué canales usan para reportar incidentes o solicitudes: correo, WhatsApp, teléfono, portal, ticket, chat?
3. ¿Qué tipos de problemas más frecuentes reciben: caídas, errores funcionales, cambios, mantenimiento, configuración, seguridad?
4. ¿Cómo se determina si un caso es urgente o no urgente?
5. ¿Qué tiempos de respuesta suelen prometer o entregar a los clientes cuando hay un problema?
6. ¿Cuánto tiempo normalmente tarda una incidencia en resolverse desde que se reporta hasta que queda cerrada?
7. ¿Qué porcentaje de incidentes ocurre en horario laboral y qué porcentaje fuera de horario?
8. ¿Qué nivel de atención ofrecen según el tipo de cliente o del plan contratado?
9. ¿Qué recursos o roles intervienen en la resolución de un caso: soporte, técnico, administrador, líder, cliente?
10. ¿Cómo se priorizan varias incidencias al mismo tiempo?
11. ¿Cuáles son los indicadores que ustedes usan para saber si el servicio está funcionando bien?
12. ¿Qué tan importante es la disponibilidad del servicio para los clientes y qué nivel de disponibilidad aceptan como mínimo?


## Preguntas adicionales que se pueden utilizar para profundizar

- ¿Cuáles son los 3 clientes o tipos de clientes más comunes?
- ¿Qué características distinguen a un cliente básico de uno premium?
- ¿Los clientes saben cuándo hay una falla o cuándo se está atendiendo un caso?
- ¿Hay atención 24/7 o solo en horario comercial?
- ¿Qué pasa si un caso llega en fin de semana o en horario no laborable?
- ¿Cuál es la diferencia entre una solicitud de cambio y un incidente real?

## Criterios de registro de respuesta

Para la entrevista, se recomienda registrar:
- nombre de la empresa o agencia
- persona entrevistada
- cargo
- fecha
- resumen de la respuesta
- hallazgos clave
- diferencias con otras entrevistas
- decisiones que podrían convertirse en regla del servicio

## Resultado esperado

Con estas entrevistas se debe poder cerrar:
- la matriz de prioridad P1–P4,
- los tiempos de SLA por prioridad,
- los planes básicos del servicio,
- las reglas de escalamiento,
- y los KPI del modelo de servicio.

## Notas de entrevistas ficticias

### Entrevista 1 · Soluciones Digitales Popayán

- **Empresa:** Soluciones Digitales Popayán
- **Persona entrevistada:** , gerente de operaciones
- **Cargo:** Gerente de operaciones
- **Fecha:**  de octubre de 2026
- **Resumen:** La agencia recibe solicitudes por WhatsApp, correo y teléfono. El equipo trabaja con clientes pequeños y medianos que necesitan mantenimiento, cambios y soporte funcional.
- **1. Recepción:** Las solicitudes llegan principalmente por WhatsApp y correo electrónico. El cliente describe el problema y se registra un ticket manual.
- **2. Canales:** WhatsApp, correo, teléfono y un formulario de contacto. No usan un portal con seguimiento automático.
- **3. Problemas frecuentes:** errores funcionales, caídas de sitios, cambios de contenido, configuración de correo y problemas de integración.
- **4. Urgencia:** Se define como urgente cuando hay caída completa, pérdida de ventas o riesgo de datos. El nivel se revisa con el cliente dentro de la misma reunión.
- **5. Tiempos:** Respuesta inicial estimada de 2 horas en horario laboral. Resolución varía entre 1 y 5 días, según la complejidad.
- **6. Duración:** La mayoría se resuelve en un plazo de 24 a 72 horas. Las incidencias complejas pueden tardar hasta 7 días.
- **7. Horario:** El 80 % ocurre en horario laboral; el 20 % restante puede presentarse fuera del horario, especialmente durante campañas.
- **8. Nivel de atención:** Ofrecen atención prioritaria a clientes de planes mensuales de mayor valor. Los clientes básicos reciben atención por solicitud y respuesta en lotes.
- **9. Roles:** soporte, técnico y gerente. El cliente participa con accesos y evidencia para verificar la solución.
- **10. Priorización:** Se ordenan por impacto económico, urgencia y disponibilidad de recursos. Los cambios de tipo comercial se atienden después de las fallas críticas.
- **11. Indicadores:** tiempos de respuesta, tiempo de resolución, número de tickets abiertos y satisfacción del cliente.
- **12. Disponibilidad:** Aceptan una disponibilidad del 99 % para clientes críticos, pero solo ofrecen soporte 24/7 mediante convenio adicional.
- **Hallazgos clave:** La agencia necesita un tablero común para evitar que los tickets se pierdan entre chats y correos. Sus tiempos de respuesta son realistas para clientes pequeños, pero debe quedar definida la responsabilidad del cliente.
- **Diferencias:** Más orientada a un soporte reactivo que preventivo.
- **Decisiones posibles:** Definir planes con niveles de atención, seguimiento y tiempo máximo de respuesta.

### Entrevista 2 · Norte Digital Studio

- **Empresa:** Norte Digital Studio
- **Persona entrevistada:** Carlos Peña, técnico de soporte
- **Cargo:** Técnico de soporte y mantenimiento
- **Fecha:** 7 de octubre de 2026
- **Resumen:** La agencia atiende proyectos web y tiendas en línea para clientes del sector comercial. La atención se estructura por equipos y por prioridad de negocio.
- **1. Recepción:** Los clientes usan un formulario o un WhatsApp directo. El equipo registra cada caso en un sistema de tickets.
- **2. Canales:** Portal web, WhatsApp, correo y llamadas. Todos los casos se registran en el mismo sistema.
- **3. Problemas frecuentes:** fallas de conexión, errores de pago, bloqueo de cuentas, actualizaciones de plugins y cambios de contenido.
- **4. Urgencia:** Los casos se consideran urgentes si afectan ventas o la disponibilidad de una tienda. Se revisa el impacto en ingresos y la hora del reporte.
- **5. Tiempos:** Respuesta inicial de 1 hora para clientes premium y 4 horas para clientes básicos durante la semana.
- **6. Duración:** Las incidencias críticas se intentan cerrar en 8 horas; las incidencias normales suelen resolverse en 2 días.
- **7. Horario:** El 65 % ocurre en horario laboral, mientras que el 35 % puede suceder fuera de horario cuando hay promociones o ventas.
- **8. Nivel de atención:** Los planes premium incluyen soporte prioritario y actualización de seguridad. Los planes básicos cuentan con soporte limitado a horario laboral.
- **9. Roles:** apoyo técnico, diseñador, administrador y líder de proyecto. El cliente aporta credenciales y confirma el uso esperado de la herramienta.
- **10. Priorización:** Primero se atienden casos de orden de compra, luego disponibilidad del sistema y, finalmente, cambios de contenido.
- **11. Indicadores:** disponibilidad, tiempo medio de atención, tasa de resolución en el primer contacto, errores recurrentes y satisfacción.
- **12. Disponibilidad:** Mantienen una disponibilidad de 99,5 % para todos los clientes y un protocolo de escalamiento para incidentes de comercio electrónico.
- **Hallazgos clave:** El servicio ya está centralizado en tickets, pero aún depende de la disponibilidad del personal técnico para atender casos fuera de horario.
- **Diferencias:** Tiene reglas más claras y una mayor adopción de métricas de continuidad.
- **Decisiones posibles:** Establecer tickets con severidad, horarios de soporte y un tiempo de respuesta diferenciado por plan.


## Consolidación

- Las tres agencias usan WhatsApp, correo o teléfono como canales de contacto, pero solo dos tienen un registro central de tickets.
- La atención más rápida corresponde a clientes premium y requiere compromiso de disponibilidad.
- La prioridad se define principalmente por impacto económico, disponibilidad del servicio y riesgo para la operación del cliente.
- Los indicadores comunes son tiempo de respuesta, tiempo de resolución, disponibilidad y satisfacción del cliente.
- La mayor diferencia entre agencias está en la cobertura fuera de horario y en el nivel de automatización del soporte.

## Decisiones recomendadas para el modelo de servicio

1. Centralizar todas las solicitudes en un único sistema de tickets.
2. Definir una clasificación P1–P4 con tiempos de respuesta y solución por prioridad.
3. Ofrecer planes básicos, profesionales y premium con niveles de atención diferenciados.
4. Incluir una política de escalamiento por porcentaje del SLA consumido.
5. Medir la disponibilidad, el tiempo de respuesta y la satisfacción del cliente.
6. Definir un proceso claro para incidentes, cambios y solicitudes de mantenimiento.
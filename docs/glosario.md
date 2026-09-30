# Glosario

> Principio 8: **el cliente no ve jerga técnica.** Todo texto que llega al portal del cliente, a
> los reportes ejecutivos o a los mensajes de incidente usa la columna "Cómo lo ve el cliente".
> La consola de la agencia sí puede usar los términos técnicos.

## Traducción técnico → cliente

| Término técnico | Cómo lo ve el cliente |
|---|---|
| Disponibilidad (uptime) de 99,2 % | "Su sitio se mantuvo disponible dentro del objetivo acordado." |
| Disponibilidad por debajo del SLO | "Este mes su sitio estuvo disponible menos de lo acordado; le explicamos qué pasó y qué mejoramos." |
| Error HTTP 500 / 5xx | "Se detectó una falla temporal y se activó el proceso de recuperación." |
| Sitio caído (`caido`) | "Su sitio no está disponible en este momento; ya estamos trabajando en ello." |
| Sitio degradado (`degradado`) | "Su sitio funciona, pero más lento o con fallas parciales." |
| Rollback | "Se restauró una versión estable para mantener la continuidad." |
| Latencia elevada | "El sitio presentó lentitud y se inició una acción de mejora." |
| Vulnerabilidad en una dependencia | "Una actualización fue detenida antes de publicarse por controles de seguridad." |
| Secreto detectado por Gitleaks | "Una actualización fue detenida porque contenía información sensible." |
| Imagen sin firma válida | "Una actualización fue detenida porque no pasó la verificación de origen." |
| Despliegue / sync de Argo CD | "Publicamos la actualización que usted solicitó." |
| Incidente P1 | "Falla crítica: atención inmediata." |
| MTTR | "Tiempo que tardamos en recuperar su sitio." |
| Ticket | "Solicitud." |
| Namespace, Pod, Ingress, clúster | No se mencionan nunca. |

## Términos del dominio

| Término | Definición |
|---|---|
| **Agencia** | Empresa que presta el servicio (Forja Digital). Rol `agencia`. |
| **Cliente** | PyME que contrata el servicio. Rol `cliente`. |
| **Proyecto** | Trabajo que la agencia hace para un cliente (ej. "Sitio web La Sazón"). |
| **Servicio** | Algo que corre y se monitorea: un sitio con URL, versión y plan. |
| **Plan** | Básico, Estándar o Premium: define SLO, horario de atención, SLA y cuota de recursos. |
| **SLA** | Acuerdo de nivel de servicio: tiempos máximos de respuesta y solución por prioridad. |
| **SLO** | Objetivo de disponibilidad mensual del plan (ej. 99,5 %). |
| **Prioridad P1–P4** | Clasificación por impacto × urgencia (ver [constitución](../constitution.md#prioridades-y-sla-base-propuesta-la-spec-000-los-confirma)). |
| **Tiempo de respuesta** | Desde que se abre el caso hasta que un técnico lo toma (`en_progreso`). |
| **Tiempo de solución** | Desde que se abre el caso hasta que queda `resuelto` (ticket) o `mitigado` (incidente). |
| **MTTR** | Tiempo medio de recuperación: promedio de (hora de mitigación − hora de inicio) de los incidentes. |
| **Incidente** | Falla del servicio, abierta a mano o por una alerta. Tiene prioridad, SLA y línea de tiempo. |
| **Solicitud de cambio** | Pedido de una nueva versión del sitio; pasa por aprobación y la puerta de seguridad. |
| **Rollback** | Volver a la última versión estable con un `git revert` en el repo GitOps. |
| **Borrador IA** | Texto generado por el asistente local; nadie lo ve fuera de la agencia hasta que un humano lo aprueba. |

## Estados canónicos (texto que se muestra)

| Entidad | Valor interno | Texto en la interfaz |
|---|---|---|
| Ticket | `abierto` · `en_progreso` · `en_espera` · `resuelto` · `cerrado` | Abierto · En progreso · En espera · Resuelto · Cerrado |
| Incidente | `abierto` · `mitigado` · `cerrado` | Abierto · Mitigado · Cerrado |
| Servicio | `operativo` · `degradado` · `caido` | Operativo · Con fallas · No disponible |
| Solicitud de cambio | `pendiente` · `aprobada` · `en_validacion` · `desplegada` · `rechazada` | Pendiente · Aprobada · En validación · Publicada · Rechazada |
| Texto de IA | `borrador_ia` · `aprobado` · `descartado` | Borrador · Aprobado · Descartado |

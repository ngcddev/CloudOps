# 004 · Mesa de servicio: tickets y prioridad

> **Módulo:** 2 (producto: puede adelantarse) · **Requerimientos:** RF-04, RF-05 · **Depende de:** 000, 001 · **Estado:** Spec y plan

## Qué y por qué

Las solicitudes de los clientes se registran, se priorizan con una regla común y se asignan a un
responsable. Así ninguna solicitud se pierde en un chat, y el SLA se puede medir desde la hora real
en que llegó.

## Actores

| Actor | Qué hace en esta spec |
|---|---|
| Cliente PyME | Crea una solicitud y ve en qué va |
| Técnico de la agencia | Clasifica, asigna, cambia el estado y registra horas |

## Historias de usuario

- **HU-1.** Como cliente, quiero crear una solicitud desde mi portal, para no depender de un chat.
- **HU-2.** Como técnico, quiero clasificar la solicitud por impacto y urgencia y que el sistema
  proponga la prioridad, para priorizar siempre igual.
- **HU-3.** Como técnico, quiero asignar la solicitud y moverla por sus estados, para que todos
  sepan quién la atiende.
- **HU-4.** Como administrador, quiero la hora de cada cambio, para medir el SLA con datos reales.
- **HU-5.** Como técnico, quiero registrar las horas trabajadas, para calcular carga y costo.

## Criterios de aceptación

- [ ] CA-1. Un cliente crea una solicitud (título, descripción, servicio) desde el portal.
- [ ] CA-2. La agencia elige impacto y urgencia y el sistema asigna P1–P4 según la matriz de la
  spec 000; la prioridad se puede corregir dejando el motivo.
- [ ] CA-3. La agencia asigna un responsable y mueve el ticket por
  `abierto → en_progreso → en_espera → resuelto → cerrado`; no se permiten saltos inválidos.
- [ ] CA-4. Cada cambio de estado, prioridad o responsable queda en el historial con hora (UTC) y
  usuario.
- [ ] CA-5. Cada ticket muestra su hora límite de respuesta y de solución, y si va "a tiempo",
  "en riesgo" (≥ 80 %) o "vencido".
- [ ] CA-6. El técnico registra horas trabajadas en el ticket.
- [ ] CA-7. El cliente ve sus solicitudes con estados en lenguaje simple, sin ver notas internas.

## Fuera de alcance

- Notificaciones por correo o chat.
- Adjuntos.
- Incidentes automáticos (spec 008) y solicitudes de cambio con despliegue (spec 005).

## Demo de cierre

1. Como cliente La Sazón, crear "El menú del domingo no aparece".
2. Como agencia, clasificar impacto alto / urgencia media → P2; asignar y pasar a `en_progreso`.
3. Mostrar el historial con horas y el indicador de SLA.
4. Resolver con 1,5 h registradas; el cliente ve "Resuelto".

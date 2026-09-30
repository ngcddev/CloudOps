# 001 — Clientes, tickets y SLA

## Qué hace
La agencia registra clientes (cada uno con un proyecto/sitio y un plan) y crea tickets de soporte con prioridad. Cada ticket calcula automáticamente sus tiempos límite de SLA y muestra si está a tiempo o vencido.

## Historias de usuario
- Como agencia, quiero registrar un cliente con su sitio y plan para atenderlo.
- Como agencia, quiero crear un ticket con prioridad P1–P4 para que el sistema calcule el SLA.
- Como agencia, quiero ver la lista de tickets con su estado de SLA para priorizar el trabajo.
- Como agencia, quiero cerrar un ticket para registrar su resolución.

## Reglas de SLA
| Prioridad | Respuesta | Solución |
|---|---|---|
| P1 | 15 min | 4 h |
| P2 | 1 h | 8 h |
| P3 | 4 h | 24 h |
| P4 | 8 h | 72 h |

## Criterios de aceptación
- [ ] Se puede crear un cliente con nombre, sitio (URL) y plan.
- [ ] Existen 3 clientes ficticios cargados por defecto (p. ej. un restaurante).
- [ ] Se puede crear un ticket asociado a un cliente, con título, descripción y prioridad.
- [ ] Al crear el ticket se guardan las fechas límite de respuesta y solución según la tabla.
- [ ] La lista de tickets muestra estado: `abierto`, `en progreso` o `cerrado`.
- [ ] Un ticket sin resolver muestra **"A tiempo"** o **"Vencido"** según la hora actual.
- [ ] Se puede cerrar un ticket y queda registrada la fecha de cierre.
- [ ] La interfaz está en español y en blanco y negro.

## Fuera de alcance
Login, roles, notificaciones por correo, planes con SLA distintos.

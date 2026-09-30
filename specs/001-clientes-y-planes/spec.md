# 001 · Clientes y planes

> **Acciona:** Sistemas (Backend, Frontend) · Industrial valida planes y SLA
>
> **Módulo:** 1 · **Requerimientos:** RF-01, RF-02 · **Depende de:** 000 · **Estado:** Tareas listas

## Qué y por qué

La agencia registra a sus clientes, sus proyectos, los servicios que opera para ellos y el plan
contratado. Es el punto de partida del flujo (principio 1): todo lo demás (tickets, cambios,
incidentes, reportes) cuelga de un cliente y su servicio.

## Actores

| Actor | Qué hace en esta spec |
|---|---|
| Administrador de la agencia | Registra y edita clientes, proyectos y servicios |
| Técnico de la agencia | Consulta el plan y el SLA de un servicio |

## Historias de usuario

- **HU-1.** Como administrador, quiero registrar un cliente con sus datos de contacto, para tener un
  único lugar con todas las cuentas.
- **HU-2.** Como administrador, quiero crear un proyecto y un servicio para cada cliente y asignarle
  un plan, para saber qué se le presta y en qué condiciones.
- **HU-3.** Como técnico, quiero ver en el detalle de un cliente su servicio, su plan y su SLA, para
  saber qué tan rápido debo responder.

## Criterios de aceptación

- [ ] CA-1. Desde cero, un solo comando levanta el sistema con la agencia **Forja Digital**, los
  3 planes de la spec 000 y los 3 clientes canónicos cargados.
- [ ] CA-2. Se puede crear, listar, ver y editar un cliente (nombre, contacto, correo, teléfono).
- [ ] CA-3. Cada cliente tiene al menos un proyecto y un servicio; el servicio tiene nombre, dirección
  (host), plantilla y plan.
- [ ] CA-4. El detalle del cliente muestra su proyecto, su servicio, el plan y los tiempos de SLA
  por prioridad tomados de la spec 000.
- [ ] CA-5. No se puede crear un servicio sin plan ni un cliente sin nombre; el error se explica en
  español.
- [ ] CA-6. La interfaz está en español y en blanco y negro.

## Fuera de alcance

- Inicio de sesión y roles (spec 007): en esta spec todas las pantallas son de agencia.
- Borrar clientes (se desactivan en una spec posterior si hace falta).
- Estado en vivo del sitio (spec 008).

## Demo de cierre

1. Clonar el repo y ejecutar un solo comando.
2. Abrir la consola: aparecen La Sazón, El Tornillo y Dental Popayán.
3. Registrar un cliente nuevo con su proyecto, servicio y plan Básico.
4. Abrir el detalle de La Sazón: plan Premium, SLO 99,9 % y SLA P1 de 15 min / 4 h.

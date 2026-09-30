# 008 · Monitoreo e incidente automático

> **Acciona:** Sistemas (DevSecOps / SRE, Backend) · Industrial valida el cálculo del SLA
>
> **Módulo:** 4 (incidentes manuales pueden adelantarse) · **Requerimientos:** RF-11, RF-12, RF-13, RNF-07 · **Depende de:** 000, 003, 004 · **Estado:** Spec y plan

## Qué y por qué

La agencia se entera de una caída antes que el cliente. El sistema vigila cada sitio, abre el
incidente solo, arranca el reloj del SLA con la hora real (principio 7) y registra cuándo se
recuperó. Mientras llega el monitoreo, los incidentes se pueden abrir a mano (regla de desacople).

## Actores

| Actor | Qué hace en esta spec |
|---|---|
| Sistema de monitoreo | Detecta la falla y avisa al Hub |
| Técnico de la agencia | Recibe el incidente, lo atiende y lo mitiga |

## Historias de usuario

- **HU-1.** Como técnico, quiero que una caída abra un incidente sola, para no depender de que el
  cliente llame.
- **HU-2.** Como técnico, quiero ver el reloj de SLA del incidente corriendo, para saber cuánto
  margen tengo.
- **HU-3.** Como técnico, quiero ver alertas, registros y el último cambio del servicio en el
  incidente, para diagnosticar rápido.
- **HU-4.** Como técnico, quiero abrir un incidente a mano, para cuando la falla no la detecta el
  monitoreo.

## Criterios de aceptación

- [ ] CA-1. Cada sitio se revisa al menos cada 15 segundos.
- [ ] CA-2. Con la v2 rota desplegada, en **1 minuto o menos** se crea un incidente **P1** con hora
  de inicio, cliente y servicio.
- [ ] CA-3. Si llegan más alertas de la misma falla, no se crean incidentes duplicados.
- [ ] CA-4. El reloj del SLA (respuesta 15 min, solución 4 h para P1) corre con hora real y se
  muestra en el incidente.
- [ ] CA-5. El servicio pasa a `caido` al abrir el incidente y a `operativo` al recuperarse.
- [ ] CA-6. Al recuperarse el sitio, el incidente registra la hora de mitigación y pasa a `mitigado`.
- [ ] CA-7. El incidente muestra una línea de tiempo (detectado, tomado, acciones, recuperado) y
  enlaces a los registros y al último cambio.
- [ ] CA-8. Se puede abrir un incidente manual con prioridad elegida.

## Fuera de alcance

- Rollback (spec 009), redacción con IA (spec 012).
- Notificaciones por SMS o correo.

## Demo de cierre

1. Desplegar la v2 de La Sazón.
2. Cronómetro: en ≤ 1 min aparece el incidente P1 en la consola con el reloj de SLA corriendo.
3. Abrir la línea de tiempo, los registros del sitio y el último cambio.
4. Volver a v1 a mano: el incidente pasa a `mitigado` con su hora.

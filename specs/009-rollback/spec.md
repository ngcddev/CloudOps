# 009 · Recuperación por rollback

> **Acciona:** Sistemas (Cloud / Platform, Backend, Frontend)
>
> **Módulo:** 4 · **Requerimientos:** RF-14 · **Depende de:** 005, 007, 008 · **Estado:** En curso

## Qué y por qué

Volver a la versión estable con un clic desde el incidente y dejar registro. Es la segunda mitad del
caso del restaurante del módulo 4: la v2 rota tumbó el sitio (spec 008) y aquí se recupera, con el
tiempo entre la caída y la recuperación (MTTR) medido de verdad (principio 7).

El rollback cumple el principio 3: el Hub no toca el clúster, escribe un commit en `hub-gitops` y
Argo CD hace el resto. Cada paso lo firma quien pulsó el botón (spec 007).

## Actores

| Actor | Qué hace en esta spec |
|---|---|
| Técnico de la agencia | Ejecuta el rollback desde el incidente |
| Cliente PyME | Ve su sitio recuperado; el mensaje con el tiempo que tomó se lo envía la agencia |

## Historias de usuario

- **HU-1.** Como técnico, quiero un botón de rollback en el incidente, para recuperar el servicio
  sin pasos manuales.
- **HU-2.** Como técnico, quiero ver a qué versión se va a volver antes de confirmar.
- **HU-3.** Como administrador, quiero que el incidente muestre su MTTR, para medir el servicio.
- **HU-4.** Como técnico, quiero un mensaje listo para el cliente con las horas reales, para
  avisarle sin redactarlo desde cero.

## Criterios de aceptación

- [ ] CA-1. El incidente muestra la versión actual, la versión a la que se vuelve y un botón
  **Rollback** con confirmación. Si no hay a dónde volver, o ya hay un rollback en curso, el botón
  queda deshabilitado y dice por qué.
- [ ] CA-2. Al confirmar, el Hub escribe en el repositorio de configuración un commit que deja el
  sitio en la versión de destino; nadie toca el clúster ni el repositorio a mano.
- [ ] CA-3. La plataforma vuelve a la versión de destino, la verificación de salud vuelve a verde y
  el incidente muestra el avance: «Enviado → Sincronizando → Recuperado».
- [ ] CA-4. El incidente pasa a `mitigado` con su hora real y muestra su **MTTR en minutos**; el
  servicio vuelve a `operativo`.
- [ ] CA-5. El rollback queda en la bitácora (usuario, hora, versión de origen y de destino), en el
  historial de versiones del servicio (como restauración, a nombre de quien lo pidió) y en la línea
  de tiempo del incidente.
- [ ] CA-6. Si había un cambio en validación hacia la versión rota, queda como «No se pudo
  publicar» con una nota que remite al incidente; no bloquea cambios posteriores.
- [ ] CA-7. El mensaje al cliente se genera con la plantilla de la misión (horas y minutos reales,
  hora de Colombia), en el lenguaje del [glosario](../../docs/glosario.md), y se puede copiar; nunca
  se envía solo.
- [ ] CA-8. No se pueden lanzar dos rollbacks a la vez sobre el mismo servicio.
- [ ] CA-9. Si el monitoreo no confirma la recuperación (sonda apagada o alerta ya cerrada), el
  técnico puede mitigar a mano un incidente cuyo rollback ya se confirmó en Argo CD.

## Fuera de alcance

- Rollback de la base de datos.
- Elegir a mano la versión de destino de una lista (solo vuelve a la última estable).
- Rollback automático sin que una persona lo pida.
- Enviar el mensaje al cliente por correo o chat; redactarlo con IA (spec 012).

## Demo de cierre

1. Con el incidente P1 de La Sazón abierto (spec 008), abrir su detalle y ver «v2 → v1».
2. Pulsar **Rollback** y confirmar.
3. Mostrar el commit de `revert` en Gitea y la sincronización en Argo CD.
4. El sitio vuelve a responder; el incidente queda `mitigado` con su hora y su MTTR.
5. Mostrar el mensaje al cliente con horas reales, y el rollback en la bitácora y en el historial.

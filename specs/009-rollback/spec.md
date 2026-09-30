# 009 · Recuperación por rollback

> **Módulo:** 4 · **Requerimientos:** RF-14 · **Depende de:** 005, 008 · **Estado:** Spec y plan

## Qué y por qué

Volver a la última versión estable con un clic desde el incidente y dejar registro. Es el corazón
del caso demo: el tiempo entre la caída y la recuperación (MTTR) se mide de verdad.

## Actores

| Actor | Qué hace en esta spec |
|---|---|
| Técnico de la agencia | Ejecuta el rollback desde el incidente |
| Cliente PyME | Ve su sitio recuperado y el tiempo que tomó |

## Historias de usuario

- **HU-1.** Como técnico, quiero un botón de rollback en el incidente, para recuperar el servicio
  sin pasos manuales.
- **HU-2.** Como técnico, quiero ver a qué versión se va a volver antes de confirmar.
- **HU-3.** Como administrador, quiero que el incidente guarde su MTTR, para medir el servicio.

## Criterios de aceptación

- [ ] CA-1. El incidente muestra la versión actual, la última estable y un botón **Rollback** con
  confirmación.
- [ ] CA-2. Al confirmar, se revierte el último cambio en el repositorio de configuración; nadie
  toca el clúster.
- [ ] CA-3. La plataforma vuelve a la versión estable y la verificación de salud vuelve a verde.
- [ ] CA-4. El incidente pasa a `mitigado` con su hora y su **MTTR en minutos**; el servicio vuelve
  a `operativo`.
- [ ] CA-5. El rollback queda en la bitácora (usuario, hora, versión origen y destino) y en el
  historial de versiones.
- [ ] CA-6. El mensaje al cliente se genera con la plantilla de la constitución (horas y minutos
  reales).

## Fuera de alcance

- Rollback de base de datos.
- Rollback a una versión elegida de una lista (solo a la última estable).

## Demo de cierre

1. Con el incidente P1 de La Sazón abierto (spec 008), pulsar **Rollback** y confirmar v1.
2. Mostrar el commit de revert en Gitea y la sincronización en Argo CD.
3. La métrica vuelve a verde; el incidente queda `mitigado` con su MTTR.
4. Mostrar el mensaje al cliente con horas reales.

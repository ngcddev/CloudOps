# 008 · Monitoreo e incidente automático

> **Acciona:** Sistemas (DevSecOps / SRE, Backend, Frontend) · Industrial valida el cálculo del SLA
>
> **Módulo:** 4 (los incidentes manuales y sus pantallas pueden adelantarse) · **Requerimientos:** RF-11, RF-12, RF-13, RNF-07 · **Depende de:** 000, 003, 004, 005, 007 · **Estado:** Tareas listas

## Qué y por qué

La agencia se entera de una caída antes que el cliente. El sistema vigila cada sitio, abre el
incidente solo, arranca el reloj del SLA con la hora real (principio 7) y registra cuándo se
recuperó. Los incidentes también se pueden abrir a mano, y esa parte funciona aunque el monitoreo
esté apagado (regla de desacople).

Es la primera mitad del caso del restaurante del módulo 4: **v2 rota → alerta → incidente P1**. La
segunda mitad (rollback y MTTR) es la spec 009.

## Actores

| Actor | Qué hace en esta spec |
|---|---|
| Sistema de monitoreo | Revisa cada sitio, detecta la falla y avisa al Hub |
| Técnico de la agencia | Recibe el incidente, lo toma, lo atiende, lo mitiga y lo cierra |

## Historias de usuario

- **HU-1.** Como técnico, quiero que una caída abra un incidente sola, para no depender de que el
  cliente llame.
- **HU-2.** Como técnico, quiero ver el reloj de SLA del incidente corriendo, para saber cuánto
  margen tengo.
- **HU-3.** Como técnico, quiero ver la línea de tiempo, los registros del sitio y el último cambio
  del servicio en el incidente, para diagnosticar rápido.
- **HU-4.** Como técnico, quiero abrir un incidente a mano, para cuando la falla no la detecta el
  monitoreo.
- **HU-5.** Como técnico, quiero cerrar el incidente dejando la causa raíz, para que quede la
  lección.

## Criterios de aceptación

- [ ] CA-1. Cada sitio se revisa al menos cada 15 segundos.
- [ ] CA-2. Con la v2 rota publicada, en **1 minuto o menos** se crea un incidente **P1** con hora
  de inicio, cliente y servicio.
- [ ] CA-3. Si llegan más avisos de la misma falla, no se crean incidentes duplicados.
- [ ] CA-4. El reloj del SLA (respuesta 15 min, solución 4 h para P1) corre con hora real y se
  muestra en el incidente como «a tiempo», «en riesgo», «vencido» o «cumplido», con texto e ícono.
  La respuesta se cumple al tomar el incidente; la solución, al mitigarlo.
- [ ] CA-5. El servicio pasa a `caido` al abrirse el incidente por la alerta y a `operativo` al
  recuperarse; la consola de servicios lo muestra.
- [ ] CA-6. Al recuperarse el sitio, el incidente registra la hora real de mitigación y pasa a
  `mitigado` sin que nadie lo toque.
- [ ] CA-7. El incidente muestra una línea de tiempo (detectado, tomado, notas, recuperado,
  cerrado) y enlaces a los registros del sitio y al último cambio del servicio.
- [ ] CA-8. Se puede abrir un incidente manual eligiendo servicio y prioridad, y mitigarlo a mano.
- [ ] CA-9. **Una publicación sana no abre ningún incidente**, aunque el sitio se reinicie unos
  segundos durante el cambio.
- [ ] CA-10. Un incidente solo se cierra desde `mitigado` y con causa raíz; crear, tomar, mitigar y
  cerrar quedan en la bitácora (spec 007) y el cliente no ve nada de esto.
- [ ] CA-11. Con el monitoreo apagado, los incidentes manuales y sus pantallas siguen funcionando.

## Fuera de alcance

- Rollback (spec 009), redacción con IA (spec 012) y dashboards (spec 010).
- Notificaciones por SMS o correo.
- Estado `degradado` automático: el monitoreo solo distingue «responde» de «no responde».
- Incidentes semilla: el MTTR solo sale de incidentes reales (principio 7).

## Demo de cierre

1. Con La Sazón en v1 y su servicio `operativo`, aprobar en el Hub el cambio a la v2 (ya pasó la
   puerta de seguridad, que no mira la salud).
2. Cronómetro: en ≤ 1 min aparece el incidente P1 en la consola, con el reloj de SLA corriendo y el
   servicio en «No disponible».
3. Tomar el incidente; abrir la línea de tiempo, los registros del sitio y el último cambio.
4. Volver a v1 con `git revert` en Gitea (la spec 009 pondrá el botón): el incidente pasa a
   `mitigado` con su hora y el servicio a `operativo`.
5. Cerrar el incidente con su causa raíz y verlo en la bitácora.
6. Publicar una versión sana (v1.1 de El Tornillo): no aparece ningún incidente.

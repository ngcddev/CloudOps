# 006 · Puerta de calidad y seguridad

> **Acciona:** Sistemas (DevSecOps / SRE, Backend, Frontend)
>
> **Módulo:** 3 · **Requerimientos:** RF-08, RF-09, RNF-05, RNF-06 · **Depende de:** 005 · **Estado:** Terminada

## Qué y por qué

Un cambio inseguro nunca llega a producción, y el Hub dice por qué (principio 4). La agencia puede
demostrarle al cliente que cada publicación pasó controles, y guarda la evidencia.

Hoy (spec 005) aprobar un cambio publica cualquier versión que exista en el registro, sin revisarla.
Con esta spec, cada versión nueva de un sitio pasa una puerta automática de controles en cuanto el
técnico la sube, y el Hub solo deja aprobar las versiones que la pasaron.

## Actores

| Actor | Qué hace en esta spec |
|---|---|
| Técnico de la agencia | Sube una versión nueva del sitio, lee el resultado de los controles y aprueba |
| Puerta de seguridad | Revisa la versión, firma la imagen y avisa al Hub de cada control |
| Cliente PyME | Ve que una actualización fue detenida por seguridad, sin jerga |

## Historias de usuario

- **HU-1.** Como técnico, quiero que cada versión pase controles automáticos antes de poder
  publicarse, para no depender de revisar a mano.
- **HU-2.** Como técnico, quiero ver en el Hub qué control falló y por qué, para corregirlo rápido.
- **HU-3.** Como agencia, quiero guardar la evidencia de cada control, para mostrarla en los
  reportes.
- **HU-4.** Como cliente, quiero saber que una actualización se detuvo por seguridad, en palabras
  simples.

## Criterios de aceptación

- [x] CA-1. Una versión con una contraseña o token en sus cambios es **bloqueada** antes de construir
  la imagen.
- [x] CA-2. Una imagen con vulnerabilidades **críticas** es bloqueada.
- [x] CA-3. Una imagen sin firma válida no pasa la verificación y **no se puede publicar**.
- [x] CA-4. Cada imagen que pasa la puerta tiene guardado su inventario de componentes (SBOM) y los
  reportes de los demás controles, y se pueden abrir desde el Hub.
- [x] CA-5. El Hub muestra los controles de cada versión (pasó / falló, con un resumen). Una
  solicitud de cambio hacia una versión que falló pasa a `rechazada` con el control que falló; el
  cliente ve el texto del [glosario](../../docs/glosario.md) para ese control.
- [x] CA-6. El Hub no deja aprobar una versión que no pasó la puerta (o que aún no termina) y lo dice.
- [x] CA-7. Un Pod que intenta correr como root es rechazado por la plataforma.
- [x] CA-8. Ningún secreto del proyecto está en el repositorio; se usan variables de entorno y
  secretos de la plataforma.

## Fuera de alcance

- Verificación de firma dentro del clúster (admission controller): mejora futura documentada.
- Probar que la versión funciona: la puerta revisa seguridad, no salud. La v2 rota pasa los
  controles a propósito (su falla es la que detecta el monitoreo del módulo 4).
- Pruebas de penetración.

## Demo de cierre

1. En el sitio de El Tornillo, subir una versión con una contraseña en un archivo: la puerta falla en
   el control de secretos, la solicitud de cambio queda "rechazada por seguridad" y el cliente ve
   "Una actualización fue detenida porque contenía información sensible."
2. Subir una versión limpia: pasa secretos, vulnerabilidades, SBOM, firma y verificación; se aprueba
   en el Hub y se publica como en la 005.
3. Abrir desde el Hub la evidencia guardada de la versión publicada.
4. Intentar correr un Pod como root en `cliente-ferreteria`: la plataforma lo rechaza.

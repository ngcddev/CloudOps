# 006 · Puerta de calidad y seguridad

> **Acciona:** Sistemas (DevSecOps / SRE, Backend)
>
> **Módulo:** 3 · **Requerimientos:** RF-08, RF-09, RNF-05, RNF-06 · **Depende de:** 005 · **Estado:** Spec y plan

## Qué y por qué

Un cambio inseguro nunca llega a producción, y el Hub dice por qué (principio 4). La agencia puede
demostrarle al cliente que cada publicación pasó controles, y guarda la evidencia.

## Actores

| Actor | Qué hace en esta spec |
|---|---|
| Técnico de la agencia | Sube cambios y lee el motivo de un rechazo |
| Cliente PyME | Ve que una actualización fue detenida por seguridad, sin jerga |

## Historias de usuario

- **HU-1.** Como técnico, quiero que cada cambio pase controles automáticos antes de publicarse,
  para no depender de revisar a mano.
- **HU-2.** Como técnico, quiero ver en el Hub por qué se rechazó un cambio, para corregirlo rápido.
- **HU-3.** Como administrador, quiero guardar la evidencia de cada control, para mostrarla en los
  reportes.
- **HU-4.** Como cliente, quiero saber que una actualización se detuvo por seguridad, en palabras
  simples.

## Criterios de aceptación

- [ ] CA-1. Un commit con una contraseña o token es **bloqueado** antes de construir la imagen.
- [ ] CA-2. Una imagen con vulnerabilidades **críticas** es bloqueada.
- [ ] CA-3. Una imagen sin firma válida no pasa la verificación y **no se publica**.
- [ ] CA-4. Cada imagen publicada tiene su inventario de componentes (SBOM) guardado.
- [ ] CA-5. El Hub marca el cambio como `rechazada` con el control que falló y un resumen; el
  cliente ve "detenida por controles de seguridad".
- [ ] CA-6. Un Pod que intenta correr como root es rechazado por la plataforma.
- [ ] CA-7. Ningún secreto del proyecto está en el repositorio; se usan variables de entorno y
  secretos de la plataforma.

## Fuera de alcance

- Verificación de firma dentro del clúster (admission controller): mejora futura documentada.
- Pruebas de penetración.

## Demo de cierre

1. Subir un commit con una contraseña al sitio de El Tornillo: el pipeline falla en el control de
   secretos y el Hub muestra "rechazado por seguridad".
2. Subir un cambio limpio: pasa escaneo, SBOM, firma y verificación; se publica.
3. Abrir la evidencia guardada del cambio publicado.

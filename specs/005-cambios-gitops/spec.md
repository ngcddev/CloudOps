# 005 · Cambios por GitOps

> **Acciona:** Sistemas (Cloud / Platform, Backend)
>
> **Módulo:** 2 · **Requerimientos:** RF-06, RF-07, RF-22, RNF-04 · **Depende de:** 003, 004 · **Estado:** Spec y plan

## Qué y por qué

Aprobar una solicitud de cambio en el Hub publica la nueva versión del sitio sin que nadie toque el
clúster a mano (principio 3). Toda la configuración vive en Git, así cada publicación queda
registrada y se puede revertir.

## Actores

| Actor | Qué hace en esta spec |
|---|---|
| Cliente PyME | Pide un cambio en su sitio |
| Técnico de la agencia | Aprueba o rechaza el cambio y sigue su publicación |

## Historias de usuario

- **HU-1.** Como técnico, quiero aprobar un cambio y que se publique solo, para no ejecutar pasos
  manuales en el servidor.
- **HU-2.** Como técnico, quiero ver qué versión corre en cada cliente y si está sincronizada, para
  saber el estado real sin entrar al clúster.
- **HU-3.** Como administrador, quiero un catálogo de clientes y servicios, para ver de un vistazo
  qué opera la agencia.

## Criterios de aceptación

- [ ] CA-1. Una solicitud de cambio pasa por `pendiente → aprobada → en_validacion → desplegada`
  (o `rechazada`), con hora y usuario en cada paso.
- [ ] CA-2. Al aprobar un cambio, el Hub actualiza la versión del cliente en el repositorio de
  configuración, **y en ningún otro lugar**.
- [ ] CA-3. En menos de 3 minutos, el sitio del cliente muestra la nueva versión en su pie y en
  `/health`.
- [ ] CA-4. La consola muestra, por cliente, la versión activa, el estado de sincronización y quién
  hizo el último cambio.
- [ ] CA-5. Revertir el último commit en el repositorio devuelve el sitio a la versión anterior.
- [ ] CA-6. Existe un catálogo mínimo con los 3 clientes y sus servicios, con enlace al Hub.

## Fuera de alcance

- Validaciones de seguridad (spec 006).
- Botón de rollback desde un incidente (spec 009).
- Despliegues progresivos (canary, blue/green).

## Demo de cierre

1. El Tornillo pide "publicar la nueva portada" (v1 → v1.1).
2. El técnico aprueba en el Hub.
3. Se ve el commit en Gitea, Argo CD sincroniza y el sitio muestra v1.1.
4. La consola muestra v1.1, "Sincronizado" y el nombre del técnico.

# 002 · Plantillas de sitio y apps demo

> **Acciona:** Sistemas (Cloud / Platform, Frontend)
>
> **Módulo:** 1 · **Requerimientos:** RNF-01, RNF-02 · **Depende de:** — · **Estado:** Tareas listas

## Qué y por qué

La agencia ofrece dos tipos de sitio estándar, no "cualquier repositorio". Cada cliente demo tiene
un sitio hecho con una de esas plantillas, en dos versiones: una sana y una rota a propósito. Así la
demo puede provocar una falla real y controlada, y un cliente nuevo se crea copiando una plantilla.

## Actores

| Actor | Qué hace en esta spec |
|---|---|
| Técnico de la agencia | Crea el sitio de un cliente desde una plantilla y publica sus versiones |
| Visitante del sitio | Ve la página del negocio y, en el consultorio, envía el formulario |

## Historias de usuario

- **HU-1.** Como técnico, quiero dos plantillas estándar (landing y landing con formulario), para
  crear el sitio de un cliente nuevo cambiando solo nombre, dominio y plan.
- **HU-2.** Como técnico, quiero que cada sitio diga qué versión está corriendo y si está sano, para
  que el monitoreo y el Hub lo sepan sin entrar al sitio.
- **HU-3.** Como equipo de demo, quiero una versión rota de cada sitio, para provocar una caída
  real cuando haga falta.

## Criterios de aceptación

- [ ] CA-1. Existen 2 plantillas: **landing estática** y **landing + formulario**.
- [ ] CA-2. Existen 3 sitios: La Sazón y El Tornillo (landing) y Dental Popayán (landing +
  formulario), con contenido ficticio propio de cada negocio.
- [ ] CA-3. Los 3 sitios corren en contenedores que **no usan el usuario root**.
- [ ] CA-4. Cada sitio responde en `/health` con `{"status":"ok","version":"v1"}` y muestra su
  versión en el pie de página.
- [ ] CA-5. La versión **v2** de cada sitio responde HTTP 500 en `/` y en `/health`.
- [ ] CA-6. El formulario del consultorio guarda la solicitud y responde un mensaje de confirmación.
- [ ] CA-7. Los 3 sitios se levantan con un solo comando junto con el Hub.

## Fuera de alcance

- Kubernetes, namespaces e Ingress (spec 003).
- Envío de correos desde el formulario.
- Editor de contenido para el cliente.

## Demo de cierre

1. Levantar todo con un solo comando y abrir los 3 sitios.
2. Mostrar `/health` de cada uno con `v1`.
3. Cambiar La Sazón a `v2` y mostrar el error 500.
4. Enviar el formulario del consultorio y ver la confirmación.
5. Mostrar que el contenedor corre con un usuario distinto de root.

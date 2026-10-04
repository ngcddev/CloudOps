# 003 · Plataforma multi-cliente en k3s

> **Acciona:** Sistemas (Cloud / Platform) · Industrial aporta las cuotas por plan
>
> **Módulo:** 2 · **Requerimientos:** RF-03, RNF-03 · **Depende de:** 002 · **Estado:** Terminada

## Qué y por qué

Cada cliente vive aislado en la plataforma con los recursos que paga su plan. Si el sitio de un
cliente falla o consume de más, no afecta a los demás, y la agencia puede demostrar que cada plan
recibe lo que promete.

## Actores

| Actor | Qué hace en esta spec |
|---|---|
| Técnico de plataforma | Prepara el espacio de cada cliente con sus límites y reglas |
| Cliente PyME | Accede a su sitio por su propia dirección |

## Historias de usuario

- **HU-1.** Como administrador, quiero que cada cliente tenga su propio espacio aislado, para que
  una falla de uno no toque a otro.
- **HU-2.** Como administrador, quiero que los recursos de cada espacio dependan del plan, para que
  el precio refleje lo que se entrega.
- **HU-3.** Como cliente, quiero entrar a mi sitio por su dirección de siempre.

## Criterios de aceptación

- [x] CA-1. Existe un espacio por cliente (`cliente-restaurante`, `cliente-ferreteria`,
  `cliente-consultorio`) además de los de plataforma (`hub`, `argocd`, `monitoring`, `gitea`).
- [x] CA-2. Cada espacio de cliente tiene un límite de CPU y memoria igual al de su plan (spec 000).
- [x] CA-3. Un sitio de un cliente **no puede** comunicarse por red con el de otro cliente.
- [x] CA-4. Un contenedor que intenta correr como root o con privilegios es **rechazado**.
- [x] CA-5. Cada sitio responde en su dirección (`restaurante.hub.local`, `ferreteria.hub.local`,
  `consultorio.hub.local`) y el Hub en `hub.local`.
- [x] CA-6. Un sitio solo recibe tráfico cuando su verificación de salud responde bien.

## Fuera de alcance

- Varios nodos o alta disponibilidad.
- Certificados TLS reales y dominios públicos.
- Despliegue automático desde Git (spec 005): aquí se aplica una sola vez para validar.

## Demo de cierre

1. Listar los espacios y mostrar la cuota de cada cliente según su plan.
2. Abrir los 3 sitios y el Hub por su dirección.
3. Desde el sitio del restaurante, intentar llegar al de la ferretería: falla.
4. Intentar lanzar un contenedor como root en `cliente-restaurante`: es rechazado.

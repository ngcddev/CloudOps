# 011 · Infraestructura como código

> **Acciona:** Sistemas (Cloud / Platform)
>
> **Módulo:** 4 · **Requerimientos:** RNF-08 · **Depende de:** 003, 005 · **Estado:** Tareas listas

## Qué y por qué

El entorno de cada cliente se recrea desde código. Si un espacio se daña o llega un cliente nuevo, la agencia
no depende de la memoria de nadie: un comando lo deja listo e idéntico. Hoy crear un cliente exige copiar una
carpeta de `gitops/clients/`, editar parches a mano, subirla a Gitea y aplicar una `Application` de Argo CD;
esta spec lo convierte en una sola operación repetible.

La frontera con GitOps (principio 3) se mantiene: el código de infraestructura **no** toca Deployments,
Services ni Ingress. Crea el punto de entrada del cliente (su carpeta de configuración en `hub-gitops` y su
`Application` de Argo CD) y Argo CD reconcilia el resto, incluidos el namespace, la cuota, los límites y la
política de red que ya definen las plantillas de la 003.

## Actores

| Actor | Qué hace en esta spec |
|---|---|
| Técnico de plataforma | Crea, recrea o elimina el entorno de un cliente |

## Historias de usuario

- **HU-1.** Como técnico, quiero crear el entorno de un cliente nuevo con un solo comando, indicando nombre,
  dominio y plan.
- **HU-2.** Como técnico, quiero borrar y recrear el entorno de un cliente y que quede igual.

## Criterios de aceptación

- [ ] CA-1. Un comando con nombre, dominio y plan deja al cliente nuevo con su carpeta en `hub-gitops`, su
  `Application` de Argo CD y, ya reconciliado, su namespace con cuota, límites, aislamiento de red y política
  de seguridad (`restricted`) según el plan.
- [ ] CA-2. Borrar y volver a crear el entorno de un cliente deja todo igual: sin diferencias en el plan de
  ejecución y con el sitio respondiendo de nuevo.
- [ ] CA-3. Un segundo comando sin cambios no modifica nada.
- [ ] CA-4. El estado de la infraestructura y las credenciales no quedan en el repositorio.
- [ ] CA-5. El mismo código funciona con OpenTofu y con Terraform.
- [ ] CA-6. Las cuotas de cada plan salen de `seed/plans.json` (una sola fuente), no se repiten en el código.
- [ ] CA-7. Los tres clientes que ya existen se pueden administrar con el código sin recrearlos ni
  interrumpir su sitio.
- [ ] CA-8. El comando falla con un mensaje claro si el nombre ya existe, el plan no existe o el dominio no
  termina en `.hub.local`.

## Fuera de alcance

- Crear las máquinas, el clúster o la red del laboratorio.
- Nubes públicas.
- Dar de alta al cliente en el Hub (eso se hace desde la pantalla de clientes de la 001; esta spec solo
  prepara su entorno).
- Instalar la plataforma (Argo CD, Gitea, monitoreo): ya la entregan las specs 003, 005 y 008.

## Demo de cierre

1. Crear el cliente nuevo «Panadería El Trigo» (plan Básico) con un comando.
2. Mostrar en Gitea su carpeta, en Argo CD su `Application` `Synced` y `Healthy`, y su namespace con la cuota.
3. Destruir y recrear el entorno de El Tornillo: el plan final no muestra diferencias y el sitio responde.
4. Repetir el comando de creación: «0 para cambiar».
5. Correr lo mismo con Terraform.

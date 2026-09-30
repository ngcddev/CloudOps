# 011 · Infraestructura como código

> **Acciona:** Sistemas (Cloud / Platform)
>
> **Módulo:** 4 · **Requerimientos:** RNF-08 · **Depende de:** 003 · **Estado:** Spec y plan

## Qué y por qué

El entorno de cada cliente se recrea desde código. Si un espacio se daña o llega un cliente nuevo,
la agencia no depende de la memoria de nadie: un comando lo deja listo e idéntico.

## Actores

| Actor | Qué hace en esta spec |
|---|---|
| Técnico de plataforma | Crea, recrea o elimina el entorno de un cliente |

## Historias de usuario

- **HU-1.** Como técnico, quiero crear el entorno de un cliente nuevo con un solo comando, indicando
  nombre, dominio y plan.
- **HU-2.** Como técnico, quiero borrar y recrear el entorno de un cliente y que quede igual.

## Criterios de aceptación

- [ ] CA-1. Un comando con nombre, dominio y plan crea el espacio del cliente con cuota, límites,
  aislamiento de red, política de seguridad y registro en la configuración GitOps.
- [ ] CA-2. Borrar y volver a crear el entorno de un cliente deja todo igual (sin diferencias en
  el plan de ejecución).
- [ ] CA-3. Un segundo comando sin cambios no modifica nada.
- [ ] CA-4. El estado de la infraestructura no queda en el repositorio.
- [ ] CA-5. El mismo código funciona con OpenTofu y con Terraform.

## Fuera de alcance

- Crear las máquinas o la red del laboratorio.
- Nubes públicas.

## Demo de cierre

1. Crear un cliente nuevo "Panadería El Trigo" (plan Básico) con un comando.
2. Mostrar su namespace, cuota y política.
3. Destruir y recrear el entorno de El Tornillo: el plan final no muestra diferencias.

# Misión

## Qué construimos

**CloudOps Client Hub** es un centro de operación de servicios digitales para agencias web que atienden
a varias PyMEs. Gestiona clientes, planes, solicitudes, cambios, despliegues, monitoreo, incidentes,
recuperación, SLA y reportes.

**No es otro Vercel**: el despliegue es una capacidad interna, no el producto.

Es el proyecto integrador del diplomado **CloudForge AI 5.0** (Unicomfacauca, 28 sep – 30 nov 2026),
hecho por un equipo de 5: 4 ingenieros de sistemas y 1 ingeniero industrial.

## La pregunta que responde

> "Tengo varios clientes, ¿cómo organizo su soporte, detecto problemas, cumplo tiempos y explico el
> valor del servicio?"

## Para quién

| Rol | Quién es | Qué ve |
|---|---|---|
| `agencia` | Administrador y técnico de la agencia (Forja Digital) | Todo: todos los clientes, tickets, cambios, incidentes y métricas |
| `cliente` | Usuario de una PyME | Solo lo suyo, en lenguaje de negocio ([glosario](../docs/glosario.md)) |

## Qué lo hace distinto de Vercel

| Vercel | CloudOps Client Hub |
|---|---|
| El producto es el despliegue | El producto es el servicio: el despliegue es un paso más |
| Empieza en el repositorio | Empieza en el cliente: cliente → proyecto → servicio → acuerdo (plan + SLA) |
| Acepta cualquier repositorio | Solo dos plantillas estándar de servicio |
| Métricas para desarrolladores | SLA, MTTR y disponibilidad explicados al cliente |
| Servicio de terceros | Infraestructura propia, sin dependencias externas |

## Caso demo de referencia

El sitio del Restaurante La Sazón cae tras desplegar la `v2`:

1. Blackbox Exporter detecta HTTP 500 → Alertmanager avisa al Hub en ≤ 1 min.
2. El Hub abre un incidente **P1** y arranca el SLA (respuesta 15 min, solución 4 h) con hora real.
3. El técnico revisa alertas, logs y el último cambio.
4. Pulsa **Rollback**: el Hub hace `git revert` en `hub-gitops`, Argo CD reconcilia a `v1`.
5. La métrica vuelve a verde, el incidente se cierra con su MTTR.
6. El cliente recibe: *"Detectamos una falla temporal en su sitio a las {hora}. Activamos la recuperación y a las {hora_fin} el servicio volvió a funcionar. Tiempo total: {min} minutos."*
7. El caso queda en el reporte mensual y en la infografía.

## Éxito del proyecto

- La demo final muestra los 10 puntos del caso integrador en menos de 15 minutos ([roadmap](roadmap.md)).
- Cada módulo cierra con una demo de 3 a 5 minutos que conecta lo nuevo con el producto.
- Todo arranca desde datos semilla y es reproducible en otra máquina.

## Fuera de alcance

CDN, serverless, escala global, dominios reales, pagos y facturación (RF-24), video y 3D, multi-agencia.

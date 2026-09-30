# 010 · Dashboards y métricas del servicio

> **Acciona:** Sistemas (Frontend, Backend) · Industrial define los KPI y hace la prueba con personas no técnicas
>
> **Módulo:** 4 (vistas pueden adelantarse con datos del Hub) · **Requerimientos:** RF-15, RF-16, RF-17, RNF-10 · **Depende de:** 008, 009 · **Estado:** Spec y plan

## Qué y por qué

La agencia ve la operación completa en una pantalla y el cliente ve un resumen claro de su servicio,
sin jerga (principio 8). Convierte el mantenimiento web en un servicio medible.

## Actores

| Actor | Qué hace en esta spec |
|---|---|
| Administrador / técnico | Revisa SLA, MTTR, carga y costo |
| Cliente PyME | Revisa el estado y la disponibilidad de su sitio |

## Historias de usuario

- **HU-1.** Como administrador, quiero ver cumplimiento de SLA, MTTR, tickets, carga por técnico y
  costo por cliente, para decidir dónde mejorar.
- **HU-2.** Como técnico, quiero ver el estado de todos los sitios de un vistazo.
- **HU-3.** Como cliente, quiero saber si mi sitio está bien, cuánto estuvo disponible este mes y
  qué incidentes hubo, explicado en palabras simples.

## Criterios de aceptación

- [ ] CA-1. La consola muestra por cliente: estado del sitio, disponibilidad del mes vs. SLO,
  cumplimiento de SLA, MTTR, tickets abiertos/cerrados, horas y costo.
- [ ] CA-2. La consola muestra la carga por técnico (horas registradas vs. disponibles).
- [ ] CA-3. Los KPI usan exactamente las fórmulas de la spec 000.
- [ ] CA-4. El portal del cliente muestra: estado actual, disponibilidad del mes frente al objetivo,
  incidentes del mes y solicitudes, todo con los textos del glosario.
- [ ] CA-5. Una persona sin formación técnica entiende el portal: prueba con 3 personas, al menos 2
  explican correctamente el estado de su sitio.
- [ ] CA-6. Existe un detalle técnico (gráficas de disponibilidad y latencia) accesible desde la
  consola.

## Fuera de alcance

- Dashboards configurables por el usuario.
- Históricos de más de 3 meses.

## Demo de cierre

1. Consola: La Sazón con el incidente del día, MTTR y SLA cumplido.
2. Carga por técnico y costo por cliente.
3. Portal de La Sazón: "Su sitio se mantuvo disponible dentro del objetivo acordado" y el incidente
   explicado sin jerga.

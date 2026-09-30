# 013 · Reportes operativo y ejecutivo

> **Módulo:** 5 (puede adelantarse con datos del Hub) · **Requerimientos:** RF-20 · **Depende de:** 010 · **Estado:** Spec y plan

## Qué y por qué

Un reporte mensual para la agencia (cómo operamos) y otro para cada cliente (qué valor recibió).
Es la prueba concreta de que el mantenimiento web es un servicio medible.

## Actores

| Actor | Qué hace en esta spec |
|---|---|
| Administrador de la agencia | Genera y revisa el reporte operativo |
| Cliente PyME | Recibe su reporte ejecutivo |

## Historias de usuario

- **HU-1.** Como administrador, quiero un reporte operativo con los KPI del mes, para mejorar el
  proceso y decidir precios.
- **HU-2.** Como cliente, quiero una página con la disponibilidad, los incidentes y los cambios del
  mes, en palabras simples, para entender qué pago.

## Criterios de aceptación

- [ ] CA-1. El reporte operativo muestra los KPI de la spec 000 por cliente y total, con el mes
  anterior como comparación.
- [ ] CA-2. El reporte ejecutivo cabe en **una página** y resume disponibilidad vs. objetivo,
  incidentes (con el texto aprobado), cambios publicados y solicitudes atendidas.
- [ ] CA-3. El reporte ejecutivo no contiene jerga (glosario).
- [ ] CA-4. Ambos se generan para cualquier mes y cliente y se pueden descargar en PDF.
- [ ] CA-5. Los números coinciden con los de los dashboards (spec 010).

## Fuera de alcance

- Envío automático programado.
- Reportes personalizables.

## Demo de cierre

1. Generar el reporte operativo del mes: SLA, MTTR, carga y costo por cliente.
2. Generar el ejecutivo de La Sazón y descargar el PDF: una página, sin jerga, con el incidente del
   día explicado.

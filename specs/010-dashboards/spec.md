# 010 · Dashboards y métricas del servicio

> **Acciona:** Sistemas (Frontend, Backend) · Industrial define los KPI y hace la prueba con personas no técnicas
>
> **Módulo:** 4 (las vistas con datos del Hub se pueden adelantar) · **Requerimientos:** RF-15, RF-16, RF-17, RNF-10 · **Depende de:** 004, 005, 007, 008, 009 · **Estado:** Tareas listas

## Qué y por qué

La agencia ve la operación completa en una pantalla y el cliente ve un resumen claro de su servicio, sin
jerga (principio 8). Convierte el mantenimiento web en un servicio medible, con números reales (principio 7):
la disponibilidad sale de las sondas de la 008, el MTTR de los incidentes reales (008 y 009) y las horas de lo
que el equipo registra en las solicitudes (004).

Regla de desacople: si Prometheus no responde, las tarjetas de disponibilidad dicen «sin datos» y todo lo
demás sigue funcionando.

## Actores

| Actor | Qué hace en esta spec |
|---|---|
| Administrador / técnico | Revisa SLA, MTTR, carga y costo de todos los clientes |
| Cliente PyME | Revisa el estado y la disponibilidad de su sitio, explicados en palabras simples |

## Historias de usuario

- **HU-1.** Como administrador, quiero ver cumplimiento de SLA, MTTR, tickets, carga por técnico y costo por
  cliente, para decidir dónde mejorar.
- **HU-2.** Como técnico, quiero ver el estado de todos los sitios de un vistazo.
- **HU-3.** Como cliente, quiero saber si mi sitio está bien, cuánto estuvo disponible este mes y qué
  incidentes hubo, explicado en palabras simples.

## Criterios de aceptación

- [ ] CA-1. La consola muestra por cliente: estado del sitio, disponibilidad del mes frente al objetivo de su
  plan, cumplimiento de SLA, MTTR, solicitudes abiertas/cerradas, horas y costo.
- [ ] CA-2. La consola muestra la carga por técnico (horas registradas vs. disponibles del mes).
- [ ] CA-3. Los KPI usan exactamente las fórmulas de `docs/kpi.md` (spec 000; lo crea la T01 de esta spec si la 000 aún no lo hizo); mientras la
  000 no las cierre, rige la versión provisional de ese archivo y cualquier cambio se hace ahí primero.
- [ ] CA-4. El portal del cliente muestra: estado actual, disponibilidad del mes frente al objetivo, incidentes
  del mes y solicitudes, todo con los textos del [glosario](../../docs/glosario.md).
- [ ] CA-5. Una persona sin formación técnica entiende el portal: prueba con 3 personas, al menos 2 explican
  correctamente el estado de su sitio.
- [ ] CA-6. Existe un detalle técnico (disponibilidad, latencia y errores del sitio) accesible desde la
  consola con un enlace a Grafana.
- [ ] CA-7. Un cliente solo ve sus datos (spec 007); las cifras de costo y carga son solo de la agencia.
- [ ] CA-8. Con Prometheus apagado la consola y el portal cargan y las tarjetas de disponibilidad muestran «sin
  datos» (nunca un 100 % inventado ni un error).
- [ ] CA-9. Los incidentes semilla no existen: con cero incidentes reales el MTTR muestra «sin incidentes este
  mes», no 0.

## Fuera de alcance

- Dashboards configurables por el usuario.
- Históricos de más de 3 meses.
- Facturación y precios finales (los planes siguen sin precio; el costo usa un valor por hora parametrizado).
- Reporte ejecutivo con IA (spec 013).

## Demo de cierre

1. Consola: La Sazón con el incidente del día (el de la demo 008/009), su MTTR y el SLA.
2. Carga por técnico y costo por cliente.
3. Detalle técnico de La Sazón con el hueco de disponibilidad de la caída y el enlace a Grafana.
4. Portal de La Sazón: «Su sitio se mantuvo disponible dentro del objetivo acordado» (o la frase de «por
   debajo del objetivo», según el mes) y el incidente explicado sin jerga.
5. Apagar Prometheus: el portal sigue cargando con «sin datos» en la disponibilidad.

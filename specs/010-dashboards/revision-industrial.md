# Revisión de Industrial · KPIs y SLO de la spec 010 (T02)

> **Tarea:** T02 · Revisar con Industrial las fórmulas provisionales y registrar los cambios en
> [`docs/kpi.md`](../../docs/kpi.md).
> **Criterio:** al terminar, `docs/kpi.md` queda sin la marca «provisional, valida Industrial» **o**
> con los cambios pedidos anotados y aplicados.
> **Duración:** 30–45 minutos.
> **Quién firma:** una persona de Industrial con criterio sobre precios, capacidad y niveles de
> servicio. No hace falta que sea del área de sistemas.

Este formulario se llena en la reunión. Lo que se apruebe se aplica **primero** en `docs/kpi.md` y en
`seed/kpi_params.json`; después se corre la suite. No se cambia código de fórmulas para esta tarea.
Si Industrial no puede reunirse, puede responder por escrito las secciones 2, 3 y 4 y devolver este
archivo diligenciado: sirve igual.

## 1. Qué se está aprobando

La spec 000 todavía no cierra los KPI del servicio. Mientras eso pase, la 010 usa una **versión
provisional** documentada en `docs/kpi.md` y parametrizada en `seed/kpi_params.json`. Aprobar esta
versión significa:

- Aceptar las **fórmulas** con las que se calculan los indicadores.
- Aceptar los **valores de trabajo** (costo por hora, horas por técnico, umbral de riesgo y moneda).
- Aceptar los **objetivos de disponibilidad (SLO)** de los tres planes.

Nada de esto cambia la forma en que el cliente ve el portal: el portal nunca muestra costo ni horas
(CA-7). Los valores solo afectan la consola de la agencia.

## 2. Fórmulas (marcar una opción por fila)

| # | KPI | Fórmula provisional | Fuente | ¿Aprueba? | Si no, ¿cómo debe quedar? |
|---|---|---|---|---|---|
| 1 | Disponibilidad del mes | `avg_over_time(probe_success{client="<c>"}[<mes>]) × 100` | Prometheus / Blackbox (008) | ☐ Sí ☐ No ☐ Cambia | |
| 2 | Cumple el objetivo | Disponibilidad del mes ≥ `plans.slo_availability` | Hub (plan) + Prometheus | ☐ Sí ☐ No ☐ Cambia | |
| 3 | Latencia p95 | `histogram_quantile(0.95, sum by (le) (rate(traefik_service_request_duration_seconds_bucket{service=~"cliente-<c>-.*"}[5m])))` | Prometheus + Traefik (008) | ☐ Sí ☐ No ☐ Cambia | |
| 4 | Cumplimiento de SLA | (casos resueltos dentro del plazo ÷ casos terminados del mes) × 100; sin terminados → `null` | Hub: tickets (004) + incidentes (008, 009) | ☐ Sí ☐ No ☐ Cambia | |
| 5 | MTTR | Promedio de (`mitigación − inicio`) en minutos de los incidentes del mes en estado `mitigado`/`cerrado`; sin incidentes → `null` | Hub: incidentes (008, 009) | ☐ Sí ☐ No ☐ Cambia | |
| 6 | Solicitudes abiertas / cerradas | Conteo por estado canónico (`abierto → en_progreso → en_espera → resuelto → cerrado`) del mes | Hub: tickets (004) | ☐ Sí ☐ No ☐ Cambia | |
| 7 | Horas por cliente | Σ `work_logs.hours` de las solicitudes del cliente en el mes | Hub: `work_logs` (004) | ☐ Sí ☐ No ☐ Cambia | |
| 8 | Costo por cliente | Horas por cliente × `hourly_cost` | Hub (horas) + `kpi_params.json` | ☐ Sí ☐ No ☐ Cambia | |
| 9 | Carga por técnico | Σ `work_logs.hours` del técnico en el mes ÷ `technician_monthly_hours`; riesgo si supera `at_risk_ratio` | Hub (horas) + `kpi_params.json` | ☐ Sí ☐ No ☐ Cambia | |

### Observación conocida de la fórmula 4 (SLA)

`docs/kpi.md` y el plan de la 010 describen el SLA como **tickets + incidentes**, pero la
implementación actual (`cumplimiento_sla` en `backend/app/services/kpi.py`) **solo cuenta tickets**.
Hay que decidir una de dos:

- ☐ **Opción A:** el SLA se mide solo con tickets. Se corrige `docs/kpi.md` para que diga «tickets» y
  no hace falta tocar el código.
- ☐ **Opción B:** el SLA incluye también incidentes mitigados/cerrados. Se deja el documento como está
  y se abre una tarea de seguimiento para cambiar `kpi.py` (no se hace en T02).

Decisión de Industrial: ______________________________________________

## 3. Parámetros de trabajo

| Parámetro | Valor provisional | Unidad | ¿Aprueba? | Valor aprobado |
|---|---|---|---|---|
| `hourly_cost` | 25 000 | COP por hora de soporte | ☐ Sí ☐ No | |
| `technician_monthly_hours` | 120 | horas de soporte por técnico al mes | ☐ Sí ☐ No | |
| `at_risk_ratio` | 0,8 (80 %) | proporción de carga que se considera riesgo | ☐ Sí ☐ No | |
| `currency` | COP | moneda de los costos | ☐ Sí ☐ No | |

Preguntas para cerrar el contexto (responder aunque sea «no aplica»):

1. ¿El costo por hora incluye IVA y desplazamientos, o es costo directo?
2. ¿Las 120 horas son horas facturables, horas de soporte o jornada completa? ¿Cambian por plan?
3. ¿El 80 % de carga es el mismo umbral para los tres planes? ¿Debe sonar una alerta o solo pintarse?
4. ¿Se cobra por hora redondeada, por minuto o por bloque? (Hoy se suman las horas tal como se registran,
   sin redondeo).
5. ¿Las horas incluidas del plan (`included_hours`) se definen ahora o quedan fuera de la 010?

Respuestas:

> 1.
>
> 2.
>
> 3.
>
> 4.
>
> 5.

## 4. Objetivos de disponibilidad (SLO)

| Plan | SLO provisional | Horario de soporte | ¿Aprueba? | SLO aprobado |
|---|---|---|---|---|
| Básico | 99,0 % | lun–vie 08:00–18:00 | ☐ Sí ☐ No | |
| Estándar | 99,5 % | lun–sáb 07:00–20:00 | ☐ Sí ☐ No | |
| Premium | 99,9 % | 24×7 | ☐ Sí ☐ No | |

Preguntas:

1. ¿El SLO se mide sobre el mes calendario completo (incluidas noches y fines de semana) o solo dentro
   del horario de soporte? Hoy se mide sobre el mes completo.
2. ¿Una caída programada (mantenimiento anunciado) cuenta como indisponibilidad? Hoy **sí cuenta**.
3. ¿99,9 % en Premium es exigible con un solo nodo y sin redundancia? Si no, ¿qué valor se promete?
4. ¿Qué pasa si el cliente no contrata monitoreo? Hoy la disponibilidad queda en `null` y se muestra
   «sin datos», nunca 100 %.

Respuestas:

> 1.
>
> 2.
>
> 3.
>
> 4.

## 5. Decisiones de Industrial

Marcar una sola opción:

- ☐ **Aprueba todo tal como está.** Se quita la marca «provisional, valida Industrial» de
  `docs/kpi.md` y no se cambian valores.
- ☐ **Aprueba con cambios.** Se anotan los valores/fórmulas aprobados en las secciones 2–4, se aplican
  en `docs/kpi.md` y `seed/kpi_params.json`, y luego se quita la marca.
- ☐ **No aprueba.** Se deja la marca y se anota qué falta para volver a revisar.

Comentarios o condiciones:

> ____________________________________________________________________________
>
> ____________________________________________________________________________

## 6. Firma

| Campo | Valor |
|---|---|
| Nombre de quien revisa (Industrial) | |
| Cargo / área | |
| Fecha | |
| Correo o medio de contacto | |
| Nombre de quien registra (equipo) | |
| Fecha en que se aplicó al repositorio | |

Firma o constancia (si fue presencial, basta el nombre y la fecha; si fue por escrito, adjuntar el
correo o la captura al acta del proyecto):

> ____________________________________________________________________________

## 7. Cierre de T02 (lo hace el equipo)

1. Aplicar los cambios **primero** en `docs/kpi.md` y, si hay valores nuevos, en
   `seed/kpi_params.json`.
2. Si se aprueba todo sin cambios, quitar de `docs/kpi.md` la frase «provisional, valida Industrial»
   (incluida la columna «Estado» de las tablas) y dejar una línea con la fecha y quién aprobó.
3. Si se aprobó la opción B del SLA (incidentes incluidos), **no** cerrar T02 como si el código
   estuviera listo: dejar la marca en la fórmula 4 y abrir la tarea de seguimiento en `tasks.md` o en
   la spec 000.
4. Correr `pytest` en `backend/` para confirmar que ningún valor aprobado rompe las pruebas.
5. Marcar T02 en [`tasks.md`](tasks.md) con el nombre de quien hizo la revisión, por ejemplo:
   `- [x] T02 · … [Andres]`.
6. Guardar este formulario diligenciado en esta misma carpeta (puede ser el mismo archivo con las
   respuestas y la firma).

## 8. Hallazgos de la puesta en marcha en el clúster (26 oct 2026)

Estos hallazgos salieron al ejecutar T18 por primera vez con Prometheus real. **No cambian las
fórmulas acordadas**: son defectos de implementación o definiciones que Industrial debe confirmar.
Los dos primeros ya están corregidos en `backend/app/services/kpi.py`; el resto queda para decidir.

| # | Hallazgo | Impacto | Decisión sugerida | Dónde se corrige |
|---|---|---|---|---|
| 1 | La API consultaba `probe_success{client="cliente-restaurante"}`; Prometheus etiqueta `client="restaurante"` (sin el prefijo `cliente-`, spec 008 T22) | Disponibilidad y serie siempre `null` en el clúster | Corregido: se usa el nombre del cliente sin prefijo y hay prueba de regresión | `kpi.py`, `test_kpi.py` |
| 2 | La disponibilidad tomaba el último sondeo, no el promedio del mes; el mes solo se usaba como clave de caché | Un solo sondeo bueno mostraba 100 % aunque el mes tuviera caídas | Corregido: `avg_over_time` con la ventana del mes y `offset` para meses pasados | `kpi.py` |
| 3 | `at_risk_ratio` (0,8) está documentado como señal de riesgo, pero ni el backend ni el tablero lo aplican | La carga por técnico se muestra, pero nunca avisa del 80 % | Decidir: implementar el aviso en la consola o quitar el parámetro de `docs/kpi.md` | `docs/kpi.md` + `Dashboard.tsx` |
| 4 | Horas y costo se cuentan por el mes de **creación del ticket**, no por la fecha del registro de horas (`work_logs.created_at`) | Trabajo de octubre sobre un ticket de septiembre cae en septiembre; el costo del mes no cuadra | Confirmar que el mes del reporte es el del trabajo realizado y corregir la consulta | `kpi.py` (tarea de seguimiento) |
| 5 | El tablero escribe «120 disponibles» fijo en el texto; no lee `technician_monthly_hours` | Si Industrial aprueba otro valor, la pantalla miente | Enviar el parámetro en la respuesta de la API y mostrarlo | `dashboard` + `Dashboard.tsx` |
| 6 | La latencia p95 no tiene meta numérica («latencia elevada inicia mejora») | No se puede decir si cumple o no | Que Industrial fije un umbral por plan (por ejemplo, p95 ≤ 1 s) | `docs/kpi.md` |
| 7 | SLA: el documento dice tickets + incidentes; el código solo cuenta tickets | Dos lecturas distintas del mismo KPI | Elegir la opción A o B de la sección 2 | `docs/kpi.md` o tarea de seguimiento |

**Postura del equipo confirmada el 26 oct 2026** (pendiente de la firma de Industrial; no se aplica a
`docs/kpi.md` hasta que la firme):

- Aprobar las fórmulas 1–3 y 5–9 tal como están.
- Fórmula 4: **opción A** (SLA solo con tickets) y corregir la frase de `docs/kpi.md`.
- Aprobar los parámetros 25 000 COP/h, 120 h, 0,8 y COP; aclarar si las 120 h son de soporte.
- Aprobar los SLO 99,0 / 99,5 / 99,9 % medidos sobre el **mes calendario completo**.
- Los hallazgos 3–6 se corrigen en tareas de seguimiento, no en T02.

> **Estado de T02:** abierta. Falta la reunión con Industrial, las respuestas de las secciones 2–5 y la
> firma de la sección 6. Con esa firma se quita la marca «provisional, valida Industrial» y se aplica la
> opción A del SLA.

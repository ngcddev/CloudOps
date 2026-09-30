# 000 · Modelo de servicio (industrial)

> **Acciona:** Industrial · Sistemas apoya validando que cada regla y KPI se pueda medir en el Hub
>
> **Módulo:** 1–2 · **Requerimientos:** planes, P1–P4, SLA y KPI (insumo de RF-02, RF-05, RF-13, RF-17, RF-20) · **Depende de:** — · **Estado:** Tareas listas
>
> Fecha límite de la matriz P1–P4: **2 oct**.

## Qué y por qué

Definir cómo se presta y se mide el servicio de la agencia, para que el software tenga reglas reales
que aplicar. Sin esta spec, el SLA, las prioridades y los KPI del Hub serían números inventados.
Cada regla que sale de aquí se convierte en datos semilla que cargan las demás specs.

## Actores

| Actor | Qué hace en esta spec |
|---|---|
| Ingeniero industrial | Levanta el proceso, diseña planes, matriz, SLA y KPI |
| Agencias entrevistadas (2–3) | Cuentan cómo reciben solicitudes, se enteran de caídas y cobran |
| Equipo | Valida que las reglas se puedan medir con los datos del Hub |

## Historias de usuario

- **HU-1.** Como administrador de la agencia, quiero planes con precio, cuota y SLA claros, para
  vender el servicio y saber qué prometo a cada cliente.
- **HU-2.** Como técnico, quiero una regla única para decidir si un caso es P1, P2, P3 o P4, para no
  priorizar a ojo.
- **HU-3.** Como administrador, quiero saber cuándo escalar un caso y a quién, para no incumplir el SLA.
- **HU-4.** Como administrador, quiero KPI con fórmula, para medir si el servicio se presta bien y si
  cada plan es rentable.

## Criterios de aceptación

- [ ] CA-1. Existen **3 planes** (Básico, Estándar, Premium) con precio mensual, SLO de
  disponibilidad, horario de atención, cuota de CPU/RAM y horas de soporte incluidas.
- [ ] CA-2. Existe una **matriz P1–P4** de impacto × urgencia (3 × 3 o 4 × 4) con al menos un
  ejemplo por prioridad para los 3 clientes canónicos.
- [ ] CA-3. Cada prioridad tiene **tiempo de respuesta y de solución**, y se define si el reloj corre
  24/7 o solo en el horario del plan.
- [ ] CA-4. Existen **reglas de escalamiento**: qué pasa al 50 %, 80 % y 100 % del tiempo de SLA.
- [ ] CA-5. Existe una **lista de KPI con fórmula, fuente del dato y meta**: cumplimiento de SLA,
  MTTR, disponibilidad, tickets por cliente, carga por técnico y costo por plan.
- [ ] CA-6. Existe el **mapa del proceso AS-IS y TO-BE** de solicitud a cierre y de falla a cierre.
- [ ] CA-7. Existen **fichas de persona** para los 3 actores humanos.
- [ ] CA-8. Todo lo anterior está en **archivos semilla** que la spec 001 carga sin editarlos a mano.

## Fuera de alcance

- Facturación, pagos o contratos reales (RF-24).
- Planes personalizados por cliente.
- Encuestas de satisfacción.

## Demo de cierre

1. Mostrar la matriz P1–P4 y clasificar en vivo tres casos: "el sitio del restaurante no carga"
   (P1), "el formulario del consultorio no envía" (P2) y "cambiar una foto" (P4).
2. Mostrar la tabla de planes y explicar por qué Premium cuesta más (SLO, horario, cuota).
3. Mostrar la tabla de KPI y de dónde saldrá cada dato en el Hub.
4. Abrir los archivos semilla que usará la spec 001.

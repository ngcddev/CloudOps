# Sitio lento

**Síntoma:** el sitio responde pero tarda; el tablero muestra la duración del sondeo alta o la alerta `PresupuestoQuemadoLento`.

## Diagnóstico

1. Tablero RED y USE: ¿sube la duración sola, o también los errores? Duración sin errores apunta a red o CPU; errores, a la aplicación.
2. Trazas en Tempo (Grafana, fuente Tempo) para ver en qué tramo se pierde el tiempo; los registros de Loki con el mismo identificador de traza dicen por qué.
3. Reproducir de forma controlada: `bash gitops/pruebas/simulaciones.sh latencia` añade 400 ms de red a los Pods y mide `probe_duration_seconds`.

## Acción

- Latencia por saturación: [saturacion.md](saturacion.md).
- Latencia tras publicar: [rollback.md](rollback.md).
- Si es la red del nodo no hay acción en el sitio: avisar a Sistemas.

## Verificación

`probe_duration_seconds` de vuelta a su nivel normal y la quema del presupuesto (`sitio:quemado:ratio_30m`) por debajo de 3.

## Cuándo escalar

Más de 6 horas con quema lenta sin causa: el margen del mes se agota en unos 10 días; revisar con el equipo.

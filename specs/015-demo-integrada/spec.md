# 015 · Demo integrada

> **Módulo:** 7 · **Requerimientos:** RNF-11 · **Depende de:** todas · **Estado:** Spec y plan

## Qué y por qué

Los 10 puntos de la demo final, en orden, repetibles y a tiempo. Es la sustentación del 30 nov: si
algo no se ve en pantalla, no cuenta (regla de oro). No se agregan funcionalidades nuevas.

## Actores

| Actor | Qué hace en esta spec |
|---|---|
| Equipo | Presenta, cada rol muestra su parte |
| Jurado | Evalúa que cada punto se cumpla |

## Historias de usuario

- **HU-1.** Como equipo, quiero reiniciar todo a un estado conocido con un comando, para ensayar y
  presentar siempre igual.
- **HU-2.** Como equipo, quiero un guion con tiempos y responsables, para no pasarnos de 15 minutos.
- **HU-3.** Como equipo, quiero un video de respaldo, por si falla la red o el hardware.

## Criterios de aceptación

- [ ] CA-1. Un comando deja la base de datos, el repositorio de configuración y los sitios en el
  estado inicial de la demo (datos semilla).
- [ ] CA-2. La demo recorre los 10 puntos de la [matriz de trazabilidad](../../docs/requerimientos.md#matriz-de-trazabilidad-demo-final--requerimientos--specs)
  en **menos de 15 minutos**.
- [ ] CA-3. Se ensaya 3 veces completa en la red del salón antes del 30 nov.
- [ ] CA-4. Existe un video de respaldo de la demo completa.
- [ ] CA-5. Existe un plan B por cada punto que dependa de la red o del PC B.

## Fuera de alcance

- Funcionalidades nuevas.

## Demo de cierre

Es la propia demo final: los 10 puntos.

1. Agencia y 3 clientes registrados.
2. Apps en contenedores y Kubernetes.
3. Validación con seguridad antes de publicar.
4. Dashboard técnico y portal del cliente.
5. Falla detectada e incidente abierto.
6. Prioridad, responsable y SLA medido.
7. Rollback.
8. Reporte operativo y ejecutivo.
9. Asistente IA con verificación humana.
10. Infografía operativa.

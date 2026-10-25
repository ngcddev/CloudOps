# Payloads de Alertmanager para las pruebas del webhook (spec 008, T09)

Avisos del webhook de Alertmanager (formato `version: "4"`) de la alerta `SitioCaido` del sitio de La Sazón.
Son JSON y no admiten comentarios, por eso se explican aquí.

| Archivo | Qué representa |
|---|---|
| `alertmanager_firing.json` | El sitio dejó de responder: la alerta pasa a `firing` tras los 30 s del `for` |
| `alertmanager_firing_repetido.json` | Alertmanager repite el mismo aviso (mismo `fingerprint`); no debe crear otro incidente |
| `alertmanager_resolved.json` | El sitio volvió: `endsAt` es la hora del primer sondeo sano |
| `alertmanager_firing_desconocido.json` | Un `namespace` que no corresponde a ningún servicio del Hub |

Las horas están en UTC: `startsAt` 19:00:30 (14:00:30 en Bogotá) y `endsAt` 19:04:10. Cuando T24 deje
Alertmanager funcionando, se reemplazan por avisos reales capturados del clúster.

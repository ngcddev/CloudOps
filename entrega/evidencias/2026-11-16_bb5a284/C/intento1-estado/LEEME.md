# Primer intento de seis verificaciones con efecto (fallos de estado de partida, de script atrasado o de credencial)

- C21 y C22: ferreteria no estaba en v1 al empezar (la demo había quedado en otra versión), y estas pruebas parten de v1. Se repiten después de devolverla a v1.
- C26 y C27: **hallazgo H-OPS-01** — `cronometro.sh` y `publicacion-sana.sh` seguían usando una sola cuenta para pedir y aprobar el cambio; desde la segregación de funciones (spec 018, commit 0df5901, 15 nov) el Hub lo rechaza con «Quien pidió el cambio no puede aprobarlo». Ese commit actualizó las demás demos pero no estas dos. Se corrigieron (aprobación con una segunda cuenta) y se repiten.
- C24: demo-010 falló solo en el paso 6 (Prometheus apagado); se repite en estado limpio para ver si se reproduce. Ver el registro de la repetición.
- C30: faltaba `GITEA_TOKEN`; se toma del Secret `hub-gitops-tokens` y se repite.

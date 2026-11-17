# Tercer intento: causas encontradas

- C22 y C27: seguían bloqueadas por dos solicitudes de cambio pendientes que dejaron los intentos fallidos (primero se intentó rechazarlas con un cuerpo con tildes que Windows rompió; luego se rechazaron con la API y quedan en la bitácora con su motivo). Se repiten.
- C24: el primer intento (con la demo en su estado inicial) pasó los pasos 1 a 5 y falló solo el paso 6 (Prometheus apagado). Los siguientes fallaron además en el paso 4 porque el incidente de la caída ya existía: `cronometro.sh` deja los incidentes «mitigados» (a propósito) y la huella de la alerta es única entre incidentes abiertos. Se cierran los incidentes antes de repetir.
- C30: faltaba `tofu init` y el script escogía el alias de Windows Store `python3` en lugar de Python; se repite con `PYTHON=python` y después de `tofu init`.

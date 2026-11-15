# Plan 018 · Cierre del módulo 3

Cada tarea se prueba antes de pasar a la siguiente. Orden: SAST y SCA → hallazgos con VEX → SBOM atestado → escenarios nuevos → segregación de funciones → solo lectura → IA y amenazas.

## Decisiones

1. **Segregación de funciones (T05):** se activa por defecto; la demo pasa a pedir con una cuenta y aprobar con otra.
2. **Sin verificación de firma en la admisión:** la verificación está en la puerta; se anota como mejora.
3. **SAST y SCA (T01):** `pipelines/pruebas/analisis-estatico.sh` corre bandit (frena con severidad media o alta), `trivy fs` sobre las dependencias declaradas y escanea la imagen del frontend, y el CI lo ejecuta. Lo que encontró: 9 hallazgos medios de bandit (urllib abre también `file://`: ahora las integraciones validan que la URL sea http o https; y la ruta de demostración de los sitios, con su razón) y una imagen del frontend con una CVE crítica y 12 altas que nadie escaneaba (se actualizan los paquetes de Alpine). Las dependencias declaradas salieron limpias. Los hallazgos bajos de bandit (10) se informan sin frenar.

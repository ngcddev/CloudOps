# Plan 018 · Cierre del módulo 3

Cada tarea se prueba antes de pasar a la siguiente. Orden: SAST y SCA → hallazgos con VEX → SBOM atestado → escenarios nuevos → segregación de funciones → solo lectura → IA y amenazas.

## Decisiones

1. **Segregación de funciones (T05):** se activa por defecto; la demo pasa a pedir con una cuenta y aprobar con otra.
2. **Sin verificación de firma en la admisión:** la verificación está en la puerta; se anota como mejora.
3. **SAST y SCA (T01):** `pipelines/pruebas/analisis-estatico.sh` corre bandit (frena con severidad media o alta), `trivy fs` sobre las dependencias declaradas y escanea la imagen del frontend, y el CI lo ejecuta. Lo que encontró: 9 hallazgos medios de bandit (urllib abre también `file://`: ahora las integraciones validan que la URL sea http o https; y la ruta de demostración de los sitios, con su razón) y una imagen del frontend con una CVE crítica y 12 altas que nadie escaneaba (se actualizan los paquetes de Alpine). Las dependencias declaradas salieron limpias. Los hallazgos bajos de bandit (10) se informan sin frenar.
4. **Hallazgos y VEX (T02):** `pipelines/hallazgos.yaml` (6 reglas con explotabilidad, tratamiento, justificación y revisión a ≤ 6 meses) + `pipelines/hallazgos.py` + `pipelines/pruebas/hallazgos.sh`. Lo corregible se corrige (zlib1g en las imágenes de Python y todos los paquetes de Alpine en las de nginx), nunca se acepta; lo demás necesita regla vigente. Resultado real: 94 hallazgos altos sin arreglo en las imágenes de Python, todos cubiertos. Trivy no consumió el VEX (productos por nombre de imagen, no por digest), así que el cruce lo hace el script y el VEX queda como documento de salida.

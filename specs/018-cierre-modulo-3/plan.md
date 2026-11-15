# Plan 018 · Cierre del módulo 3

Cada tarea se prueba antes de pasar a la siguiente. Orden: SAST y SCA → hallazgos con VEX → SBOM atestado → escenarios nuevos → segregación de funciones → solo lectura → IA y amenazas.

## Decisiones

1. **Segregación de funciones (T05):** se activa por defecto; la demo pasa a pedir con una cuenta y aprobar con otra.
2. **Sin verificación de firma en la admisión:** la verificación está en la puerta; se anota como mejora.

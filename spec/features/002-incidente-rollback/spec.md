# 002 — Incidente con rollback y mensaje al cliente

## Qué hace
Permite simular la caída del sitio de un cliente. El sistema abre automáticamente un incidente P1 (con su ticket y SLA), la agencia ejecuta un rollback a la versión estable y el sistema genera un mensaje sencillo para el cliente. Todo queda en una línea de tiempo.

## Historias de usuario
- Como agencia, quiero simular una falla en el sitio de un cliente para demostrar la detección.
- Como agencia, quiero que se abra un incidente P1 automáticamente cuando el sitio esté caído.
- Como agencia, quiero hacer rollback a la última versión estable para recuperar el servicio.
- Como cliente, quiero un mensaje en lenguaje simple que me explique qué pasó.

## Estados del sitio
`operativo` → `caído` → `operativo` (tras rollback). Cada cliente tiene una versión estable (p. ej. `v1.0`) y una versión actual (p. ej. `v1.1`).

## Criterios de aceptación
- [ ] Cada cliente muestra su estado (`operativo` / `caído`) y sus versiones estable y actual.
- [ ] Botón **"Simular falla"** que marca el sitio como caído (versión defectuosa).
- [ ] Al simular la falla se crea un ticket/incidente **P1** con SLA (15 min / 4 h) sin intervención manual.
- [ ] Botón **"Rollback"** que vuelve a la versión estable y marca el sitio como operativo.
- [ ] El rollback cierra el incidente y registra el tiempo de recuperación en minutos.
- [ ] La línea de tiempo del incidente lista los eventos con hora: falla detectada, incidente abierto, rollback, recuperado.
- [ ] Se genera un mensaje para el cliente sin términos técnicos (p. ej. "se detectó una falla temporal y se activó la recuperación").
- [ ] Interfaz en español y en blanco y negro.

## Fuera de alcance
Monitoreo real (ping HTTP), Kubernetes/GitOps reales, IA para redactar el mensaje (se usa una plantilla).

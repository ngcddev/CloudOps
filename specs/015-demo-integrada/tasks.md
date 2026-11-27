# Tareas · 015 Demo integrada

> Propuestas el 16 nov 2026 a partir del [guion](../../demo/guion.md) y de [cumplimiento-tecnico.md](../../docs/cumplimiento-tecnico.md). Marcar una tarea solo si su **Verifica** se cumple y se ve en pantalla.
> El punto 10 de la spec («infografía») se cambia por **voz del asistente**: la spec 014 queda como mejora (decisión del 15 nov).

## Preparar

- [ ] T01 · Actualizar la matriz de trazabilidad de `docs/requerimientos.md` y esta spec: el punto 10 es voz (spec 021) y no la infografía — **Verifica:** la matriz y la spec dicen lo mismo que el guion.
- [ ] T02 · Un solo script `demo/reiniciar-todo.sh` que encienda en orden (Docker, serverlb, server-0, estado-remoto, runner), confirme la IP del nodo, reinicie datos y deje ✓/✗ por punto — **Verifica:** correrlo dos veces seguidas deja el mismo estado y termina en menos de 5 min (CA-1).
- [ ] T03 · Preparar una versión del colegio con un secreto a propósito para que Gitleaks la rechace, y su corrida grabada — **Verifica:** en el Hub aparece «rechazado por seguridad» con el motivo y no se puede aprobar.
- [ ] T04 · Agregar al archivo `hosts` del equipo de la demo `mlflow.hub.local`, `backstage.hub.local` y `ferreteria-staging.hub.local` — **Verifica:** `curl -sI http://mlflow.hub.local` responde 200 sin `--resolve`.
- [ ] T05 · Probar la voz con una persona real y su micrófono en el navegador de la demo — **Verifica:** se pregunta hablando, se corrige lo entendido y se escucha la respuesta. (El 16 nov ya pasó la prueba automática en un navegador real contra el clúster con la política de seguridad estricta y un micrófono falso; falta la voz humana.)

## Verificar lo que quedó sin ver

- [ ] T06 · Correr `infra/pruebas/crear-cliente.sh` y `tofu plan -detailed-exitcode` contra el clúster con un token de Gitea — **Verifica:** el cliente temporal se crea, Argo CD lo sincroniza y se limpia; el plan sale con 0.
- [ ] T07 · Provocar una caída real y ver las alertas nuevas (`HubCaido`, memoria, disco, respaldo) en Prometheus — **Verifica:** `HubCaido` pasa a `firing` a 1 min de apagar la API y se resuelve al volver.
- [ ] T08 · Decidir con el profesor si el audio cubre el módulo 6 o si hace falta una imagen — **Verifica:** respuesta por escrito en `docs/historico/bitacora.md`.

## Plan B

- [ ] T09 · Grabar el video de respaldo del recorrido completo (CA-4) y los videos cortos de la detección (punto 4–5) y de la corrida de la puerta (punto 3) — **Verifica:** abren sin Internet.
- [ ] T10 · Generar con antelación los dos PDF (operativo y ejecutivo de La Sazón) y dejar aprobado un borrador semilla — **Verifica:** están a un clic en la demo.

## Ensayar

- [ ] T11 · Ensayo 1 cronometrado sin público — **Verifica:** tiempos reales por punto anotados en `docs/historico/context.md`; el recorrido principal dura menos de 15 min.
- [ ] T12 · Ensayo 2 con reinicio previo y relevo entre personas — **Verifica:** sin pasos improvisados.
- [ ] T13 · Ensayo 3 en el equipo y la red del salón (CA-3), grabando el video — **Verifica:** el video de T09 sale de este ensayo.
- [ ] T14 · Demo: los puntos del guion en orden — **Verifica:** [spec.md](spec.md#criterios-de-aceptación).

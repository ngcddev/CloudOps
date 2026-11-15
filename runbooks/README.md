# Runbooks de operación (spec 019, T01)

Qué hacer cuando algo falla. Cada runbook tiene la misma forma: **síntoma**, **diagnóstico**, **acción**, **verificación** y **cuándo escalar**.
Las alertas apuntan aquí con su `runbook_url` (ver `observability/prometheus/reglas/`). Todo lo que citan existe: lo comprueba `backend/tests/test_runbooks.py`.

| Situación | Runbook | Alerta que lo usa |
|---|---|---|
| Un sitio de cliente no responde | [caida-del-sitio.md](caida-del-sitio.md) | `SitioCaido` |
| Una publicación salió mal | [rollback.md](rollback.md) | `PresupuestoQuemadoRapido` |
| Perder o dañar la base del Hub | [respaldo-y-restauracion.md](respaldo-y-restauracion.md) | — |
| El clúster no arranca tras apagar el equipo | [reinicio-del-cluster.md](reinicio-del-cluster.md) | — |
| La API o un sitio van al límite de CPU o memoria | [saturacion.md](saturacion.md) | — |
| El sitio responde pero lento | [latencia.md](latencia.md) | `PresupuestoQuemadoLento` |

Convención: los comandos suponen `KUBECONFIG=C:/Users/<usuario>/.kube/k3d-hub.yaml` y Git Bash. Nada se arregla a mano en el clúster: los cambios entran por Git (Argo CD los revierte).

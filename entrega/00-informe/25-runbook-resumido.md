<!-- Sección 25 · Resumen del runbook (el completo es el complementario 05). Fuente: runbooks/ (9 procedimientos; test_runbooks.py comprueba su estructura y que lo que citan existe). -->

# Runbook resumido

Los procedimientos de operación están en `runbooks/`, uno por situación, y todos tienen la misma forma: síntoma, diagnóstico, acción, verificación y cuándo escalar. Las alertas de Prometheus apuntan al procedimiento con la anotación `runbook_url`, y la prueba `backend/tests/test_runbooks.py` comprueba que cada procedimiento tenga sus cinco secciones y que todo lo que cita exista. La versión completa, con los procedimientos de arranque, apagado, escalamiento y degradación elegante, está en el documento complementario `05_Runbook_Operacion.docx`. La regla común es que nada se arregla a mano en el clúster: los cambios entran por Git y Argo CD revierte lo que no esté allí.

::: {custom-style="Table Caption"}
**Tabla {T:runbooks}**\
*Procedimientos de operación: síntoma, acción principal y cuándo escalar*
:::

| Situación | Alerta | Acción principal | Cuándo escalar |
|--------------|------------|-------------------------|-----------------------|
| Un sitio de cliente no responde (`caida-del-sitio`) | `SitioCaido` | Si la causa es una publicación mala, rollback desde el incidente; si el Pod está en bucle, reiniciar el Deployment y, si vuelve a caer, hacer rollback | Más de 15 minutos sin recuperar, o caen varios sitios a la vez (apunta al nodo) |
| Una publicación salió mal (`rollback`) | `PresupuestoQuemadoRapido` | Botón «Rollback» del incidente: el Hub escribe el commit de vuelta y Argo CD lo aplica; sin el Hub, `git revert` en `hub-gitops` | Gitea caído o conflicto en `hub-gitops`: avisar a Sistemas |
| El Hub no responde (`caida-del-hub`) | `HubCaido` | Esperar a que la base vuelva, o volver a la versión anterior en `gitops/hub/` y promoverla con el sincronizador | El Pod no arranca con la versión anterior o la base no vuelve con el respaldo |
| Perder o dañar la base del Hub (`respaldo-y-restauracion`) | — | Respaldo manual con un Job del CronJob; restaurar con `restaurar.sh` sobre una base nueva y con la API detenida | El volcado no existe o falla al restaurar: no sobrescribir la base y avisar |
| El clúster no arranca tras apagar el equipo (`reinicio-del-cluster`) | — | Arrancar Docker Desktop y los contenedores en orden: balanceador, nodo, estado remoto y ejecutor; revisar el puerto y el kubeconfig | El nodo sigue sin arrancar con la IP correcta: recrear el clúster desde `gitops/` |
| CPU o memoria al límite (`saturacion`) | `ContenedorSinMemoria` | La API escala con el HPA; un sitio no se sube a mano: el plan define la cuota | La cuota impide escalar o el nodo está sin memoria |
| Un contenedor se reinicia en bucle (`contenedor-en-bucle`) | `ContenedorEnBucle` | Según la causa: sin memoria, seguir el procedimiento de saturación; una sonda falla, volver el manifiesto a la versión anterior por Git; error de la aplicación, corregir o hacer rollback; muere por la base o un Secret, ver la caída del Hub | El contenedor sigue muriendo con la versión anterior: guardar `describe` y `logs --previous` y revisar el manifiesto contra el último cambio |
| El monitoreo dejó de sondear (`monitoreo-ciego`) | `MonitoreoCiego`, `Watchdog` | Ver por qué cae o reinicia el Pod del monitoreo; comprobar que los Services conserven la anotación `hub/probe`; mientras tanto, comprobar a mano el `/health` de los sitios (estas alertas no avisan a nadie) | Prometheus no arranca (volumen lleno) o Alertmanager no recibe alertas: recrear el monitoreo desde `observability/` (se pierde el historial) |
| El sitio responde pero lento (`latencia`) | `PresupuestoQuemadoLento` | Según la causa: saturación, una publicación reciente (rollback) o la red del nodo (avisar a Sistemas) | Más de 6 horas de quema lenta sin causa: revisar con el equipo, porque el margen del mes se agota en unos 10 días |

::: {custom-style="Nota"}
*Nota.* Elaboración propia a partir de `runbooks/README.md` y de los nueve procedimientos. Los comandos suponen Git Bash y el `kubeconfig` del clúster `k3d-hub`.
:::

**Respaldos.** El Hub se respalda cada día a las 03:00 UTC (se conservan 7 volcados), Gitea y Argo CD se respaldan aparte (se conservan 5) y la restauración se prueba con `gitops/pruebas/respaldo.sh`. **Límite.** Los procedimientos de arranque y de recuperación ante la caída del equipo dependen de un orden de arranque y de una dirección fija del nodo; el reinicio de todo el entorno con un solo script está pendiente (especificación 015, tarea T02).

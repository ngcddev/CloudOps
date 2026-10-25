# Plan 009 · Recuperación por rollback

> Cómo se construye [la spec](spec.md). No agrega herramientas: reutiliza el cliente de Gitea, el
> seguimiento de Argo CD y el flujo de incidentes de las specs 005 y 008.

## Punto de partida

| Pieza | Estado | Dónde |
|---|---|---|
| Escribir una versión en `hub-gitops` con un commit | Hecho (005) | `services/gitops_publish.py: publish_version`, `integrations/gitea.py: update_file`, `services/kustomization.py: set_new_tag` |
| Versión activa y estable por servicio | Hecho (005) | `services.current_version`, `services.stable_version`; `stable_version` solo avanza cuando una versión se publicó y quedó sana |
| Alinear la versión del Hub cuando Git cambia por fuera | Hecho (005) | `deploy_watch.reconcile_version` (crea un `Deployment` «Cambio manual en Git»; usa `source=rollback` si la versión ya existió) |
| Historial de versiones | Hecho (005) | `deployments` con `source` = `cambio` / `rollback` |
| Incidentes, línea de tiempo y mitigación | Se construye en la 008 | `incidents`, `incident_events`, `incident_flow.py` |
| Sesión y bitácora | Hecho (007) | `require_role`, `audit.record` |

## Decisión 1: a qué versión se vuelve

`rollback_target(service)`:

1. Si `stable_version` es distinta de `current_version` (el caso de la v2 rota: nunca llegó a estar sana),
   se vuelve a `stable_version`.
2. Si son iguales (la versión estuvo sana y se rompió después), se vuelve a la versión de la fila
   anterior de `deployments` (la que corría antes de la actual).
3. Si no hay ninguna → botón deshabilitado: «No hay una versión anterior a la que volver».

«Versión actual» es la que tiene Git, no la que dice el Hub: un cambio `en_validacion` ya escribió su commit, así que
su `to_version` cuenta como la actual (`rollback.running_version`). Sin esto, durante los primeros minutos de la v2 rota
el Hub aún diría v1 y no habría a dónde volver.

También se rechaza (409) si el `kustomization.yaml` de Git ya tiene la versión de destino: alguien
revirtió a mano y lo único que falta es esperar a Argo CD. La versión de destino ya corrió en el
clúster, así que no se vuelve a pasar por la puerta de seguridad: recuperar es el camino de salida y no
debe depender de que el pipeline funcione.

## Flujo

1. `GET /api/incidents/{id}/rollback-plan` → versión actual, versión de destino, `can_rollback` y la
   razón si no se puede (sin versión anterior, incidente cerrado o ya en curso).
2. `POST /api/incidents/{id}/rollback` (rol agencia, el cuerpo no trae el actor: sale de la sesión):
   1. El incidente debe estar `abierto` y sin rollback en curso (409 si no).
   2. `gitops_publish.publish_rollback(...)` lee `clients/<c>/kustomization.yaml`, cambia solo los
      `newTag` con `set_new_tag` y hace un commit con el mensaje
      `revert(<cliente>): volver a <versión> (incidente #<id>)`, autor = el usuario del Hub. La API de
      Gitea no tiene `revert`: se escribe el contenido anterior, que es lo mismo que haría un `git revert`.
   3. El incidente guarda `rollback_commit_sha`, `rollback_by_id`, `rollback_at`,
      `rollback_from_version` y `rollback_to_version`; evento `rollback_enviado`; `audit.record(
      "rollback", "incident", …)`.
   4. Si había un cambio `en_validacion` hacia la versión rota, pasa a `fallida` con la nota «Revertido
      por el incidente #N» (la transición ya existe); si no, su plazo vencería sin sentido.
3. El seguimiento periódico de la 005 (`deploy_watch.check_cycle`) confirma el rollback cuando Argo CD
   está `Synced`, `Healthy` y en la revisión del commit (`is_published`): fija
   `rollback_confirmed_at`, deja `current_version` y `stable_version` en la versión de destino, agrega un
   `Deployment` con `source=rollback` y el nombre de quien lo pidió, evento `rollback_confirmado` y
   `audit.record(None, "confirmar_rollback", …)` («Sistema»).
4. **Mitigación.** La fuente de verdad es la sonda: el `resolved` de Alertmanager (spec 008) fija
   `mitigated_at` con el primer sondeo sano. Para evitar un `Deployment` duplicado, `reconcile_version`
   se salta los servicios con un rollback pendiente. Si el monitoreo no lo confirma, el técnico puede
   mitigar a mano **solo si** el rollback ya está confirmado en Argo CD (cambio en `incident_flow.py`: la
   mitigación manual vale para `source=manual` o con `rollback_confirmed_at`); un `resolved` posterior
   sobre un incidente ya mitigado no hace nada.
5. **MTTR:** `mttr_minutes(incidente) = (mitigated_at − started_at)` en minutos con un decimal. Se
   calcula, no se guarda: así no puede desalinearse y lo reutilizan la 010 y la 013.

Estado del rollback en la API (`rollback.status`), derivado y no guardado (al pedir el detalle el Hub lee la
revisión de Argo CD con la dependencia `get_argocd`; si Argo CD no responde, el estado se queda en `enviado`): `sin_rollback` →
`enviado` (hay commit y Argo CD aún no está en esa revisión) → `sincronizando` (Argo CD en esa revisión
pero sin salud) → `recuperado` (`rollback_confirmed_at`).

## Modelo de datos (migración `0009`)

`incidents` suma `rollback_from_version`, `rollback_to_version`, `rollback_commit_sha`, `rollback_by_id` FK
users, `rollback_at` y `rollback_confirmed_at` (todos nulos hasta que haya rollback). `incident_events`
suma los tipos `rollback_enviado`, `rollback_confirmado` y `mensaje_cliente`. No hay tablas nuevas.

## Mensaje al cliente

`services/messages.py: client_message(incident, now)` usa la plantilla de la [misión](../../constitution/mission.md):
*«Detectamos una falla temporal en su sitio a las {hora}. Activamos la recuperación y a las {hora_fin} el
servicio volvió a funcionar. Tiempo total: {min} minutos.»* Las horas salen de `started_at` y
`mitigated_at` en America/Bogota. `GET /api/incidents/{id}/client-message` responde 409 mientras el
incidente no esté `mitigado`. La duración sale de las horas mostradas al minuto (14:00 → 14:07 = «7 minutos» aunque el MTTR exacto sea 7,5). Es un texto determinista (no es IA) pero se trata igual que un borrador:
se muestra en el detalle con «Copiar» y la agencia decide si lo envía (principio 6).

## API y pantalla

| Método | Ruta | Rol | Qué hace |
|---|---|---|---|
| GET | `/api/incidents/{id}/rollback-plan` | agencia | Versión actual, destino y si se puede |
| POST | `/api/incidents/{id}/rollback` | agencia | Escribe el commit y registra el rollback |
| GET | `/api/incidents/{id}/client-message` | agencia | Mensaje para el cliente (solo `mitigado`) |

`GET /api/incidents/{id}` suma el bloque `rollback` (estado, versiones, quién y cuándo) y `mttr_minutes`.

Detalle del incidente (`/agencia/incidentes/:id`): bloque «Recuperación» con «versión actual → destino», el
botón **Rollback** con un diálogo de confirmación, el avance Enviado → Sincronizando → Recuperado (se
vuelve a leer cada 5 s mientras no esté recuperado), el MTTR y, ya mitigado, el mensaje con «Copiar».

## Riesgos

| Riesgo | Respuesta |
|---|---|
| Dos rollbacks a la vez (doble clic o dos técnicos) | 409 si ya hay `rollback_commit_sha` sin confirmar (en ese incidente o en otro del mismo servicio); la fila se bloquea con `FOR UPDATE`; el botón se bloquea; Gitea además rechaza la segunda escritura con otro `sha` de blob |
| La versión estable ya no está en el registro | Antes de escribir, el Hub no la verifica (no habla con el registro); si Argo CD no la puede bajar el estado queda `sincronizando` y se ve en la consola; mejora futura: comprobar la imagen |
| `resolved` llega antes que Argo CD | Gana la sonda: `mitigated_at` es el primer sondeo sano; la confirmación del rollback llega después y solo completa el historial |
| La versión de destino también está rota | El incidente sigue `abierto` (la sonda no vuelve a verde) y se puede escalar a mano |
| Mensaje con jerga | Se prueba contra el glosario («Rollback» → «Se restauró una versión estable») |

## Cómo se verifica

- `pytest` con Gitea y Argo CD simulados (`tests/fake_gitea.py`, `tests/fake_argocd.py`): el rollback deja
  `kustomization.yaml` idéntico al de la versión de destino y cambia solo los `newTag`; las reglas de la
  decisión 1; un solo rollback a la vez; permisos (cliente → 403); bitácora.
- Prueba de integración con `deploy_watch`: confirmar, `Deployment` único y `stable_version` actualizada.
- `gitops/pruebas/demo-caso-restaurante.sh`: el caso completo (v2 → incidente → rollback → `mitigado`) con
  MTTR medido y mensaje.
- Demo de [spec.md](spec.md#demo-de-cierre).

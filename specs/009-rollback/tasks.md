# Tareas 009 · Recuperación por rollback

> Cada tarea: una acción con verbo · se comprueba en minutos · menos de un día · se integra sola.
> Rama por tarea: `feat/009-tNN-slug`. Poner el nombre de quien la toma entre corchetes.
>
> Fechas: módulo 4 del 24 oct al 3 nov (sustentación). El caso del restaurante sin IA debe estar listo el
> 31 oct (008 + 009); el 1 y 2 de nov solo se ensaya. Meta de esta spec: **30 oct**.

## Cómo repartirlo

| Carril | Tareas | Necesita el clúster | Puede empezar |
|---|---|---|---|
| Backend | T01–T09 | No (`pytest` con Gitea y Argo CD simulados) | Cuando la 008 tenga T01–T06 (tablas y flujo de incidentes) |
| Frontend | T10–T12 | No (datos de prueba hasta que la API responda) | Cuando la 008 tenga T17 (detalle del incidente) |
| Integración | T13–T16 | Sí | Cuando cierren Backend y Frontend y la 008 esté publicada |

Depende de la 008: usa sus tablas, su detalle de incidente y su `resolved` del monitoreo. El backend de esta
spec se puede adelantar con incidentes manuales en las pruebas.

## Backend

- [x] T01 · Agregar a `incidents` las columnas del rollback con migración `0009` (versiones, `rollback_commit_sha`, `rollback_by_id`, `rollback_at`, `rollback_confirmed_at`) y los tipos de evento nuevos — **Verifica:** `alembic upgrade head` y `alembic downgrade -1` sin errores; los incidentes de la 008 siguen leyéndose. *Verificado también en PostgreSQL 16: `upgrade`, `downgrade -1` y `upgrade` sin errores; las seis columnas y la FK quedan en `incidents`.* [ngcddev]
- [x] T02 · Escribir `rollback_target(service)` en `services/rollback.py` con las reglas de la decisión 1 — **Verifica:** `pytest`: con v2 sin estabilizar vuelve a v1; con v1.1 sana y rota vuelve a la anterior; sin versión anterior responde «no hay a dónde volver». *`running_version` toma como versión actual la de un cambio `en_validacion` (ya está en Git aunque el Hub aún diga v1): así el caso real de la v2 rota, que nunca llega a `desplegada`, vuelve a v1.* [ngcddev]
- [x] T03 · Agregar `publish_rollback` a `services/gitops_publish.py`, que cambia solo los `newTag` y escribe el commit `revert(<cliente>): volver a <versión> (incidente #<id>)` con el usuario como autor — **Verifica:** `pytest` con `tests/fake_gitea.py`: el `kustomization.yaml` queda idéntico al de la versión de destino y el resto del archivo no cambia. *Se agregó `find_existing_rollback`, que adopta el commit si un rollback quedó escrito en Gitea pero no guardado en la base.* [ngcddev]
- [x] T04 · Crear `GET /api/incidents/{id}/rollback-plan` — **Verifica:** `pytest`: respuesta con versión actual, destino y `can_rollback`; con incidente cerrado o rollback en curso, `false` con la razón; como cliente → 403. [ngcddev]
- [x] T05 · Crear `POST /api/incidents/{id}/rollback` que escribe el commit, guarda los campos, deja el evento `rollback_enviado` y llama a `audit.record` — **Verifica:** `pytest`: queda el commit, el actor sale de la sesión (un cuerpo con otro id no cambia `rollback_by_id`) y una fila en `audit_logs`; el segundo intento → 409 (CA-8). *La fila del incidente se bloquea con `FOR UPDATE` (PostgreSQL) y un segundo clic o un segundo incidente del mismo servicio dan 409 sin segundo commit.* [ngcddev]
- [x] T06 · Pasar a `fallida` el cambio `en_validacion` hacia la versión rota, con la nota «Revertido por el incidente #N» — **Verifica:** `pytest`: el cambio queda `fallida` y se puede crear un cambio nuevo después (CA-6). *Además del evento interno con la nota exacta, el cliente ve «Se restauró una versión estable para mantener la continuidad» (glosario).* [ngcddev]
- [x] T07 · Confirmar el rollback en `deploy_watch.check_cycle` (`Synced`, `Healthy`, revisión del commit), dejar `current_version`/`stable_version` y un `Deployment` con `source=rollback`, y hacer que `reconcile_version` salte los servicios con rollback pendiente — **Verifica:** `pytest` con `tests/fake_argocd.py`: un solo `Deployment`, versión de destino estable, evento `rollback_confirmado` y fila de «Sistema» en la bitácora. [ngcddev]
- [x] T08 · Calcular `mttr_minutes` y `rollback.status` (`enviado`/`sincronizando`/`recuperado`) en `GET /api/incidents/{id}`, y permitir mitigar a mano un incidente de alerta con `rollback_confirmed_at` — **Verifica:** `pytest`: incidente iniciado 14:00:00 y mitigado 14:07:30 → `mttr_minutes` 7.5; mitigar a mano sin rollback confirmado → 409 y con él → 200 (CA-9). *Un incidente de alerta mitigado a mano también deja el servicio `operativo`. El avance `enviado`/`sincronizando` se lee de Argo CD al pedir el detalle (dependencia `get_argocd`); sin respuesta se queda en `enviado`.* [ngcddev]
- [x] T09 · Escribir `services/messages.py: client_message` y `GET /api/incidents/{id}/client-message` con la plantilla de la misión, horas en America/Bogota — **Verifica:** `pytest`: para un incidente de 14:00 a 14:07 el texto trae «14:00», «14:07» y «7 minutos»; sin jerga del glosario; antes de `mitigado` → 409. *La duración sale de las horas mostradas al minuto, para que 14:00 → 14:07 diga «7 minutos» aunque el MTTR exacto sea 7,5. El evento `mensaje_cliente` queda reservado y no se escribe: generar el texto no cambia nada.* [ngcddev]

## Frontend

- [x] T10 · Agregar a `frontend/src/api.ts` los tipos y llamadas de rollback y mensaje, con datos de prueba si la API no responde — **Verifica:** `tsc` sin errores. [ngcddev]
- [x] T11 · Agregar al detalle del incidente el bloque «Recuperación»: versiones, botón **Rollback** con confirmación, deshabilitado con su razón, y el avance Enviado → Sincronizando → Recuperado — **Verifica:** con datos de prueba el avance cambia cada 5 s sin recargar y el botón se bloquea tras el primer clic (CA-1, CA-3, CA-8). *Verificado en el navegador con datos de prueba: el avance pasó de «Enviado» a «Sincronizando» y «Recuperado» solo, cada 5 s, y el botón desapareció tras el primer clic.* [ngcddev]
- [x] T12 · Mostrar el MTTR y el mensaje al cliente con «Copiar» cuando el incidente está `mitigado` — **Verifica:** el texto copiado coincide con el de la API y no aparece antes de mitigar (CA-4, CA-7). *Verificado en el navegador: el texto del cuadro es idéntico al de `getClientMessage` y no aparece antes de mitigar.* [ngcddev]

## Integración

- [ ] T13 · Publicar el Hub con la 009 (imágenes `hub-api` y `hub-web` con etiqueta nueva) — **Verifica:** `kubectl rollout status` en verde y la migración `0009` aplicada. *Hecho: etiqueta `v1.4` en `gitops/hub/api.yaml`, `gitops/hub/web.yaml` y `apps/publicar-imagenes.sh`. Falta: publicar las imágenes (pide `REGISTRY_PASSWORD`), subir los manifiestos a `hub-gitops` y ver `rollout status` y la migración `0009`; el clúster sigue en `v1.2`, así que `v1.4` también lleva la 008.* [ ]
- [ ] T14 · Escribir `gitops/pruebas/demo-caso-restaurante.sh`: aprueba la v2 de La Sazón por la API, espera el incidente P1, pide el rollback, mide hasta `mitigado` y pide el mensaje — **Verifica:** tres corridas con el incidente `mitigado`, `mttr_minutes` impreso y el sitio respondiendo 200 al final (CA-2 a CA-4). *Hecho: el script está escrito (`bash -n` sin errores). Falta correrlo tres veces contra el clúster con la 008 y la 009 publicadas.* [ ]
- [ ] T15 · Comprobar la bitácora, el historial de versiones y la línea de tiempo tras el rollback — **Verifica:** el rollback aparece en las tres con el usuario y las dos versiones (CA-5). *Falta: el script de T14 ya comprueba línea de tiempo, historial y bitácora, pero no se ha corrido en el clúster.* [ ]
- [ ] T16 · Probar los casos de borde en el clúster: rollback sin versión anterior, doble clic y monitoreo apagado — **Verifica:** botón deshabilitado con razón, un solo commit en Gitea y mitigación manual posible (CA-1, CA-8, CA-9). *Falta: las pruebas con `pytest` cubren el botón deshabilitado, el doble clic y la mitigación manual; hace falta repetirlas en el clúster.* [ ]

## Cierre

- [ ] T17 · Demo: de la v2 rota al sitio recuperado con un clic, con MTTR y mensaje al cliente, y mostrar el commit en Gitea y la sincronización en Argo CD — **Verifica:** todos los criterios de [spec.md](spec.md#criterios-de-aceptación). *Falta: depende de T13 a T16.* [ ]

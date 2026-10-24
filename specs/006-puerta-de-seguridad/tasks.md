# Tareas 006 · Puerta de calidad y seguridad

> Cada tarea: una acción con verbo · se comprueba en minutos · menos de un día · se integra sola.
> Rama por tarea: `feat/006-tNN-slug`. Poner el nombre de quien la toma entre corchetes.
>
> Depende de la 005 (terminada). Dos carriles: **plataforma** (T01–T11: Gitea Actions, runner y el
> workflow) y **Hub** (T12–T21: corridas, regla de aprobación y pantallas). El Hub puede avanzar con
> eventos simulados en `pytest` mientras el workflow no existe; se juntan en T22.
> Ningún secreto en el repo: los de la puerta van en los secretos de Gitea Actions.

## Gitea Actions y runner

- [ ] T01 · Activar Actions en Gitea (`GITEA__actions__ENABLED=true` en `gitops/platform/gitea/deployment.yaml`) — **Verifica:** la organización `forja-digital` muestra la sección "Actions" y "Runners". [ ]
- [ ] T02 · Registrar un `act_runner` en un equipo de desarrollo con Docker (fuera del PC A) y documentar su instalación en `pipelines/README.md` — **Verifica:** el runner aparece "Idle" en Gitea y un workflow de prueba con `echo` termina en verde. [ ]
- [ ] T03 · Crear el par de claves de Cosign, subir la privada y su contraseña como secretos de la organización y guardar `pipelines/cosign.pub` — **Verifica:** `git grep -n "BEGIN ENCRYPTED"` no encuentra nada y `cosign.pub` está en el repo. [ ]
- [ ] T04 · Cargar en los secretos de la organización `REGISTRY_USER`, `REGISTRY_PASSWORD`, `HUB_URL` y `HUB_PIPELINE_TOKEN` — **Verifica:** la lista de secretos de la organización muestra los 6 nombres; ningún valor está en el repo. [ ]
- [ ] T05 · Probar a mano que el registro de Gitea guarda firmas: firmar y verificar `ferreteria:v1.1` con `cosign --allow-http-registry` — **Verifica:** `cosign verify --key pipelines/cosign.pub` responde la firma válida; si el registro no la acepta, se anota en el plan y se usa el plan B del riesgo. [ ]

## Repos de los sitios

- [ ] T06 · Escribir `pipelines/sembrar-repos-sitios.sh` que crea `restaurante`, `ferreteria` y `consultorio` en Gitea desde `apps/<sitio>` con los tags `v1` y `v2` (y `v1.1` en la ferretería) — **Verifica:** los 3 repos existen con sus tags; correrlo otra vez no cambia nada. [ ]

## Workflow de la puerta (`pipelines/`)

- [ ] T07 · Escribir `pipelines/reportar.sh` que manda un paso al Hub (`POST /api/pipeline-events` con el token) — **Verifica:** contra el Hub en `docker compose`, un evento de prueba queda en la base. [ ]
- [ ] T08 · Escribir `pipelines/puerta.yaml` con `push` de tags `v*`: Gitleaks sobre los commits nuevos del tag y build con `APP_VERSION=<tag>` — **Verifica:** un tag con una contraseña falla en "secretos" y no llega a construir (CA-1). [ ]
- [ ] T09 · Sumar al workflow Trivy (`CRITICAL`, `--ignore-unfixed`) y Syft sobre el tar de la imagen — **Verifica:** una versión con una imagen base vieja (por ejemplo `nginx:1.18`) falla en "vulnerabilidades" (CA-2); una limpia deja el SBOM SPDX en el Hub. [ ]
- [ ] T10 · Sumar al workflow el push con `skopeo`, `cosign sign` y `cosign verify` — **Verifica:** una versión limpia queda firmada en el registro; si se cambia `cosign.pub` por otra clave, falla en "verificación" y la corrida queda `fallo` (CA-3). [ ]
- [ ] T11 · Construir en la misma corrida las dos imágenes del consultorio y copiar el workflow a los 3 repos (lo hace el script de T06) — **Verifica:** un tag en `consultorio` produce `consultorio-web` y `consultorio-api` firmadas en una sola corrida. [ ]

## Modelo y reglas en el Hub

- [x] T12 · Crear las tablas `security_runs` y `security_checks` con migración — **Verifica:** `alembic upgrade head` y `alembic downgrade -1` sin errores. [ngcddev]
- [x] T13 · Crear `POST /api/pipeline-events` con `PIPELINE_TOKEN` (en `config.py` y `.env.example`): abre la corrida, registra cada paso con su reporte y la cierra — **Verifica:** `pytest`: una corrida completa queda `ok` con 6 controles; sin token o con otro → 401; servicio o paso desconocido → 422. [ngcddev]
- [x] T14 · Escribir `services/security_gate.py` con `gate_status(service, version)` — **Verifica:** `pytest` cubre `sin_corrida`, `en_curso`, `ok`, `fallo` y que vale la última corrida de la versión. [ngcddev]
- [x] T15 · Exigir puerta `ok` en `POST /api/change-requests/{id}/approve` antes de escribir en Gitea — **Verifica:** `pytest` con Gitea simulado (`tests/fake_gitea.py`): con puerta `en_curso` o `fallo` responde 409 con el motivo y Gitea no recibe ningún commit; con `ok` publica como antes (CA-6). [ngcddev]
- [x] T16 · Rechazar solas las solicitudes `pendiente` hacia una versión que falló (al cerrar la corrida y al crear la solicitud), con el texto del glosario para el cliente — **Verifica:** `pytest`: la solicitud queda `rechazada` con "Detenida por controles de seguridad: secretos" y, vista como cliente, el evento dice "Una actualización fue detenida porque contenía información sensible." (CA-5). [ngcddev]
- [ ] T17 · Crear `GET /api/services/{id}/security-runs`, `GET /api/change-requests/{id}/checks` y `GET /api/security-checks/{id}/report` — **Verifica:** desde `/docs` se lista la corrida de una versión y se descarga su SBOM (CA-4). [ ]

## Pantallas

- [ ] T18 · Agregar a `frontend/src/api.ts` los tipos y llamadas de la puerta — **Verifica:** `tsc` sin errores. [ ]
- [ ] T19 · Mostrar en `/agencia/cambios` los controles de la versión destino (✓ / ✗ / … con resumen y "Ver reporte") y deshabilitar "Aprobar" con el motivo si la puerta no está `ok` — **Verifica:** un cambio hacia una versión en curso muestra "…" y "Aprobar" deshabilitado; al terminar en `ok` se habilita sin recargar. [ ]
- [ ] T20 · Agregar a `/agencia/servicios` la columna "Controles de la versión activa" — **Verifica:** tras la demo, El Tornillo muestra ✓ en los 6 controles. [ ]

## Plataforma y repositorio

- [ ] T21 · Correr Gitleaks sobre la historia completa del monorepo y dejar `.gitleaks.toml` que solo permite los valores de desarrollo de `.env.example` — **Verifica:** `gitleaks git .` termina sin hallazgos (CA-8). [ ]

## Integración

- [ ] T22 · Publicar en k3s el Hub con la puerta (`PIPELINE_TOKEN` en un `Secret` y en `gitops/hub/api.yaml`) y pasar por la puerta los tags `v1`, `v1.1` y `v2` existentes — **Verifica:** `/agencia/servicios` muestra ✓ en la versión activa de los 3 sitios y `cosign verify` valida `restaurante:v2`. [ ]
- [ ] T23 · Repetir la prueba de root de la 003 (`bash gitops/pruebas/pod-security.sh ferreteria`) en `cliente-ferreteria` — **Verifica:** el Pod root es rechazado con el mensaje de la política `restricted` (CA-7). [ ]

## Cierre

- [ ] T24 · Demo: versión de El Tornillo con contraseña → "rechazada por seguridad" y el cliente ve el texto del glosario; versión limpia → pasa los 6 controles, se aprueba y se publica; se abre su evidencia; un Pod root es rechazado — **Verifica:** todos los criterios de [spec.md](spec.md#criterios-de-aceptación). [ ]

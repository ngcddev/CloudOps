# Plan 006 · Puerta de calidad y seguridad

> Cómo se construye [la spec](spec.md). Base: "Políticas de seguridad" y "Flujo de despliegue" de
> [constitution/tech-stack.md](../../constitution/tech-stack.md). Sin Kyverno. Se monta sobre lo que
> dejó la 005: el Hub sigue escribiendo el tag en `hub-gitops` al aprobar, pero solo si la versión
> pasó la puerta.

## Stack (módulo 3)

| Control | Herramienta | Falla si |
|---|---|---|
| Secretos | Gitleaks (commits nuevos de la versión) | Encuentra cualquier secreto |
| Construcción | `docker build` del sitio con `APP_VERSION=<tag>` | El build falla |
| Vulnerabilidades | Trivy (`--severity CRITICAL --ignore-unfixed --exit-code 1`) | Hay CVE crítica con arreglo |
| SBOM | Syft (SPDX JSON) | — (evidencia) |
| Firma | Cosign (`cosign sign --key`, clave en secreto de Gitea Actions) | — |
| Verificación | `cosign verify --key pipelines/cosign.pub` | Firma inválida o ausente |
| Pods | Pod Security Admission `restricted` (spec 003) | Pod root o privilegiado |

La puerta revisa seguridad, no salud: no arranca la imagen ni llama a `/health`. Así la v2 rota
(canónica) pasa los controles y el monitoreo del módulo 4 tiene qué detectar.

## Dónde vive el código de cada sitio

Hasta ahora las imágenes se construyen desde `apps/` del monorepo con `apps/publicar-imagenes.sh`.
Para que haya "subir una versión" en Gitea:

- Un repo por sitio en Gitea: `forja-digital/restaurante`, `forja-digital/ferreteria`,
  `forja-digital/consultorio`, sembrados desde `apps/<sitio>` por `pipelines/sembrar-repos-sitios.sh`
  (mismo estilo que `gitops/platform/gitea/sembrar-hub-gitops.sh`).
- Una versión = un tag de Git (`v1`, `v1.1`, `v2`…) en ese repo. El workflow se copia desde
  `pipelines/puerta.yaml` a `.gitea/workflows/puerta.yaml` de cada repo.
- Desde aquí, `apps/` queda como semilla: los cambios de los sitios se hacen en Gitea.

## Flujo

```
técnico ── push tag vX ──> repo del sitio en Gitea ──> Gitea Actions (runner fuera del PC A)
   gitleaks → build → trivy → syft → push al registro → cosign sign → cosign verify
   cada paso: POST /api/pipeline-events (token de la puerta)
                                   │
Hub: corrida de seguridad de (servicio, vX) = ok | fallo
   · si falla y hay una solicitud de cambio `pendiente` hacia vX → `rechazada` con el control
   · aprobar hacia vX exige corrida `ok` → escribe el tag en hub-gitops (código de la 005)
```

Sigue la regla de la constitución: `cosign verify` ocurre antes de que se escriba el tag y, sin firma
válida, no hay despliegue. Se escoge disparar la puerta al subir la versión (y no al aprobar): el Hub
no tiene que lanzar workflows en Gitea, la puerta no necesita permiso de escritura en `hub-gitops`, y
el Hub conserva la escritura del tag que ya probó la 005. El técnico ve el resultado antes de pedir
la aprobación.

## Workflow (`pipelines/puerta.yaml`)

- Se dispara con `push` de tags `v*`. Runner `act_runner` en un equipo de desarrollo con Docker, que
  ve `gitea.hub.local` y `hub.local` (archivo `hosts`).
- Gitleaks revisa los commits del tag que no están en tags anteriores
  (`--log-opts="<tag> --not <tags anteriores>"`): un secreto viejo ya corregido no bloquea para
  siempre, uno nuevo sí.
- La imagen se construye con Docker, se guarda en un tar y Trivy y Syft leen el tar. Se sube con
  `skopeo` (`--dest-tls-verify=false`) como en `apps/publicar-imagenes.sh`, y Cosign usa
  `--allow-http-registry` porque el registro de Gitea va por HTTP.
- El consultorio construye sus dos imágenes (`consultorio-web` y `consultorio-api`) en la misma
  corrida; la versión pasa solo si pasan las dos.
- `pipelines/reportar.sh <paso> <estado> <resumen> [reporte.json]` envía cada paso al Hub; el último
  paso corre siempre (`if: always()`) y cierra la corrida.

## Modelo de datos

| Tabla | Campos |
|---|---|
| `security_runs` | `id` · `service_id` FK · `version` · `commit_sha` · `status` (`en_curso` / `ok` / `fallo`) · `failed_step` · `image_digests` JSON · `started_at` · `finished_at` |
| `security_checks` | `id` · `run_id` FK · `step` (`secretos`, `construccion`, `vulnerabilidades`, `sbom`, `firma`, `verificacion`) · `image` · `status` (`ok` / `fallo`) · `summary` · `report` JSON · `created_at` |

Los reportes (JSON de Gitleaks y Trivy, SBOM, salida de `cosign verify`) se guardan en la base
(`report` JSON): no hace falta un volumen nuevo en el Hub y quedan con su respaldo. Una versión que se
vuelve a subir abre una corrida nueva; vale la última.

## Reglas en el Hub (`backend/app/services/security_gate.py`)

- `gate_status(service, version)` → `sin_corrida` · `en_curso` · `ok` · `fallo` (con el control).
- `approve` (router de la 005) llama a `gate_status` antes de `publish_version`: si no es `ok`
  responde 409 con el motivo y no escribe nada en Gitea.
- Al cerrar una corrida en `fallo`, las solicitudes `pendiente` hacia esa versión pasan a `rechazada`
  (transición `pendiente → rechazada` que ya existe) con motivo "Detenida por controles de seguridad:
  <control>"; el evento visible al cliente usa el texto del [glosario](../../docs/glosario.md) del
  control (secreto, vulnerabilidad, firma). Crear una solicitud hacia una versión ya fallida queda
  `rechazada` de una vez.
- Las versiones `v1`, `v1.1` y `v2` que ya están publicadas (sin firma) se vuelven a pasar por la
  puerta al sembrar los repos, para que tengan su corrida y su firma.

## API

| Método | Ruta | Quién | Qué hace |
|---|---|---|---|
| POST | `/api/pipeline-events` | token de la puerta (`PIPELINE_TOKEN`) | Abre la corrida, registra un paso o la cierra |
| GET | `/api/services/{id}/security-runs` | agencia | Corridas del servicio con sus controles |
| GET | `/api/change-requests/{id}/checks` | agencia | La corrida de la versión destino del cambio |
| GET | `/api/security-checks/{id}/report` | agencia | Descarga el reporte JSON (evidencia) |

## Pantallas

- Bandeja `/agencia/cambios` (de la 005): cada cambio muestra la puerta de su versión con ✓ / ✗ / …
  por control, el resumen y "Ver reporte". "Aprobar" queda deshabilitado con el motivo si la puerta
  no está `ok`.
- `/agencia/servicios`: columna "Controles de la versión activa".
- Portal del cliente: el evento de la solicitud dice el texto del glosario; nunca nombres de
  herramientas.

## Secretos (RNF-06)

- Secretos de Gitea Actions a nivel de la organización `forja-digital`: `COSIGN_PRIVATE_KEY`,
  `COSIGN_PASSWORD`, `REGISTRY_USER`, `REGISTRY_PASSWORD`, `HUB_URL`, `HUB_PIPELINE_TOKEN`.
- `pipelines/cosign.pub` sí va en el repo (es pública); `cosign.key` ya está en `.gitignore`.
- `PIPELINE_TOKEN` en `.env.example` (valor de desarrollo) y en un `Secret` del Hub en k3s.
- Gitleaks recorre una vez la historia completa del monorepo; `.gitleaks.toml` solo permite los
  valores de desarrollo de `.env.example`.

## Contratos con otras specs

- Recibe de **003**: Pod Security `restricted` y registro de Gitea. De **005**: `change_requests`,
  `change_flow.py`, `publish_version`, `/agencia/cambios`.
- Entrega a quien publique versiones después: ninguna versión se publica sin corrida `ok`.
- Entrega a los reportes: `security_runs` y `security_checks` como evidencia por versión.

## Riesgos

| Riesgo | Respuesta |
|---|---|
| La base de datos de Trivy necesita internet | Descargarla en el runner antes de la demo y usar `--skip-db-update` |
| Un tag del registro se puede sobrescribir después de verificado | Solo la puerta tiene usuario de escritura en el registro; el Hub guarda el digest verificado como evidencia. Fijar el digest en `hub-gitops`: mejora futura |
| El registro de Gitea no acepta firmas de Cosign | Probarlo primero (T05); si falla, guardar la firma como archivo junto al SBOM |
| La firma no se verifica en el clúster | Nadie despliega a mano (principio 3); documentado como mejora futura |
| El runner necesita Docker y RAM | Corre fuera del PC A (tech-stack) |

## Cómo se verifica

- `pytest`: eventos de la puerta con token bueno y malo, cierre en `ok` y en `fallo`, aprobar con
  puerta `en_curso` / `fallo` / `ok`, rechazo automático de la solicitud pendiente.
- Tres corridas reales: versión con secreto (falla en secretos), imagen vulnerable (falla en
  vulnerabilidades), versión limpia (pasa y se publica).
- Demo de [spec.md](spec.md#demo-de-cierre).

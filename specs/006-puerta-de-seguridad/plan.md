# Plan 006 · Puerta de calidad y seguridad

> Cómo se construye [la spec](spec.md). Base: "Políticas de seguridad" y "Flujo de despliegue" de
> [docs/tech-stack.md](../../docs/tech-stack.md). Sin Kyverno.

## Stack (módulo 3)

| Control | Herramienta | Falla si |
|---|---|---|
| Secretos | Gitleaks | Encuentra cualquier secreto |
| Pruebas | pytest / build del sitio | Una prueba falla |
| Vulnerabilidades | Trivy (`--severity CRITICAL --exit-code 1`) | Hay CVE crítica |
| SBOM | Syft (SPDX JSON) | — (evidencia) |
| Firma | Cosign (`cosign sign` con clave en secreto de Gitea) | — |
| Verificación | `cosign verify` antes de tocar `hub-gitops` | Firma inválida o ausente |
| Pods | Pod Security Admission `restricted` (spec 003) | Pod root o privilegiado |

## Pipeline (`pipelines/site.yaml`, Gitea Actions)

```
checkout → gitleaks → tests → docker build → trivy → syft → push → cosign sign
        → cosign verify → reportar al Hub → (si todo ok) actualizar tag en hub-gitops
```

- Corre en el runner fuera del PC A.
- Cada paso reporta al Hub: `POST /api/pipeline-events` con `change_request_id`, `step`, `status`,
  `summary` y los reportes (JSON de Trivy, SBOM, resultado de verify).
- El Hub autentica al pipeline con un token propio (secreto de Gitea Actions).

## Cambio respecto a la spec 005

Desde esta spec, **quien actualiza el tag es el pipeline**, no el Hub directamente: aprobar en el
Hub dispara el pipeline (`workflow_dispatch` vía API de Gitea) y el tag solo cambia si todos los
controles pasan. El estado del cambio pasa a `en_validacion` mientras corre.

## Modelo de datos

| Tabla | Campos |
|---|---|
| `security_checks` | `id` · `change_request_id` FK · `step` · `status` (`ok` / `fallo`) · `summary` · `report_path` · `created_at` |

Los reportes se guardan en un volumen del Hub (`/data/evidence/<cambio>/`), no en Git.

## API y pantallas

- `POST /api/pipeline-events` (token del pipeline).
- `GET /api/change-requests/{id}/checks`.
- Detalle del cambio en la consola: lista de controles con ✓ / ✗ y enlace al reporte.
- Portal del cliente: texto del [glosario](../../docs/glosario.md) según el control que falló.

## Secretos (RNF-06)

- Clave de Cosign, tokens de Gitea/Hub: secretos de Gitea Actions.
- `.env.example` con valores de desarrollo; `.gitignore` bloquea `cosign.key`, `.env` y similares.
- Gitleaks también corre sobre el monorepo en cada PR.

## Riesgos

| Riesgo | Respuesta |
|---|---|
| Base de datos de Trivy necesita internet | Descargarla antes de la demo y usar `--skip-db-update` |
| La firma no se verifica en el clúster | Nadie despliega a mano; documentado como mejora futura |

## Cómo se verifica

- Tres corridas del pipeline: con secreto (falla), con imagen vulnerable (falla), limpia (publica).
- Demo de [spec.md](spec.md#demo-de-cierre).

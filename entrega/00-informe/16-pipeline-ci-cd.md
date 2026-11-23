<!-- Sección 16 · Fuente: pipelines/puerta.yaml, pipelines/puerta.sh, pipelines/lib.sh, pipelines/hallazgos.yaml, .github/workflows/ci.yml, .trivyignore.yaml, .gitleaks.toml (leídos el 16 nov 2026) -->

# Pipeline CI/CD

El proyecto tiene dos pipelines que comparten las mismas herramientas de seguridad con las mismas versiones (`pipelines/lib.sh:6-9`). La **CI del repositorio** (`.github/workflows/ci.yml`) valida cada cambio al código del Hub: lint, pruebas, observabilidad, análisis estático y seguridad de la imagen de producción. La **puerta de seguridad** (`pipelines/puerta.yaml`) valida cada versión de un sitio de cliente: corre en Gitea Actions al subir una etiqueta `v*`, publica y firma la imagen y reporta cada control al Hub, que solo deja aprobar una versión cuya corrida terminó en «ok». El despliegue no ocurre en el pipeline: lo hace Argo CD a partir de un commit (ver la sección de GitOps y ADR-01).

## Etapas y herramientas

::: {custom-style="Table Caption"}
**Tabla {T:etapas}**\
*Etapas del pipeline, herramienta, criterio de bloqueo y dónde corren*
:::

| Etapa | Herramienta y versión | Criterio de bloqueo | CI | Puerta |
|--------|------------------|------------------------|----|----|
| Lint | `ruff` (`ruff.toml`); `tsc` y `vite build` | Cualquier aviso de `ruff` o error de tipos | Sí (`ci.yml:30,39`) | No |
| Pruebas | `pytest` del backend (1.134 recogidas) y de `ai/`; pruebas del sitio | Cualquier prueba que falle | Sí (`ci.yml:51,60`) | Sí, dentro de «construir» |
| Construcción | Docker, multi-stage, sin root | La imagen no construye, corre como root, trae `pytest` o no responde `/health` | Sí (`ci.yml:123`) | Sí (`puerta.sh`, paso `construir`) |
| Secretos | Gitleaks v8.30.1 sobre toda la historia con `.gitleaks.toml` | Cualquier secreto que no esté en la lista de permitidos | Sí (`ci.yml:119-122`) | Sí (`puerta.sh:92-99`) |
| Análisis estático | `bandit` (SAST) y `trivy fs` | Hallazgo ALTO o CRÍTICO sin decisión vigente | Sí (`ci.yml:97`) | `trivy fs` sobre dependencias (`puerta.sh:160-163`) |
| Vulnerabilidades de la imagen | Trivy 0.76.1, imagen | CRÍTICAS con arreglo publicado (`--ignore-unfixed`) | Sí (`ci.yml:127-132`) | Sí (`puerta.sh:137-140`) |
| Configuración insegura | Trivy `config` sobre Dockerfile y manifiestos | ALTA o CRÍTICA fuera de las excepciones con vencimiento (`.trivyignore.yaml`) | Sí (`ci.yml:133-135`) | Sí (`puerta.sh:149-152`) |
| SBOM y licencias | Syft v1.55.0 (SPDX); Trivy `sbom --scanners license` | Licencia CRÍTICA; las restringidas (ALTA) se cuentan y se informan | Sí (`ci.yml:136-141`) | Sí (`puerta.sh:181-185`) |
| Firma y procedencia | Cosign v3.1.4 con clave; atestación SLSA (`slsaprovenance1`) y del SBOM (`spdxjson`) | No se puede firmar o atestar | No (decisión D11) | Sí (`puerta.sh:205-228`) |
| Publicación | Registro de contenedores de Gitea, por `digest` | No se publica una imagen que no pasó los pasos anteriores | No | Sí (`puerta.sh`, paso `firmar`) |
| Verificación | Cosign: firma, procedencia y SBOM con la clave pública del Hub | Firma ajena o procedencia de otro commit | No | Sí (`puerta.sh:247-265`) |
| Despliegue | Argo CD sobre `hub-gitops` | Fuera del pipeline | — | — |

::: {custom-style="Nota"}
*Nota.* Elaboración propia a partir de `.github/workflows/ci.yml`, `pipelines/puerta.yaml`, `pipelines/puerta.sh` y `pipelines/lib.sh`. La CI de GitHub no firma ni publica la imagen del Hub porque no alcanza el registro del laboratorio (ADR-10); la puerta de Gitea no prueba la imagen del Hub.
:::

Además de la CI, el trabajo `operacion` valida la observabilidad (`promtool`, `amtool`, `kustomize`), que Grafana cargue el tablero provisionado, las trazas del Hub de punta a punta, que el chart de Helm coincida con Kustomize y el respaldo y la restauración de PostgreSQL (`ci.yml:68-90`).

## Evidencia de ejecución

- **CI de GitHub:** cinco verificaciones por cambio (`calidad`, `pruebas`, `operacion`, `analisis` y `seguridad`) sobre cada solicitud de cambio.
- **Puerta de seguridad en Gitea:** al subir las etiquetas `v1` y `v2` del repositorio `forja-digital/colegio` (14 de noviembre de 2026), el ejecutor disparó la puerta por sí solo y dejó dos corridas en `ok` con los 11 controles registrados en el Hub, de aproximadamente un minuto cada una (`docs/bitacora.md:408`).
- **Capturas pendientes:** la corrida aprobada en Gitea (E-04), la corrida rechazada por un secreto (E-05, que se prepara con la tarea T03 de la especificación 015), el reporte de Trivy y el SBOM (E-06) y la verificación de Cosign (E-07) se describen en el Apéndice A.
- **Simulador de la puerta:** `pipelines/pruebas/simular-puerta.sh` corre los mismos pasos contra el Hub real y un registro local con nueve escenarios: `limpia` (pasa los seis controles, queda firmada y verificada) y ocho que deben fallar en el control correspondiente (`secreto`, `vulnerable`, `configuracion`, `dependencia`, `manifiesto`, `firma-ajena`, `procedencia` y `pruebas`).

## Política de tratamiento de vulnerabilidades

La política parte de un principio: lo corregible se corrige y no se acepta. La puerta bloquea toda vulnerabilidad crítica con arreglo publicado y toda dependencia con hallazgo alto o crítico con arreglo. Las vulnerabilidades sin arreglo publicado se tratan en un registro de hallazgos aceptados (`pipelines/hallazgos.yaml`), que es la fuente de verdad y tiene estas reglas:

1. Cada regla indica el paquete y el CVE, el estado (`not_affected` con una justificación del vocabulario de OpenVEX, o `affected` con mitigaciones), quién puede explotarlo y en qué condiciones, el tratamiento (aceptar o mitigar), el detalle y una fecha de revisión.
2. `pipelines/hallazgos.py` cruza el registro con los reportes de Trivy, genera el VEX (OpenVEX) y frena si queda un hallazgo sin decisión, con arreglo disponible o con la decisión vencida. Cada regla se revisa como máximo a los seis meses.
3. Las mitigaciones comunes son: contenedores sin root, sin escalada de privilegios, sin capacidades de Linux, con perfil `seccomp` por defecto, Pod Security `restricted`, NetworkPolicy y sin token de la API de Kubernetes montado.
4. Las excepciones de `trivy config` (`.trivyignore.yaml`) tienen razón y fecha de vencimiento: al vencer vuelven a fallar. Los sitios de clientes quedaron fuera de la excepción de sistema de archivos de solo lectura (KSV-0014): si uno vuelve a escribir en disco, Trivy lo frena.

El registro y el VEX se guardan como artefacto de la CI (`ci.yml:99-105`).

## Control de secretos y accesos

::: {custom-style="Table Caption"}
**Tabla {T:secretos-pipeline}**\
*Controles de secretos y accesos del pipeline*
:::

| Riesgo | Control | Evidencia |
|----------|------------------------------|---------------------|
| Secretos en el repositorio | Gitleaks sobre toda la historia, con lista de permitidos acotada por línea completa a valores falsos conocidos | `.gitleaks.toml`, `ci.yml:119-122` |
| Secretos en el pipeline | Los secretos se definen en la organización de Gitea (`HUB_URL`, `HUB_PIPELINE_TOKEN`, `REGISTRY_*`, `COSIGN_*`); el valor viaja por entrada estándar y no queda en la lista de procesos; ninguno está en el archivo del workflow | `pipelines/configurar-gitea.sh:62-70`, `pipelines/puerta.yaml:1-7` |
| Clave de firma | Par de claves de Cosign creado y rotado con `configurar-gitea.sh --rotar-claves`; la clave pública está en el repositorio | `pipelines/cosign.pub`, `pipelines/configurar-gitea.sh` |
| Pipeline que reporta al Hub | Token de máquina propio (`HUB_PIPELINE_TOKEN`) para `POST /api/pipeline-events`, distinto de las sesiones de personas | `backend/app/routers/pipeline.py:30` |
| Permisos de la CI de GitHub | `permissions: contents: read` | `.github/workflows/ci.yml:14-15` |
| Ejecutor comprometido | El ejecutor corre con todas las capacidades de Linux retiradas y sin poder ganar privilegios nuevos | `pipelines/runner/docker-compose.yml:21-23` |
| Escritura indebida en `hub-gitops` | Regla de protección de la rama: el Hub solo escribe los archivos de cada cliente | `gitops/proteccion_hub_gitops.py` (ADR-03) |
| Aprobación sin segunda persona | Quien pide un cambio no lo aprueba | `backend/app/routers/change_requests.py:181` (ADR-11) |

::: {custom-style="Nota"}
*Nota.* Elaboración propia. Fuentes: los archivos citados, leídos el 16 de noviembre de 2026.
:::

**Límites.** La firma se verifica en el pipeline y no dentro del clúster (ADR-09); el registro de Gitea se usa por HTTP en laboratorio; la puerta de seguridad no prueba la imagen del Hub, que se valida en la CI de GitHub.

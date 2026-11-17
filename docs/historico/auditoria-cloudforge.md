> **Documento histórico** (auditoría del 14 nov 2026 (versiones y conteos de esa fecha)). Se conserva como registro y **no describe el estado actual**. Las cifras vigentes están en el paquete de evidencias de la entrega final (`entrega/evidencias/`).

# Auditoría técnica del proyecto integrador CloudForge AI (notas de trabajo)

> Auditoría solo de lectura del repositorio (14 nov 2026, rama `main`, 723 commits). No se modificó código.
> Rúbrica leída completa: `Diplomado_CloudForge_AI_5.0.md` (576 líneas). Estados: Completo · Parcial · No existe · No verificable.
> "No verificable" = requiere ejecutar algo (clúster, pytest, Ollama); se indica la prueba que lo confirmaría.

## Fase 1. Rúbrica extraída (R1..R43)

**A. Entregables mínimos del módulo 7 (sección 6)**: R1 contexto/decisiones · R2 repo Git con ramas, issues, README · R3 app contenedorizada con pruebas ·
R4 manifests K8s/Helm/Kustomize · R5 pipeline CI/CD con calidad y seguridad · R6 SBOM + escaneo + firma/verificación · R7 repo GitOps con Argo CD ·
R8 IaC · R9 dashboard con SLI/SLO · R10 registro de experimentos/modelos · R11 servicio IA local con RAG o generación · R12 workflow multimodal adicional
(obligatorio) · R13 análisis de privacidad, seguridad, licencias y riesgos IA · R14 runbook (operación, respaldo, recuperación) · R15 informe ejecutivo, demo y sustentación.

**B. Rúbrica del proyecto (sección 7.2, 20 % de la nota del diplomado)**: R16 arquitectura/requisitos/decisiones (10 %) · R17 Kubernetes, GitOps e IaC (20 %) ·
R18 DevSecOps y cadena de suministro (15 %) · R19 observabilidad, SLI/SLO y operación (10 %) · R20 MLOps/LLMOps y reproducibilidad (15 %) ·
R21 IA local y multimodal (15 %) · R22 documentación, privacidad, sostenibilidad y sustentación (15 %).

**C. Tecnología nombrada en entregables y laboratorios (sección 8.2)**: R23 Git+Docker+Compose · R24 Kubernetes local/compartido (kind/k3d/k3s) · R25 Helm/Kustomize + Argo CD ·
R26 Backstage (catálogo mínimo) · R27 OpenTofu · R28 Trivy+Syft+Cosign · R29 SLSA/procedencia · R30 OpenTelemetry · R31 Prometheus+Grafana+Loki ·
R32 MLflow · R33 Ollama/GPT4All · R34 AnythingLLM/Open WebUI · R35 Stability Matrix+ComfyUI · R36 video (Wan2.2)/2D→3D (Hunyuan3D)/audio (solo hace falta UNA modalidad extra, cubierta por R12).

**D. Condiciones transversales (secciones 6, 7, 9, 11.6)**: R37 jurado puede clonar, seguir instrucciones y desplegar · R38 equipo de 3 a 5 y caso realista del Cauca ·
R39 gobierno de IA (trazabilidad de prompts, validación, ficha por modelo, datos sintéticos) · R40 continuidad sin Internet (kit offline) ·
R41 falla inducida y recuperación · R42 endurecimiento de ejecución (no root, límites, políticas, secretos) · R43 certificación (80 % asistencia + "Plan Estratégico de Desarrollo Sostenible y Marketing").

Inconsistencias de la rúbrica: R43 parece copiada de otro diplomado (el propio documento lo advierte); fechas del documento (14 sep–20 nov) distintas a las del repo (28 sep–30 nov).

## Fase 2. Resumen (≤ 15 líneas)

CloudOps Client Hub es un "centro de operación de servicios" para agencias web que atienden PyMEs: el flujo empieza en el cliente (cliente → servicio → plan/SLA), no en el código.
Hub = FastAPI + PostgreSQL 16 + React/Vite (`backend/`, `frontend/`): clientes, tickets con prioridad P1–P4 y SLA, solicitudes de cambio, incidentes, rollback, KPIs, bitácora, roles agencia/cliente.
El Hub nunca toca Kubernetes: escribe en Gitea (`hub-gitops`), lee Argo CD y Prometheus (`backend/app/integrations/`).
Flujo: tag `vN` en el repo del sitio → Gitea Actions `puerta.yaml` (Gitleaks → build → Trivy → Syft → Cosign sign → cosign verify) reporta cada paso al Hub (`routers/pipeline.py`) →
el Hub solo deja aprobar versiones con puerta en "ok" (`routers/change_requests.py:172-174`) → commit del tag en `hub-gitops` → Argo CD sincroniza (selfHeal/prune) al namespace del cliente
(PSA `restricted`, NetworkPolicy, ResourceQuota por plan) → Blackbox/Prometheus sondea `/health` cada 5 s → `SitioCaido` (30 s) → Alertmanager → webhook al Hub abre incidente P1 con SLA →
rollback = `git revert` en `hub-gitops` → Argo CD reconcilia → el Hub cierra con MTTR. Loki+Alloy guardan logs; OpenTofu crea clientes (overlay + Application).
IA: asistente de ayuda con Ollama (Qwen2.5-7B) protegido por una compuerta Naive Bayes propia; evaluación con preguntas ciegas; corridas en JSON (MLflow opcional, no instalado).
Propuesta comercial: vender el servicio gestionado (SLA medible, lenguaje de negocio para el cliente, recuperación auditada, IA local sin que salgan datos) frente a "solo publicar" (Vercel).
Demostrable: caso del restaurante (v2 rota → alerta ≤ 45 s → incidente P1 → rollback → MTTR). Faltan: multimodal, MLflow, runbooks, tableros de Grafana, borradores IA del incidente, reportes, informe/demo.
Riesgo inmediato: el código del asistente (`ai/`, `backend/app/services/assistant*.py`, migraciones 0010/0011, `Assistant.tsx`) está sin commit (`git status`), y `gitops/hub/api.yaml:37` sigue en la imagen `hub-api:v1.6` sin `OLLAMA_URL`.

## Fase 3. Tabla final

Ver la tabla del reporte entregado en el chat (misma tabla, misma numeración). Resumen de estados:
Completo: R3 R4 R6 R7 R8 R9 R16 R17 R23 R24 R25 R26 R27 R28 R31 R33* R38 R41 R42 · Parcial: R1 R2 R5 R10 R11 R13 R15 R18 R19 R20 R21 R22 R29 R30 R37 R39 · No existe: R12 R14 R32 R34 R35 R36 R40 · No verificable: R43 (y la ejecución real de varios Completos).
(*R33 se baja a Parcial en la tabla: Ollama no está conectado al Hub del clúster.)

## No verificable solo leyendo código (y qué lo confirma)

| Qué | Prueba que lo confirmaría |
|---|---|
| "573 pruebas pasando" (`docs/cumplimiento-diplomado.md`) | `docker compose exec api pytest` (se contaron 451 funciones `test_` en `backend/tests` y 20 en `apps/`; la parametrización puede subir la cifra) |
| Clúster k3s corriendo, Applications `Synced/Healthy` | `kubectl -n argocd get applications` y `gitops/pruebas/ciclo-gitops.sh` |
| Detección ≤ 60 s y MTTR | `observability/pruebas/cronometro.sh` |
| Firma verificable de punta a punta | `pipelines/pruebas/simular-puerta.sh` |
| Aislamiento de red y PSA | `gitops/pruebas/aislamiento-red.sh`, `gitops/pruebas/pod-security.sh` |
| Resultados de la evaluación del LLM | `python ai/eval/run_eval.py --archivo ai/eval/preguntas_ayuda_ciegas.jsonl` (requiere Ollama) |
| Despliegue en VPS (spec 011 T17, "falta probar el inicio de sesión") | Abrir la URL pública e iniciar sesión |

## Actualización del 14 nov (tras MLflow y RAG)

Cambios de estado respecto de la auditoría: **R10 Completo** (MLflow con Model Registry y alias `production`), **R20 y R32** suben (MLflow existe),
**R11 Completo** y **R34 Completo (equivalente)**: RAG propio con embeddings; **R39 Parcial** sigue (falta la ficha por modelo) y se suma la validación de
inyección de prompts (10 casos, 9 resistidos con el prompt v3). Siguen abiertos R12/R35 (ComfyUI, fuera de alcance por ahora) y R14, R15, R5. El cumplimiento
aproximado sube de ~66 % a ~72 %. Detalle, cifras y decisiones en `docs/bitacora.md`. Lo nuevo **no se probó en el clúster** (T27) y sigue sin commit.

## Actualización del 14 nov (segunda tanda: operación, CI, borradores, reportes, trazas)

Cambios de estado respecto de la auditoría original: **R5 Completo** (CI con ruff, pytest, tsc, Gitleaks, Trivy y Syft, y la puerta de los sitios con pruebas), **R9 y R19**
suben (tablero de Grafana con SLI/SLO y presupuesto de error, trazas con Tempo, cuentas probadas con promtool), **R14 Parcial** (respaldo y restauración probados;
falta el runbook como documento), **R15 Parcial** (reportes operativo y ejecutivo en PDF; falta el informe y la demo), **R29 Completo** (atestación SLSA v1 verificada contra el
commit), **R30 Completo** (trazas del Hub; sin spans de SQL por incompatibilidad con SQLAlchemy 2.1), **R40 Parcial** (kit offline probado con un subconjunto), **R42** mejora (Pod
Security y NetworkPolicy en `hub`, imagen de producción sin pruebas, **no probado en clúster**), **R37** mejora (script de reinicio de la demo). Siguen abiertos R12/R35
(ComfyUI, fuera de alcance) y los documentos formales. No se migró a pgvector por datos (bitácora D7). El cumplimiento aproximado sube de ~72 % a ~84 % (estimación; los documentos
formales y ComfyUI son lo que falta). Detalle en `docs/bitacora.md`.

### Clúster encendido y probado (14 nov, tercera tanda)

Lo que antes figuraba «no verificable» se probó en un k3s real: Argo CD sincronizando los tres clientes y la observabilidad, el caso del restaurante de punta a punta
(MTTR 1,5 min), Pod Security y aislamiento de red, la NetworkPolicy del Hub, el respaldo y la restauración con el CronJob, el asistente con RAG, los borradores de IA, los reportes en PDF y las
trazas en Tempo. R7, R17, R24, R25, R41 y R42 pasan de «Completo (no verificable)» a verificados. Se encontraron y corrigieron seis problemas que solo el clúster mostraba (bitácora).
Siguen sin probarse el runner de Gitea Actions y Backstage. Cumplimiento aproximado: ~86 %.

# Cumplimiento del diplomado CloudForge AI 5.0

> Compara lo que exige el [documento del diplomado](diplomado-cloudforge-ai-5.0.md) (entregables mínimos del módulo 7,
> matriz de evidencias, tecnologías y rúbrica) con lo que existe hoy en este repositorio.
> Revisado el **13 nov 2026**. Cada «Hecho» cita la evidencia; si no hay evidencia, no se marca.
> Estados: **Hecho** · **Parcial** (existe pero no cubre todo lo que pide) · **Falta** (no existe).

## Resumen

| | Cantidad |
|---|---|
| Entregables mínimos (15) | 8 hechos · 4 parciales · 3 faltan (actualizado el 14 nov: MLflow y RAG, ver [bitácora](bitacora.md)) |
| Tecnologías nombradas por el diplomado | ComfyUI no se usa: la modalidad adicional es audio (faster-whisper y Piper, 15 nov); OpenTelemetry está a medias; MLflow y el RAG ya existen (14 nov); video y 3D no se exigen |

**Actualización del 15 nov:** el componente multimodal (12, audio), los runbooks (14), el registro de modelos en MLflow (10) y las fichas de modelos y privacidad (13) ya están hechos; ver la [bitácora](bitacora.md).

**Lo que más pesaba y faltaba (antes del 15 nov):** el componente multimodal (entregable 12), el runbook (14), el registro de modelos en MLflow
(10) y la ficha de modelos y privacidad (13). Son obligatorios según el documento y ninguno está construido todavía.

## Entregables mínimos del proyecto integrador

| # | Entregable del diplomado | Estado | Evidencia en el repo | Qué falta |
|---|---|---|---|---|
| 1 | Contexto, usuarios, requisitos, restricciones y decisiones de arquitectura | **Parcial** | `docs/context.md`, `docs/personas.md`, `docs/requerimientos.md`, `constitution/` | No hay registro de decisiones de arquitectura (tipo ADR): las decisiones están dispersas en la constitución y los planes |
| 2 | Repositorio Git con ramas, issues, README y convenciones | **Parcial** | `README.md`, `constitution/conventions.md` (ramas y commits), `.github/pull_request_template.md` | No hay plantillas de issues: el backlog vive en `specs/*/tasks.md`. Conviene decirlo en el README |
| 3 | Aplicación contenedorizada con pruebas automatizadas | **Hecho** | `backend/Dockerfile`, `docker-compose.yml`, 573 pruebas (`pytest`), sitios en `apps/` | — |
| 4 | Manifests de Kubernetes y/o Helm/Kustomize | **Hecho** | `gitops/` con Kustomize (`_base` + overlays por cliente) | Helm no se usa; el documento acepta Kustomize («Helm/Kustomize») |
| 5 | Pipeline CI/CD con controles de calidad y seguridad | **Parcial** | `pipelines/puerta.yaml`: Gitleaks, build, Trivy, Syft, Cosign, verificación | La puerta no corre pruebas ni lint, y no cubre la imagen del Hub: las 573 pruebas solo se corren a mano |
| 6 | Evidencia de SBOM, escaneo y firma/verificación | **Hecho** | `pipelines/` (Syft, Trivy, Cosign, `cosign.pub`); `security_runs` guarda `commit_sha` y digests de imagen; el Hub los muestra | — |
| 7 | Repositorio GitOps con Argo CD sincronizado | **Hecho** | `gitops/platform/argocd/applications/`, repo `forja-digital/hub-gitops`, `gitops/pruebas/ciclo-gitops.sh` | — |
| 8 | IaC para lo viable en el laboratorio | **Hecho** | `infra/tofu/` (OpenTofu, módulo `client-env`), `infra/client-new.sh`; probado también con Terraform (spec 011) | — |
| 9 | Dashboard de observabilidad con al menos un SLI/SLO | **Hecho** (con un pero) | El tablero del Hub (spec 010) calcula la disponibilidad del mes desde Prometheus y la compara con el SLO del plan; `observability/` con Prometheus, Alertmanager, Loki, Blackbox | Grafana está instalado pero **sin ningún tablero**: solo fuentes de datos. Un jurado que abra Grafana verá vacío |
| 10 | Registro de experimentos/modelos (MLOps) | **Hecho** (14 nov, en el equipo de desarrollo) | `ai/classifier/train.py` y `ai/eval/run_eval.py` registran cada corrida en `runs/` con parámetros y métricas | El servidor aún corre en el equipo de desarrollo, no en el PC B; el registro del modelo `compuerta-asistente` con alias `production` y `ai/tests/` están probados |
| 11 | Servicio de IA local con RAG o generación de código/documentación | **Hecho** (14 nov; el RAG se activa con `ASSISTANT_CONTEXT_MODE=rag`, aún sin llevar al clúster, T27) | Asistente con Ollama (`qwen2.5:7b-instruct`), ayuda del Hub como contexto, evaluación con preguntas ciegas: 100 % (16 preguntas), 13/13 «sin información» correctas | RAG propio con `nomic-embed-text` e índice en PostgreSQL (`kb_chunks`); iguala al contexto completo en el conjunto ciego. No se usa AnythingLLM (decisión D1 de la bitácora) |
| 12 | Workflow multimodal adicional (imagen, video, audio o 2D→3D) | **Hecho** (audio, 15 nov) | `voz/` (faster-whisper y Piper en CPU), API `/api/assistant/voice/*`, pantalla del asistente, `ai/eval/evaluar_voz.py` y prueba en navegador real (`voz/pruebas/voz-ui.sh`) | Corre también en el clúster (`hub-voz` y `https://hub.local`, probado en un navegador real el 15 nov); falta la fase 2 (memoria de la charla) |
| 13 | Análisis de privacidad, seguridad, licencias, riesgos de IA y límites | **Parcial** | Principios 2 y 6, datos ficticios, `constitution/principles.md`, puerta de seguridad | Falta la **ficha por modelo** (origen, licencia, tamaño, fecha, hash) y un análisis escrito de riesgos de IA y Ley 1581 |
| 14 | Runbook de operación, respaldo, recuperación y fallas comunes | **Falta** | Solo hay scripts de demo (`gitops/pruebas/`) y el rollback del Hub | No existe ningún runbook ni procedimiento de respaldo/restauración de PostgreSQL ni del clúster |
| 15 | Informe ejecutivo, demo técnica y sustentación | **Falta** (planificado) | Specs 013 (reportes) y 015 (demo integrada) con solo spec y plan; `gitops/pruebas/demo-caso-restaurante.sh` | Informe ejecutivo, guion y ensayo de la demo integrada |

## Matriz mínima de evidencias por equipo (sección 11.6)

| Dimensión | Estado | Evidencia o brecha |
|---|---|---|
| Reproducibilidad | Hecho | `docker compose up --build` levanta el Hub y los sitios; probado el 13 nov con 573 pruebas pasando. Falta un script de reinicio de la demo (spec 015) |
| Seguridad | Hecho | Reporte de la puerta guardado en el Hub (`security_runs`, `security_checks`) |
| GitOps | Hecho | Aplicaciones Argo CD `Synced` |
| Observabilidad | Parcial | Falta al menos un tablero en Grafana (el del Hub sí existe) |
| MLOps | Hecho | MLflow con corridas, Model Registry y alias `production` (14 nov) |
| LLMOps local | Hecho | Evaluación con preguntas de referencia y respuestas literales (`ai/eval/`) |
| Multimodal | Hecho (audio) | Spec 021 |
| Privacidad y licencia | Falta | Ficha por modelo |
| Operación | Falta | Runbook |

## Tecnologías de referencia (sección 8.2)

El documento aclara que las marcas son referencias y que las competencias son independientes del proveedor, pero evalúa
cada una de estas capacidades. Las marcadas ★ son las que nombra en sus entregables o laboratorios.

| Área | Referencia del diplomado | Nosotros | Estado |
|---|---|---|---|
| Control de versiones y contenedores | Git, Docker, Compose ★ | Git, Docker, Compose | Hecho |
| Kubernetes local/compartido | kind, minikube o k3d; k3s ★ | k3d en desarrollo y k3s en el PC A | Hecho |
| Despliegue | Helm, Kustomize, Argo CD ★ | Kustomize y Argo CD | Hecho (sin Helm, equivalente aceptado) |
| Platform Engineering | Backstage o diseño equivalente ★ | Backstage con catálogo mínimo (`gitops/platform/backstage/`, `catalog-info.yaml`); se apaga si falta RAM | Hecho, pero hay que mostrarlo encendido en la demo |
| IaC | OpenTofu ★ | OpenTofu (y Terraform) | Hecho |
| DevSecOps | Trivy, SBOM, Cosign, SLSA ★ | Trivy, Syft, Cosign, Gitleaks; procedencia por `commit_sha` y digest | Hecho (SLSA como práctica, sin nivel certificado, como pide el documento) |
| Observabilidad | OpenTelemetry, Prometheus, Grafana, Loki ★ | Prometheus, Grafana, Loki, Alloy, Alertmanager, Blackbox; OpenTelemetry solo en las métricas del formulario del consultorio | Parcial: OpenTelemetry es mínimo y no hay trazas |
| MLOps | MLflow ★ (Kubeflow opcional) | MLflow 3.18 (`ai/servidor-mlflow/`) con Model Registry | Hecho |
| LLM/SLM local | GPT4All u Ollama ★ | Ollama con Qwen2.5 3B y 7B | Hecho |
| RAG y frontend | AnythingLLM u Open WebUI | RAG propio (embeddings de Ollama + índice en PostgreSQL); sin AnythingLLM ni Open WebUI | Hecho (equivalente) |
| Imagen generativa | Stability Matrix y ComfyUI ★ | Ninguna: se eligió audio (faster-whisper y Piper, CPU) como modalidad adicional por consumo | Decisión del equipo; el diplomado exige una modalidad adicional, no la imagen |
| Video generativo | Wan2.2 (en nodo compartido) | Ninguna | No exigido: basta una modalidad adicional |
| 2D a 3D | Hunyuan3D, Blender | Ninguna | No exigido: basta una modalidad adicional |
| Documentación | Markdown, MkDocs/TechDocs | Markdown en `docs/`, `specs/`, `constitution/` | Hecho |

El documento exige **al menos una** modalidad adicional a la de texto (imagen, video, audio, 2D→3D o visión), así que video y 3D
no son obligatorios; ComfyUI para la infografía (spec 014) sí es el camino previsto.

## Diferencias entre el documento y nuestro proyecto

| Tema | El documento | Nosotros | Qué hacer |
|---|---|---|---|
| Fechas | 14 sep – 20 nov 2026, 10 semanas | 28 sep – 30 nov, 9 semanas (README, roadmap) | Confirmar con el profesor cuál es el calendario vigente; el del repo parece el acordado con el grupo |
| Equipo | De 3 a 5 personas | 5 (4 de Sistemas y 1 Industrial) | Cumple |
| Certificación | Párrafo copiado de otro diplomado (Plan de Desarrollo Sostenible y Marketing) | Proyecto integrador | El propio documento lo marca como inconsistente: confirmar con Educación Continua |
| Evaluación del proyecto | Rúbrica de 7 criterios (20 % del diplomado) | `docs/requerimientos.md` y `specs/015` | Mapear la demo a la rúbrica (ver abajo) |
| Reproducibilidad | El jurado debe clonar, seguir instrucciones y desplegar | `docker compose up --build` documentado en `CLAUDE.md` y `backend/README.md` | Agregar en el README un «cómo reproducir en 10 minutos» y el script de reinicio de datos (spec 015) |
| Estructura sugerida (`deploy/`, `platform/`, `runbooks/`, `ai-workflows/`) | Es una sugerencia | `gitops/`, `observability/`, `ai/`, `infra/`, `pipelines/` | No hace falta renombrar; sí crear `runbooks/` |

## Rúbrica del proyecto integrador: cómo vamos

| Criterio (peso) | Cobertura estimada | Por qué |
|---|---|---|
| Arquitectura, requisitos y decisiones (10 %) | Alta | Constitución, specs, requerimientos. Falta el registro de decisiones |
| Kubernetes, GitOps e IaC (20 %) | Alta | k3s, Kustomize, Argo CD, OpenTofu, quotas, PSA y NetworkPolicy |
| DevSecOps y cadena de suministro (15 %) | Alta | Gitleaks, Trivy, Syft, Cosign, bloqueo con motivo visible. Falta pruebas en el pipeline |
| Observabilidad, SLI/SLO y operación (10 %) | Media | Falta tablero en Grafana y runbook |
| MLOps/LLMOps y reproducibilidad (15 %) | Media | Compuerta de ML, evaluación y trazabilidad; falta MLflow |
| IA local y multimodal (15 %) | Media-baja | Asistente sólido; multimodal sin construir |
| Documentación, privacidad, sostenibilidad y sustentación (15 %) | Media | Documentación fuerte; falta ficha de modelos, análisis de privacidad y ensayo |

Es una estimación del equipo de desarrollo, no una calificación: la rúbrica la aplica el jurado.

## Brechas, en orden de prioridad

Quedan unos 17 días hasta la sustentación del 30 nov. Ordenadas por lo que más pesa y lo que menos cuesta:

| # | Brecha | Entregable | Esfuerzo | Spec o tarea |
|---|---|---|---|---|
| 1 | Construir la infografía con ComfyUI (la modalidad multimodal) | 12 | Alto | Spec 014 |
| 2 | Instalar MLflow y registrar la compuerta y el prompt | 10 | Bajo | 012 · T08 |
| 3 | Escribir `runbooks/`: caída del sitio, rollback, respaldo y restauración de PostgreSQL, reinicio del clúster | 14 | Medio | Nueva tarea |
| 4 | Ficha por modelo (Qwen2.5 3B/7B, modelo de imagen, clasificador) y análisis de privacidad y riesgos de IA | 13 | Bajo | Nueva tarea |
| 5 | Provisionar al menos un tablero en Grafana (disponibilidad frente al SLO) | 9 | Bajo | Nueva tarea en spec 008/010 |
| 6 | Agregar pruebas y lint a la puerta, incluida la imagen del Hub | 5 | Medio | Nueva tarea en spec 006 |
| 7 | Registro de decisiones de arquitectura (ADR) con las ya tomadas: Kyverno descartado, Kustomize sin Helm, k3s, Naive Bayes, ayuda completa | 1 | Bajo | Nueva tarea |
| 8 | Informe ejecutivo, reportes y ensayo de la demo con script de reinicio | 15 | Alto | Specs 013 y 015 |
| 9 | Aclarar RAG: decidir si se implementa con embeddings o se documenta como «contexto completo» | 11 | Medio | Spec 012 |
| 10 | README: cómo reproducir, backlog en `tasks.md`, enlace a este documento | 2 | Bajo | Nueva tarea |

Las tareas nuevas deben proponerse primero en el `tasks.md` de su spec, como pide `CLAUDE.md`, antes de implementarlas.

# Cumplimiento técnico (sin documentos) frente al diplomado CloudForge AI 5.0

> Se compara lo que **funciona y se puede ejecutar** con lo que pide el [documento del diplomado](diplomado-cloudforge-ai-5.0.md): los 15 entregables del módulo 7 (solo la parte técnica) y los módulos 1 a 6.
> Revisado el **16 nov 2026**, con el clúster y el Hub encendidos y recién desplegados (`hub-api` v1.17, `hub-web` v1.12). Sustituye en lo técnico a [cumplimiento-diplomado.md](cumplimiento-diplomado.md) (13 nov), que quedó vieja: MLflow, el RAG, la voz, los runbooks, Grafana, las trazas y la sincronía GitOps ya existen.
> Estados: **Hecho** · **Parcial** (existe pero no cubre todo lo que pide) · **Falta**. Lo que no se comprobó en vivo hoy lo dice la columna «Evidencia».
> No es una calificación: la rúbrica la aplica el jurado.

## Resumen

| | |
|---|---|
| Entregables técnicos (3 a 12) | **10 de 10 hechos**, con las salvedades de la tabla |
| Módulos 1 a 5 | Cubiertos con lo que el diplomado nombra o con un equivalente propio |
| Módulo 6 (IA multimodal) | **El mayor riesgo:** se eligió audio (voz) y el documento nombra imagen, video y 3D. El entregable 12 pide *una* modalidad, pero el módulo 6 vale 15 % y su contenido habla de ComfyUI y Stability Matrix |
| Pruebas | 1.128 pruebas del backend pasan (CI en GitHub con 5 verificaciones por cambio); pruebas propias de red, GitOps, IaC, seguridad e IA; 0 errores 5xx en un recorrido de punta a punta |

## Entregables técnicos del módulo 7

| # | Entregable | Estado | Evidencia (todo ejecutable) | Salvedad |
|---|---|---|---|---|
| 3 | App contenedorizada con pruebas | **Hecho** | Imágenes multi-stage sin root y con `HEALTHCHECK`; `docker compose up`; 1.128 pruebas; sitios de clientes en `apps/` | — |
| 4 | Manifests Kubernetes / Helm / Kustomize | **Hecho** | Kustomize (`gitops/clients/_base`, overlays, `gitops/hub`) **y** chart de Helm `sitio-cliente` con una prueba que exige que den lo mismo (`helm-vs-kustomize.sh`) | Helm solo para los sitios de clientes |
| 5 | Pipeline CI/CD con calidad y seguridad | **Hecho** | `pipelines/puerta.yaml` en Gitea Actions (Gitleaks → pruebas del sitio y build → Trivy → Syft → Cosign firma → verificación) y CI de GitHub (lint, build, pruebas, observabilidad, seguridad de la imagen). El runner corre endurecido (sin capacidades de Linux) | La puerta de Gitea no prueba la imagen del Hub; esa va en el CI de GitHub |
| 6 | SBOM, escaneo y firma/verificación | **Hecho** | SBOM (Syft), Trivy de imagen, configuración y dependencias, Cosign con procedencia; el Hub guarda cada control y su evidencia descargable; una versión sin firma o con secreto no se puede aprobar | La firma se verifica en el pipeline, no dentro del clúster (límite documentado) |
| 7 | GitOps con Argo CD | **Hecho** | 9 Applications `Synced/Healthy` (4 clientes, Hub, monitoreo, MLflow, Backstage, respaldos), ApplicationSet para clientes nuevos, AppProject confinado, `selfHeal`, regla de Gitea que limita lo que escribe `hub-bot` | Gitea y Argo CD se aplican a mano una vez (excepción de arranque documentada) |
| 8 | IaC | **Hecho** | OpenTofu (módulo `client-env`, estado remoto con bloqueo, prueba de drift); probado también con Terraform | `crear-cliente.sh` y `tofu plan` contra el clúster real **no se corrieron hoy** (piden un token de administrador de Gitea) |
| 9 | Dashboard con SLI/SLO | **Hecho** | Tablero del Hub (disponibilidad del mes frente al SLO del plan, con presupuesto de error) y dos tableros de Grafana (servicio de sitios; RED y USE) | — |
| 10 | Registro de experimentos / modelos | **Hecho** | MLflow en el clúster con el modelo `compuerta-asistente` y el alias `production`; corridas, evaluación y comprobación de integridad del modelo (`verificar_modelos.py`) | MLflow del clúster sin autenticación (red local; entrada cerrada por NetworkPolicy) |
| 11 | Servicio de IA local con RAG | **Hecho** | Ollama (Qwen2.5 7B) + RAG propio con `nomic-embed-text` e índice en PostgreSQL, activo en el clúster (`ASSISTANT_CONTEXT_MODE=rag`); compuerta Naive Bayes; evaluación con preguntas ciegas; pruebas de inyección de instrucciones y documentos maliciosos; en vivo respondió con la IA real | No se usa AnythingLLM ni Open WebUI (equivalente propio, decisión D1) |
| 12 | Workflow multimodal adicional | **Hecho** (audio) | Servicio de voz en el clúster (faster-whisper `small` + Piper, CPU): dictar, corregir lo entendido y escuchar la respuesta; evaluación de error de palabras; prueba en navegador real | Imagen, video y 3D no existen. No se probó el micrófono real bajo la nueva política de seguridad del navegador |

Los entregables 1, 2, 13, 14 y 15 son documentales y quedan fuera de este informe (el 14, los runbooks, existe con 9 procedimientos probados).

## Por módulo

| Módulo (peso) | Lo que el diplomado pide | Lo que hay | Falta o riesgo |
|---|---|---|---|
| **1** Cloud native, Linux, Git, contenedores (10 %) | Dockerfile, Compose, registro, pruebas, falla inducida | Todo, más límites de CPU y memoria, `HEALTHCHECK`, raíz de solo lectura en el clúster, registro de Gitea | Nada técnico |
| **2** Kubernetes, GitOps, Platform Engineering (15 %) | Objetos K8s, probes, límites, Kustomize/Helm, Argo CD con drift, Backstage, tutor de IA con matriz de aciertos | k3s, Deployments/StatefulSet/CronJobs/HPA/PDB, NetworkPolicies de entrada y salida en los 5 namespaces, Argo CD con detección y corrección de deriva, Backstage con 14 entidades y plantilla de alta, TechDocs, tutor de IA con su evaluación | Nodo único (sin alta disponibilidad: documentado) |
| **3** DevSecOps (15 %) | Pipeline con Trivy, Syft, Cosign, secretos, políticas | La puerta completa; PSA `restricted`, política de admisión de imágenes, cuotas, segregación de funciones, bitácora de auditoría, Gitea protegido | Verificación de firma dentro del clúster; SLSA como práctica, sin nivel certificado |
| **4** IaC, observabilidad, SRE (10 %) | OpenTofu, OTel, Prometheus/Grafana/Loki, SLO, alertas, runbook, respaldo, AIOps | OpenTofu con drift; Prometheus con alertas por quema de presupuesto y de plataforma; Alertmanager → webhook → incidente; Loki; Tempo con trazas de la API y registros JSON con `trace_id`; 2 tableros; respaldos probados; diagnóstico con IA | Las alertas de plataforma no avisan a nadie (no hay canal externo); trazas solo de la API del Hub, no de los sitios |
| **5** MLOps, LLMOps, IA local (15 %) | MLflow, registro, serving, evaluación RAG, latencia y memoria, seguridad de IA | MLflow con registro y alias, endpoint versionado de la compuerta, evaluación, `medir_modelos.py` (latencia y memoria), fichas de modelos, pruebas de inyección | Kubeflow (opcional) no; el servidor del endpoint de la compuerta no está encendido ahora |
| **6** IA multimodal (15 %) | Texto/código, imagen (ComfyUI), video, 3D; jobs asíncronos | Texto y código con RAG; **audio** en CPU | **Imagen, video y 3D: no.** Es una decisión del equipo (15 nov) por consumo de GPU; conviene confirmarla por escrito con el profesor antes del 30 nov |
| **7** Integrador (20 %) | Repositorio reconstruible, controles, telemetría, IA local, demo | Todo lo anterior, con un clúster que se reconstruye con scripts y sincronía GitOps verificable | Ensayos de la demo (ver [guion](../demo/guion.md)) |

## Brechas técnicas, de mayor a menor peso

| # | Brecha | Peso | Esfuerzo | Decisión |
|---|---|---|---|---|
| 1 | Módulo 6 sin imagen, video ni 3D | Alto (15 % del diplomado) | Alto (GPU) o cero si el profesor acepta audio | **Tuya y del profesor**: preguntarlo ya |
| 2 | Ensayar y cronometrar la demo 3 veces; plan B por punto | Alto (20 %) | Medio | Ver el guion |
| 3 | Probar en vivo lo que quedó sin ver: micrófono real, `crear-cliente.sh`, `tofu plan`, alertas disparando | Medio | Bajo | Una sesión de verificación |
| 4 | 15 hallazgos leves de la auditoría sin hacer (ver T34 a T37) | Bajo | Medio | Se puede dejar |
| 5 | Verificación de la firma dentro del clúster | Bajo (mejora declarada) | Alto | Dejar como mejora |
| 6 | Alertas de plataforma sin canal que avise | Bajo | Medio | Dejar documentado |
| 7 | Sustentación en otra red: la IA corre en el mismo PC, así que no depende de red, pero hay que probar con la red del salón | Medio | Bajo | En el ensayo |

## Lo que se probó hoy

Arranque del entorno completo; 9 aplicaciones de Argo CD sanas; Pod Security `restricted` en los 4 clientes; MLflow con el alias `production`; 14 entidades en Backstage; Ollama con los tres modelos; el servicio de voz en el clúster respondiendo; Grafana con sus tres fuentes de datos y los dos tableros; todo lo verificado ayer (136 comprobaciones de la API, 15 pantallas, portal del cliente, rollback real, asistente con IA real, runner endurecido con un trabajo real).

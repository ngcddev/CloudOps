# Candidatos a ADR (T05 · spec 023)

> Borrador de trabajo del 16 nov 2026 para revisión del equipo **antes** de redactar los ADR (tarea T06).
> Cada fila parte de una huella en el código o en el historial de Git; la bitácora solo se usa como pista del porqué.
> **Verificación:** `Código` = la huella se leyó en el archivo; `Historial` = se leyó el commit; `Porqué` = de dónde sale el motivo.
> **Alcance de la comprobación:** las rutas y líneas de las filas 1–3, 4, 6, 8, 10, 14, 15, 17, 18 y 22 se abrieron hoy; las demás (9, 11–13, 16, 19–21, 23–28) se tomaron del historial y de la bitácora y **se abrirán una por una al redactar cada ADR** (T06), con línea exacta.
> Las filas marcadas **⚠ confirmar** no tienen un porqué reconstruible solo desde código o historial: el equipo debe decirlo.

## A. Decisiones con huella fuerte (se pueden redactar ya)

| # | Decisión | Huella (código / historial) | Alternativa real y dónde consta | Porqué y fuente del porqué | Consecuencia que se ve en el código |
|---|---|---|---|---|---|
| 1 | RAG propio en el Hub, sin AnythingLLM ni Open WebUI | `backend/app/services/assistant.py` (modos de contexto), `kb_documents`/`kb_chunks`; commits `cc1b5a1`, `b356f00` (14 nov) | AnythingLLM, que la constitución nombraba (`constitution/tech-stack.md`) | Un servicio menos en el PC B, todo versionado y probable con fakes (D1, `docs/bitacora.md:620`) | Se aparta de la constitución; hay que mantener el RAG propio |
| 2 | Índice vectorial en tabla con coseno en Python, sin pgvector | `kb_chunks` (migración del RAG), experimento `ai/eval/experimento_hibrido.py` | pgvector, medido y descartado | El experimento con 43 preguntas no dio ganancia confiable (D2, D7, `docs/bitacora.md:545`) | No escala a miles de trozos |
| 3 | Modo de contexto del asistente configurable; por defecto `completo`, RAG por variable | `backend/app/config.py:64` (`assistant_context_mode`), `services/assistant.py:37` | `rag` como defecto | `completo` puntúa 97,5 % contra 92,5 % en el conjunto de ajuste (D3) | Para mostrar el RAG hay que fijar la variable; el clúster usa `rag` |
| 4 | Compuerta de ML (Naive Bayes) antes de despertar al LLM | `ai/classifier/train.py:1,97`; commit `b3a5126`; alias `production` en MLflow | Dejar que el LLM decida solo; modelo más pesado | Ahorra la llamada al LLM con lo ajeno al Hub (`docs/modelos/compuerta-asistente.md`) y es explicable | Otra pieza que versionar, promover y vigilar (`ai/classifier/promover.py`) |
| 5 | Qwen2.5 7B Instruct como modelo del asistente; el 3B queda solo para comparar | `config.py:52` (`ollama_model`), `ai/eval/medir_modelos.py`, fichas `docs/modelos/qwen2.5-*.md` | Llama 3.1 8B (decisión pendiente en `docs/requerimientos.md:95`); Qwen 3B | Medición de latencia y memoria; el 3B se descartó para respuestas que alguien lee; el 3B tiene licencia solo de investigación | Modelo de 7B no se blinda del todo contra inyección (D5) |
| 6 | Voz en CPU con faster-whisper `small` y Piper, en un servicio aparte | `voz/Dockerfile:23`, `voz/descargar_modelos.py:15`; commits `370bac7`, `c90bccb` | Whisper `base` (más rápido, menos preciso); imagen/video en GPU (módulo 6) | `small` acierta 93,7 % de los términos del Hub frente a 84,1 % de `base` (`docs/modelos/faster-whisper-base.md:34`); GPU compartida y limitada | El módulo 6 se cubre con audio, no con imagen, video ni 3D |
| 7 | Piper (GPL) aislado en su propio servicio al que el Hub llama por HTTP | `voz/`, `docs/modelos/README.md:56`; commit `b490789` | Importar Piper en la API | Evitar que la licencia GPL alcance al código del Hub | Un servicio más que operar |
| 8 | El Hub nunca habla con Kubernetes: todo cambio es un commit que Argo CD aplica | `backend/app/integrations/argocd.py:2`, `routers/services.py:110`; rollback = commit que restaura el `newTag` anterior (`services/gitops_publish.py:92-93`) | Que el Hub aplique manifiestos con la API de K8s | Una sola fuente de verdad (Git) y menos privilegios en el Hub (principios 1 y 2 de `constitution/principles.md`) | Todo depende de Gitea y Argo CD |
| 9 | `hub-bot` solo puede escribir lo suyo en `hub-gitops` | `gitops/proteccion_hub_gitops.py`; commit `4b1445e` | Token de administrador | Hallazgo K8-05 de `docs/auditoria-2026-11.md` | Regla de protección que hay que mantener |
| 10 | Argo CD con `selfHeal` y `prune` en los clientes; `prune: false` en Hub, MLflow, Backstage y respaldos | `gitops/platform/argocd/applications/*.yaml` (p. ej. `hub.yaml:24-26`) | `prune: true` en todos | Comentario en el propio manifiesto: un borrado por error no debe llevarse un volumen ni un Secret | Renombrar un recurso del Hub deja el viejo vivo (ocurrió con una NetworkPolicy) |
| 11 | Kustomize como base y chart de Helm equivalente, con una prueba que exige que den lo mismo | `gitops/charts/`, `gitops/clients/_base`, `gitops/pruebas/helm-vs-kustomize.sh`; commits `ded2969`, `a61a53e` | Solo uno de los dos | El diplomado pide ambos; la prueba evita que diverjan | Hay que mantener dos descripciones del mismo sitio |
| 12 | OpenTofu con HCL probado también con Terraform | `infra/tofu/`, `infra/tofu.sh`, `specs/011-infraestructura-como-codigo/plan.md:3` | Terraform solo; decisión que estaba en manos del profesor (`docs/requerimientos.md:94`) | `[⚠ confirmar quién decidió y cuándo]`; el código demuestra la compatibilidad (CA-5 de la spec 011) | Estado local por defecto; remoto con bloqueo en laboratorio (`5edeacd`) |
| 13 | Migraciones de Alembic al arrancar, en lugar de `create_all` | commit `ae0e7c7` (1 oct); `backend/alembic/versions/` (0001–0017) | `create_all` de SQLAlchemy | El esquema evoluciona con datos reales y debe ser reversible; hay pruebas de subida y bajada | Con varias réplicas hubo que evitar migraciones duplicadas (`de9f667`) |
| 14 | `json` → `jsonb` mediante una variante por dialecto | `backend/app/db.py:38` (`JSON_DOC`), migración 0017 | Dejar `json`; tipo único | Consultas indexables en PostgreSQL; SQLite en pruebas | Dos dialectos que probar; `alembic check` solo contra PostgreSQL |
| 15 | Cosign sin transparency log y registro por HTTP | `pipelines/puerta.sh:205,221,228,247` (`--tlog-upload=false`) | Rekor y TLS con CA propia | Laboratorio sin Internet ni certificados (D12, `docs/bitacora.md:550`) | La firma se verifica con la clave pública del Hub y no en el clúster |
| 16 | La CI de GitHub no firma ni publica la imagen del Hub | `.github/workflows/`; D11 | Publicar desde GitHub | GitHub no alcanza el registro del laboratorio | La evidencia queda como artefactos de CI |
| 17 | Reportes con reportlab, no WeasyPrint | `backend/requirements.txt:13`, `services/report_pdf.py:2` | WeasyPrint + Jinja2 (plan 013) | WeasyPrint exige librerías del sistema en la imagen (D8) | La imagen de producción pasó de 308 a 371 MB |
| 18 | Segregación de funciones configurable: quien pide un cambio no lo aprueba | `config.py:15`, `routers/change_requests.py:181` | Un solo rol con todo | Control de DevSecOps del módulo 3 | Con un solo técnico hay que desactivarla en la demo |
| 19 | Denegar por defecto la red (entrada y salida) en `hub`, `monitoring`, `gitea`, `mlops` y clientes | `gitops/hub/networkpolicy.yaml`, `gitops/clients/_base`; commits `0891567`, `4acc8a0`, `90db644`; pruebas `gitops/pruebas/salida-hub.sh` | Red abierta dentro del clúster | Hallazgo K8-02 de `docs/auditoria-2026-11.md` | Cambiar `OLLAMA_URL` exige cambiar un `ipBlock` y su prueba |
| 20 | Pod Security `restricted`, raíz de solo lectura y sin root | `gitops/platform/namespaces.yaml`, `gitops/hub/*`, Dockerfiles multi-stage | Contenedores con permisos por defecto | Principio de contenedores sin root (`CLAUDE.md`, `constitution/conventions.md`) | Hubo que mover el tema inicial a un archivo y montar `emptyDir` |
| 21 | CSP estricta: `script-src 'self'`, sin `unsafe-eval` ni scripts en línea | `frontend/nginx.conf`, `frontend/public/tema-inicial.js`; arreglo en `voz/pruebas/navegador.py` | CSP permisiva | Hallazgo FE-01 de la auditoría | Las pruebas de navegador no pueden usar `wait_for_function` |
| 22 | Alloy como DaemonSet que lee por la API, no del disco del nodo | `observability/alloy/` (comentario de cabecera), commit `6fdd4f8` | Promtail; Deployment único | Escala con nodos y evita montar carpetas del nodo | Más CPU y sondas tolerantes (`54342ad`, `d349ebc`) |
| 23 | Trazas sin texto de preguntas ni respuestas y sin spans de SQL | `backend/app/` (instrumentación), D10 | Spans con contenido | Privacidad; la instrumentación de SQLAlchemy no soporta 2.1 | Menos detalle al depurar |
| 24 | MLflow en el clúster con `MLFLOW_SERVER_ENABLE_JOB_EXECUTION=false` y 1 worker | `gitops/platform/mlops/`; commit `9ef0377` | Configuración por defecto | Usaba ~1,8 GB y 267 procesos (D6) | Se pierden funciones que no se usan |
| 25 | Alertmanager → webhook → incidente con huella única | migración 0008 (`fingerprint`), `routers/` de alertas; commit `767a044` | Notificar por correo o chat | Abrir el incidente solo, sin depender de que el cliente llame (`docs/requerimientos.md:24`) | Las alertas de plataforma no avisan a nadie fuera del Hub |

## B. Decisiones aceptadas como riesgo (se redactan como ADR con estado «Aceptado con riesgo»)

| # | Decisión | Huella | Porqué (fuente) |
|---|---|---|---|
| 26 | Backstage con acceso abierto y solo por la red local | `gitops/platform/backstage/` | D13 |
| 27 | MLflow sin autenticación, entrada cerrada por NetworkPolicy | `gitops/platform/mlops/` | `docs/cumplimiento-tecnico.md` (fila 10) |
| 28 | Nodo único sin alta disponibilidad | `gitops/platform/k3s/` | Un PC de 16 GB; documentado en `constitution/tech-stack.md` |

## C. Para confirmar con el equipo (sin porqué reconstruible solo del repo)

- **⚠** Por qué k3d/k3s y Traefik y no otro Kubernetes ligero (¿kind, minikube?). Huella: `gitops/platform/k3s/`.
- **⚠** Por qué Gitea con Actions en el clúster y no solo GitHub Actions para la puerta de seguridad. Huella: `pipelines/puerta.yaml`, commits `89d3f1a`, `97abc71`.
- **⚠** Por qué Backstage con plantilla de alta (¿alternativa considerada?). Huella: commits `4fd68a8`, `db36d42`.
- **⚠** Por qué PostgreSQL 16 y no otro motor. Huella: `docker-compose.yml`, `gitops/hub/`.
- **⚠** Quién decidió OpenTofu frente a Terraform y cuándo (fila 12).
- **⚠** Nodo GPU compartido (PC B): el repo muestra la restricción (IA local por túnel, voz en CPU) pero la decisión de reparto de hardware está solo en la constitución; ver `memory/plan-produccion-nube.md` para el plan de nube.

## D. Hallazgos que contradicen documentos viejos (se anotan en el informe)

- `docs/requerimientos.md` aún lista RF-21 (infografía, spec 014) como «M»; el punto 10 de la demo pasó a ser voz (spec 021).
- `docs/requerimientos.md` deja «decisiones pendientes» ya resueltas (OpenTofu o Terraform, Qwen o Llama, SD 1.5 o SDXL Turbo).
- `docs/cumplimiento-diplomado.md` (13 nov) está superado por `docs/cumplimiento-tecnico.md`.
- La constitución menciona AnythingLLM; el código usa RAG propio.

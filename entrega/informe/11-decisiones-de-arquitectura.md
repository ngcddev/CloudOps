<!-- Sección 11 · ADR. Cada decisión tiene evidencia en el código o en la corrida (HECHOS.md §11). -->

# Decisiones de arquitectura (ADR)

Cada decisión se registra con su contexto, la decisión, las alternativas que se consideraron, sus consecuencias, su estado y la evidencia que la respalda. La Tabla {T:adr} las resume y el texto que sigue desarrolla cada una.

::: {custom-style="Table Caption"}
**Tabla {T:adr}**\
*Resumen de las decisiones de arquitectura*
:::

| ID | Decisión | Estado |
|---|---|---|
| ADR-01 | k3s en k3d como clúster del laboratorio | Aceptada |
| ADR-02 | GitOps con Argo CD, selfHeal y prune | Aceptada |
| ADR-03 | Gitea con dos repositorios (código y hub-gitops) | Aceptada |
| ADR-04 | OpenTofu con versiones fijadas y en contenedor | Aceptada, con hallazgo abierto |
| ADR-05 | Puerta de seguridad por versión y segregación de funciones | Aceptada |
| ADR-06 | Observabilidad con SLO por plan y burn rate | Aceptada |
| ADR-07 | PostgreSQL con respaldo dentro y fuera del nodo | Aceptada |
| ADR-08 | Modelos locales con Ollama: Qwen2.5 7B en producción | Aceptada |
| ADR-09 | RAG propio con nomic-embed-text, sin pgvector | Aceptada |
| ADR-10 | Compuerta Naive Bayes registrada en MLflow | Aceptada |
| ADR-11 | Voz en CPU como componente multimodal | Aceptada |
| ADR-12 | Nodo GPU compartido (PC B) | Reemplazada por ADR-13 |
| ADR-13 | Un solo equipo con GPU para el clúster y la IA | Aceptada |

## ADR-01 · k3s en k3d como clúster del laboratorio

- **Contexto:** el diplomado exige Kubernetes y el equipo tiene una sola laptop.
- **Decisión:** k3s v1.32.9 de un nodo, dentro de Docker con k3d, con Traefik como Ingress.
- **Alternativas:** minikube y kind (sin Traefik ni un registro integrado tan simple) o un k3s nativo en un segundo equipo (ver ADR-12).
- **Consecuencias:** el clúster se recrea con un script. Si el nodo cambia de IP al reiniciar, hay que seguir un runbook.
- **Evidencia:** `gitops/platform/k3s/crear-cluster.sh`; corrida C03 y C17.

## ADR-02 · GitOps con Argo CD, selfHeal y prune

- **Contexto:** nadie debe desplegar a mano y cada cambio debe poder revertirse.
- **Decisión:** Argo CD 2.13.3 con una Application por cliente y por plataforma (9 en total) y un ApplicationSet para los clientes nuevos. Todas tienen `selfHeal` y `prune`.
- **Alternativas:** Flux, o despliegue por `kubectl apply` desde el CI.
- **Consecuencias:** un cambio manual se revierte en segundos (C20: 2 s). Por la misma razón, las pruebas no pueden apagar un sitio con `kubectl scale`: la falla debe provocarse por Git (hallazgo H-OPS-02).
- **Evidencia:** `gitops/platform/argocd/`; corridas C01, C20 y captura E20.

## ADR-03 · Gitea con dos repositorios

- **Contexto:** el laboratorio no depende de Internet y Argo CD necesita un repositorio que el Hub pueda escribir.
- **Decisión:** el código vive en GitHub y en Gitea vive `hub-gitops`, que vigila Argo CD. Un sincronizador promueve lo que escribe el equipo sin pisar lo que escribe el Hub (versiones y catálogo).
- **Alternativas:** un solo repositorio (el Hub escribiría en el repositorio de código) o GitHub como fuente de Argo CD (depende de Internet).
- **Consecuencias:** hace falta mantener la sincronía, que se verifica con una prueba.
- **Evidencia:** `gitops/sincronizar-hub-gitops.sh`; corridas A09 y C04.

## ADR-04 · OpenTofu con versiones fijadas y en contenedor

- **Contexto:** la infraestructura de cada cliente (namespace, cuota y overlay) debe ser reproducible.
- **Decisión:** OpenTofu 1.13.2 en contenedor, con los proveedores `hashicorp/kubernetes` 3.4.0 y `go-gitea/gitea` 0.8.1. El mismo código corre con Terraform 1.17.0.
- **Alternativas:** Terraform como única opción, o Pulumi.
- **Consecuencias:** la detección de drift funciona (A10). El inventario incluye a los tres clientes reales, que no están en el estado, y un `apply` los reescribió (hallazgo H-IAC-01, C30). Hay que importarlos al estado o probar con un inventario temporal.
- **Evidencia:** `infra/tofu/providers.tf`, `infra/tofu.sh`.

## ADR-05 · Puerta de seguridad y segregación de funciones

- **Contexto:** una versión insegura no debe llegar a producción, y nadie debe aprobar su propio cambio.
- **Decisión:** cada versión pasa por Gitleaks 8.30.1, pruebas y build, Trivy 0.76.1, Syft 1.55.0 y Cosign 3.1.4 (firma y procedencia SLSA), con verificación antes de publicar. El Hub solo permite aprobar versiones con la puerta en «ok», y quien pidió el cambio no puede aprobarlo.
- **Alternativas:** escanear solo en el CI del repositorio, o verificar la firma en el clúster con un controlador de admisión.
- **Consecuencias:** la firma se verifica en la puerta, no en el clúster (riesgo aceptado: nadie despliega a mano).
- **Evidencia:** `pipelines/puerta.yaml`, `pipelines/lib.sh`, `backend/app/routers/change_requests.py`; corridas B06, C22 y C23.

## ADR-06 · Observabilidad con SLO por plan

- **Contexto:** la agencia vende disponibilidad distinta por plan.
- **Decisión:** Blackbox sondea cada sitio cada 5 s. La alerta `SitioCaido` (30 s, se mantiene 2 min) abre el P1 por webhook. El presupuesto de error se vigila con burn rate de varias ventanas (Beyer et al., 2018). Los registros van a Loki (72 h) y las trazas a Tempo (24 h, sin el texto de las preguntas).
- **Alternativas:** chequeos desde el propio Hub, o una sola ventana de alerta.
- **Consecuencias:** las caídas de menos de 30 s no abren incidentes (C28). Tras una caída larga, la alerta de consumo lento del presupuesto puede seguir activa varias horas.
- **Evidencia:** `observability/prometheus/reglas/`; corridas C16, C26 y C28.

## ADR-07 · PostgreSQL con respaldo dentro y fuera del nodo

- **Contexto:** perder la base del Hub o la configuración de la plataforma deja la operación ciega.
- **Decisión:** PostgreSQL 16 con un CronJob de `pg_dump` y rotación. Respaldo de Gitea y Argo CD fuera del nodo.
- **Alternativas:** volúmenes sin respaldo, o un operador de base de datos.
- **Consecuencias:** la restauración se prueba tabla por tabla (23 tablas iguales).
- **Evidencia:** `gitops/hub/backup.yaml`, `gitops/platform/respaldo/`; corridas B05 y C29.

## ADR-08 · Modelos locales con Ollama

- **Contexto:** los datos de los clientes no deben ir a servicios de IA externos.
- **Decisión:** Qwen2.5 7B-Instruct (Q4, Apache 2.0) en el Hub. Qwen2.5 3B (licencia de investigación) solo para comparar. Los digests se verifican contra las fichas.
- **Alternativas:** Llama 3.1 8B, o una API externa (descartada por privacidad).
- **Consecuencias:** 51,2 tokens/s y 4.535 MiB de VRAM. Si Ollama no responde, el Hub avisa y sigue funcionando (F01, paso 7).
- **Evidencia:** `backend/app/config.py`, `docs/modelos/`; corridas D01 y D06.

## ADR-09 · RAG propio sin pgvector

- **Contexto:** el asistente debe responder solo con la ayuda del Hub y detectar lo que no sabe.
- **Decisión:** embeddings `nomic-embed-text` en las tablas `kb_documents` y `kb_chunks`, con similitud coseno en Python (top 4, umbral 0,60). Respaldo a la búsqueda léxica y modo de contexto completo configurable.
- **Alternativas:** pgvector y búsqueda híbrida: el experimento dio 41 frente a 42 de 43 aciertos, pero empeoraba el conjunto ciego. También AnythingLLM, que se reemplazó.
- **Consecuencias:** el modo RAG acierta el 92,5 % y el completo el 95 % (D02). Seis pruebas del backend dependen del modo configurado (hallazgo H-TEST-01).
- **Evidencia:** `backend/app/services/knowledge.py`, `ai/eval/experimento_hibrido.py`.

## ADR-10 · Compuerta Naive Bayes registrada en MLflow

- **Contexto:** no despertar al LLM con preguntas ajenas al Hub.
- **Decisión:** un clasificador propio, exportado a JSON con su suma SHA-256 y registrado en MLflow 3.18.0 con el alias `production`. Su promoción compara con la versión vigente y permite volver atrás.
- **Alternativas:** dejar que el LLM decida, lo que cuesta latencia y es más vulnerable a la inyección.
- **Consecuencias:** un clasificador alterado no se carga (pruebas del backend).
- **Evidencia:** `backend/app/services/assistant_gate.py`, `ai/classifier/`; corridas B04, D01 y captura E40.

## ADR-11 · Voz en CPU como componente multimodal

- **Contexto:** el diplomado pide un flujo multimodal. El plan original era generación de imagen con ComfyUI, que necesitaba unos 5 GB de VRAM.
- **Decisión:** faster-whisper `small` para pasar la voz a texto y Piper es_MX para pasar el texto a voz, en CPU y como servicio aparte. El audio no se guarda.
- **Alternativas:** ComfyUI con Stable Diffusion, descartado por cómputo.
- **Consecuencias:** error de palabras del 5,8 %, 3,3 s por transcripción y 787 MiB de memoria (D11). Piper es GPL-3.0, por eso corre aislado por HTTP.
- **Evidencia:** `voz/`, `gitops/hub/voz.yaml`; corridas D11 y D12.

## ADR-12 · Nodo GPU compartido (PC B)

- **Contexto:** al inicio se previó un segundo equipo con GPU de 6 GB para la IA (Ollama, MLflow y ComfyUI por turnos).
- **Decisión:** se descartó el 15 de noviembre de 2026.
- **Consecuencias:** la reemplaza el ADR-13.
- **Estado:** Reemplazada.

## ADR-13 · Un solo equipo con GPU para el clúster y la IA

- **Contexto:** el PC B no estaba disponible y la demo debe depender de una sola máquina.
- **Decisión:** la laptop del equipo (RTX 4060 de 8 GB) corre Docker Desktop con el clúster k3d y Ollama con los modelos en la GPU. El Hub llama a Ollama en el equipo anfitrión, con una regla de salida explícita (C09).
- **Alternativas:** el PC B; una nube con GPU rentada por horas.
- **Consecuencias:** hay límites de memoria en cada componente y una retención corta de métricas, registros y trazas. Un despliegue en la nube queda pendiente.
- **Evidencia:** corridas C03, C09 y D06.

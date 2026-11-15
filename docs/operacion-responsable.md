# Operación responsable: retención y uso de recursos (spec 019, T06)

La regla del módulo 4: el modelo más pequeño que resuelva el caso, apagar lo que no hace falta, programar lo pesado, reutilizar artefactos, dejar solo los datos
que sirven y **medir**. Las cifras de abajo se midieron en el clúster el 15 nov 2026 con `kubectl top` (metrics-server), `docker stats` y `observability/capacidad.sh`;
las de retención salen de los manifiestos y una prueba (`backend/tests/test_operacion_responsable.py`) falla si este documento deja de coincidir con ellos.

## Retención de datos

| Dato | Retención | Dónde se fija | Por qué |
|---|---|---|---|
| Métricas (Prometheus) | `30d` y `1GB` | `observability/prometheus/deployment.yaml` | El SLO se mide por mes; 1 GB es el tope del volumen de 2 Gi |
| Registros (Loki) | `72h` | `observability/loki/loki.yaml` | Sirve para diagnosticar un incidente reciente; el historial está en la bitácora del Hub |
| Trazas (Tempo) | `24h` | `observability/tempo/tempo.yaml` | Una traza solo se mira durante o justo después de una falla |
| Respaldos de PostgreSQL, Gitea y Argo CD | un volcado diario (03:00, 02:30 y 02:40 UTC) | `gitops/hub/backup.yaml`, `gitops/platform/respaldo/` | Las cargas de respaldo van de madrugada, cuando nadie usa el Hub |

Los datos de clientes (solicitudes, incidentes, mensajes) no se borran solos: son del cliente. Los registros de Loki solo recogen los Pods de `cliente-*` (Alloy descarta el
resto) y se borran a las 72 horas.

## Uso de recursos medido

Nodo del laboratorio: 16 núcleos y 7,8 GiB asignables; en uso, 1 núcleo (6 %) y 3,1 GiB (40 %).

| Carga | Memoria medida | Límite | Comentario |
|---|---|---|---|
| Sitios de clientes (Nginx) | 13 MiB cada uno | 64 MiB | Sitios estáticos: el límite es de sobra |
| Backend del consultorio | 41 MiB | 128 MiB | FastAPI y SQLite de demostración |
| API del Hub | 114 MiB | 384 MiB | Escala a 2 réplicas con la CPU al 70 % |
| PostgreSQL | 43 MiB | — | |
| Backstage | 238 MiB | — | El mayor del Hub |
| MLflow (clúster, namespace mlops) | 380 MiB | — | Hay además un servidor en compose para el desarrollo: 391 MiB con límite de 768 MiB |
| Argo CD (5 Pods) | 284 MiB en total | — | |
| Gitea | 194 MiB | — | |
| Observabilidad (Prometheus, Loki, Tempo, Grafana, Alertmanager, Blackbox, Alloy) | 440 MiB en total | — | |

Hallazgo de la medición: **Alloy** (recolector de registros) estaba al 87 % de su límite de memoria (111 de 128 MiB) y llevaba 14 reinicios con código 137 en 4 horas; el
tablero «RED y USE» lo mostró con la CPU frenada. Se subió el límite a 256 MiB (`observability/alloy/daemonset.yaml`). Sin esta medición se habría visto como «a veces
faltan registros».

## Modelo de IA: el más pequeño que cumpla

| Modelo | Tamaño en disco | Resultado en la evaluación | Uso |
|---|---|---|---|
| Qwen2.5 3B | 1,9 GB | 87,5 % en el conjunto de ajuste (inventó un paso) | Descartado para respuestas de ayuda |
| **Qwen2.5 7B (cuantizado)** | 4,7 GB | 97,5 % en ajuste y 100 % en las 16 preguntas ciegas | El del asistente y del diagnóstico |
| nomic-embed-text | 0,3 GB | — | Solo para el modo RAG (opcional) |

El 3B es más barato pero inventó un paso; para el diagnóstico y las respuestas que alguien va a leer se prefirió el 7B. Para lo que no necesita un LLM no se usa uno: la
compuerta del asistente es un clasificador pequeño (JSON local) y los textos base de los borradores son deterministas. Ollama libera el modelo de la memoria de la GPU a los
2 minutos de inactividad (`OLLAMA_KEEP_ALIVE=2m`) para que ComfyUI comparta la tarjeta.

## Apagar, programar y reutilizar

- **Apagar lo que no se usa:** MLflow, el servidor de la compuerta y el estado remoto de OpenTofu son contenedores aparte y se paran cuando no hay clase o demostración
  (`docker stop`); el clúster y el Hub siguen sin ellos.
- **Programar lo pesado:** los respaldos van de madrugada; la evaluación del asistente (`ai/eval/`) y los escaneos de seguridad completos corren en el CI o a mano, no en cada commit del Hub.
- **Reutilizar artefactos:** la caché de Trivy está en un volumen (`puerta-trivy-cache`) y el kit offline (`infra/kit-offline.sh`) reutiliza imágenes y modelos en vez de bajarlos de nuevo.
- **Revisar el margen:** `bash observability/capacidad.sh` dice cuánto de su cuota usa cada cliente; con más del 90 % reservado el cliente no cabe en una publicación con un Pod extra.

## Drift de la infraestructura

`bash infra/pruebas/drift.sh` demuestra el criterio: un cambio a mano hace que `tofu plan -detailed-exitcode` salga con código 2 y nombre el recurso, y un `apply` lo devuelve a
lo declarado. En el entorno real, un plan con código 2 se revisa antes de aplicar. En el clúster, Argo CD hace lo mismo para Kubernetes con `selfHeal` (`gitops/pruebas/drift.sh`).

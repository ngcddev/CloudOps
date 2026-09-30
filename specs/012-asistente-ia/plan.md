# Plan 012 · Asistente de incidentes con IA local

> Cómo se construye [la spec](spec.md). Todo corre en el **PC B**; el Hub (PC A) lo llama por la red
> local con IP fija.

## Stack (módulo 5)

| Pieza | Herramienta |
|---|---|
| LLM | Ollama con Qwen2.5 7B-Instruct o Llama 3.1 8B (Q4, ≈ 5 GB VRAM); respaldo Qwen2.5 3B. Decisión antes del 3 nov |
| RAG | AnythingLLM con `nomic-embed-text` (vía Ollama): glosario, runbooks, incidentes pasados |
| Evaluación | MLflow (Docker Compose en PC B): versiones de prompt, modelo y puntajes |

Ollama con `keep_alive` corto para liberar VRAM a ComfyUI (spec 014).

## Estructura

```
ai/
├── prompts/
│   ├── incident_summary.v1.md
│   └── client_message.v1.md
├── eval/
│   ├── incidents.jsonl        # 10 incidentes de prueba con respuesta esperada
│   ├── forbidden_terms.txt    # del glosario
│   └── run_eval.py            # corre cada prompt × modelo y registra en MLflow
└── anythingllm/               # documentos del espacio de trabajo
backend/app/integrations/ollama.py
backend/app/integrations/anythingllm.py
```

## Flujo en el Hub

1. `POST /api/incidents/{id}/ai-drafts` → arma el contexto **solo con datos del Hub** (cliente,
   servicio, horas, eventos, versión, rollback).
2. Llama a AnythingLLM (workspace `incidentes`) o directo a Ollama con el prompt vigente; timeout 60 s.
3. Post-proceso: rechaza el mensaje si contiene términos prohibidos; verifica que las horas del
   texto coinciden con las del incidente.
4. Guarda en `ai_drafts` con estado `borrador_ia`.
5. `POST /api/ai-drafts/{id}/approve` (con texto editado) → `aprobado` + auditoría; `discard` →
   `descartado`.

## Modelo de datos

| Tabla | Campos |
|---|---|
| `ai_drafts` | `id` · `incident_id` FK · `kind` (`resumen` / `mensaje_cliente`) · `status` · `model` · `prompt_version` · `generated_text` · `final_text` · `approved_by_id` · `approved_at` · `latency_ms` · `created_at` |

## Evaluación (MLflow)

Métricas por corrida: exactitud de hechos (horas, versión, acción), términos prohibidos (0), longitud,
latencia. Se registra `prompt_version`, `model`, puntaje; el Hub usa la versión marcada como
"producción" en `ai/prompts/`.

## Datos semilla

Resúmenes ya aprobados para el caso demo, por si la IA falla en la presentación.

## Riesgos

| Riesgo | Respuesta |
|---|---|
| PC B no responde en la sustentación | IP fija, prueba en el salón, textos semilla, escritura manual |
| Alucinación de horas o causas | Contexto cerrado + verificación automática de horas |

## Cómo se verifica

- `run_eval.py` con los 10 incidentes; puntaje registrado en MLflow.
- Demo de [spec.md](spec.md#demo-de-cierre), incluido el caso con el asistente apagado.

# Tareas 012 · Asistente de incidentes con IA local

> Cada tarea: una acción con verbo · se comprueba en minutos · menos de un día · se integra sola.
> Rama por tarea: `feat/012-tNN-slug`. Poner el nombre de quien la toma entre corchetes.
>
> Fechas: módulo 5 del 3 al 12 nov. El asistente tiene dos partes: la **compuerta de preguntas** (T01–T11, ML) y los
> **borradores del incidente** (T12–T17, LLM). T19–T21 reducen el error del asistente de ayuda. La compuerta ya existe en el código; el LLM real espera a Ollama en el PC B.

## Cómo repartirlo

| Carril | Tareas | Necesita el PC B | Puede empezar |
|---|---|---|---|
| Compuerta (MLOps) | T01–T06 | No | Hecho |
| PC B y registro de modelos | T07–T08 | Sí | Ya |
| Interfaz y reentrenamiento | T09–T10 | No | T09 hecha; T10 ya |
| Evaluación de prompts (LLMOps) | T11 | Sí | Hecha con Ollama local |
| Borradores de incidente | T12–T17 | Sí | Cuando cierre T07 |

## Compuerta de preguntas (MLOps)

- [x] T01 · Crear el conjunto etiquetado en `ai/classifier/data/` (141 preguntas de entrenamiento, 24 de prueba que no se usan para entrenar, y `vocabulario_app.txt`) — **Verifica:** cada línea de los `.jsonl` es JSON con `text` y `label` (`en_tema` o `fuera_de_tema`) y ninguna pregunta de prueba está en el entrenamiento.
- [x] T02 · Escribir `ai/classifier/train.py`: entrena Naive Bayes, evalúa, exporta `backend/app/assets/clasificador.json` y registra la corrida en MLflow (o en `runs/` si no está) — **Verifica:** `python ai/classifier/train.py` imprime exactitud, `en_tema_perdidas` y `llm_evitado_pct`, y termina con error si `en_tema_perdidas > 0`. *v1: exactitud 0,958 · 0 preguntas del Hub perdidas · 91,7 % de las ajenas sin LLM (CA-9).*
- [x] T03 · Escribir `backend/app/services/assistant_gate.py` (inferencia en Python puro y guarda de vocabulario) — **Verifica:** «ticket», «Quiero ver mis incidentes» y «¿cómo hago un rollback?» siempre despiertan al LLM (`test_assistant.py`).
- [x] T04 · Crear la tabla `ai_queries` con su modelo y la migración 0010 — **Verifica:** `alembic upgrade head` y `downgrade` funcionan (`test_migrations.py`).
- [x] T05 · Escribir `backend/app/integrations/ollama.py` con timeout de 60 s que nunca lanza y `keep_alive` corto — **Verifica:** con `OLLAMA_URL` vacío o con error HTTP devuelve «no disponible» y el Hub responde 200 (CA-10).
- [x] T06 · Crear `POST /api/assistant/ask`, `POST /api/assistant/{id}/feedback` y `GET /api/assistant/stats`, solo agencia — **Verifica:** `pytest tests/test_assistant.py`: una pregunta ajena no llama al LLM, una del tema sí, el cliente recibe 403 y las estadísticas cuentan el ahorro y las decisiones corregidas (CA-8, CA-11).

## PC B y registro de modelos

- [ ] T07 · Instalar Ollama en el PC B con IP fija, bajar Qwen2.5 7B-Instruct y Llama 3.1 8B, poner `OLLAMA_URL` en el Hub y elegir modelo con las preguntas de evaluación (elegido: Qwen2.5 7B-Instruct; el 3B inventó un paso) — **Verifica:** `POST /api/assistant/ask` con «¿Cómo abro un incidente manual?» responde en menos de 60 s con `answered_by = llm`, y el modelo elegido queda anotado en `plan.md`. [ ]
- [x] T08 · Levantar MLflow con Docker Compose, correr `train.py` con `MLFLOW_TRACKING_URI` y marcar la versión en producción — **Verifica:** la corrida `v1` aparece en el experimento `compuerta-asistente` con sus métricas, los datos y el modelo empaquetado, y la versión registrada `compuerta-asistente` tiene el alias `production` (CA-12). *Hecho: `ai/servidor-mlflow/` (imagen fija, sin root, 1 worker, ≈ 360 MB), `train.py` registra parámetros (huella de los datos, commit), métricas, datos y un modelo `pyfunc` en el Model Registry, `promover.py` baja el alias `production` a `backend/app/assets/`, `importar_corridas.py` sube el historial de evaluación. `cd ai && pytest` (9 pruebas). El servidor corre en el PC de desarrollo; falta moverlo al PC B.* [x]

## Interfaz y reentrenamiento

- [x] T09 · Crear la pantalla `frontend/src/pages/agencia/Assistant.tsx`: caja de pregunta, respuesta, quién respondió (compuerta o LLM), botones «era / no era del Hub» y panel con `stats` — **Verifica:** una pregunta del Hub y una ajena se ven distinto, la opinión se guarda y el panel muestra el % de LLM evitado (CA-8, CA-11). *Hecho: ruta `/agencia/asistente`, entrada «Asistente» en el menú; `tsc` y `vite build` pasan. Falta verla en el navegador con la API real.* [ ]
- [ ] T10 · Escribir `ai/classifier/exportar_opiniones.py`, que pasa las preguntas con opinión de `ai_queries` al conjunto de entrenamiento sin tocar el de prueba, y documentar el ciclo en `ai/README.md` — **Verifica:** tras corregir 3 decisiones en el Hub, el script agrega 3 líneas y `train.py v2` corre sin romper la regla de 0 perdidas. [ ]

## Evaluación de prompts (LLMOps)

- [x] T11 · Escribir `ai/eval/run_eval.py` con preguntas del Hub (respuesta esperada y términos prohibidos) y comparar prompt, modelo y modo de contexto — **Verifica:** una corrida por modelo y conjunto queda en `ai/eval/runs/` (y en MLflow si está instalado); el Hub usa `qwen2.5:7b-instruct` con `asistente.v2.md`. *Hecho: 100 % en el conjunto ciego de 16 preguntas con 7B en modo completo; el 3B se descartó (CA-7, CA-13). Falta registrar las corridas en el MLflow del PC B (T08).* [ ]

## Respuestas fundamentadas (reducir el error)

- [x] T19 · Escribir `backend/app/assets/ayuda_hub.md` con las pantallas, botones, estados, planes y reglas del Hub, verificados contra el código — **Verifica:** `pytest tests/test_assistant.py` (la ayuda cabe en el contexto y sus datos de planes coinciden con `seed/plans.json`) (CA-13, CA-14).
- [x] T20 · Pasar al LLM la ayuda como contexto cerrado con `asistente.v2.md`, decodificación determinista y `context_sections` por consulta (migración 0011) — **Verifica:** `python ai/eval/run_eval.py --archivo ai/eval/preguntas_ayuda_ciegas.jsonl` ≥ 95 % y 0 respuestas inventadas (CA-13).
- [ ] T21 · Mantener la ayuda al día: revisar `ayuda_hub.md` en cada PR que cambie una pantalla, botón o regla, y sumar 5 preguntas nuevas al conjunto ciego por spec — **Verifica:** la evaluación sigue en ≥ 95 % tras cada cambio de pantalla. [ ]

## RAG y registro de modelos (reemplaza a AnythingLLM)

- [x] T22 · Crear las tablas `kb_documents` y `kb_chunks` (índice vectorial como lista de números en JSON) y las columnas `context_mode` y `retrieval_score` de `ai_queries`, con la migración 0012 — **Verifica:** `alembic upgrade head` y `downgrade` funcionan (`test_migrations.py`).
- [x] T23 · Escribir `ollama.embed` (nunca lanza) y `backend/app/services/knowledge.py`: dividir la ayuda por sección, indexar con `nomic-embed-text`, detectar el índice vencido por hash y buscar por similitud coseno — **Verifica:** `pytest tests/test_knowledge.py` (26 pruebas: trozos, coseno, índice vencido, fallo de Ollama sin perder el índice anterior).
- [x] T24 · Agregar el modo `ASSISTANT_CONTEXT_MODE=rag` con respaldo a la recuperación léxica y `POST /api/assistant/reindex` (solo agencia) — **Verifica:** con embeddings caídos el asistente sigue respondiendo con `context_mode = recuperacion`; lo que la ayuda no trata no llama al LLM; el cliente recibe 403.
- [x] T25 · Medir el RAG con embeddings reales: barrido de umbral de similitud y comparación contra `completo` y `recuperacion` (`run_eval.py --contexto rag --barrido`) — **Verifica:** corridas en MLflow; umbral elegido y justificado en `plan.md`.
- [x] T26 · Escribir `ai/eval/preguntas_inyeccion.jsonl` (10 intentos de inyección de prompts) y su puntuación en `run_eval.py` — **Verifica:** el asistente no obedece ni filtra el prompt; resultado por modo en MLflow.
- [ ] T27 · Pasar el RAG a producción: poner `ASSISTANT_CONTEXT_MODE=rag` y `OLLAMA_URL` en `gitops/hub/api.yaml`, publicar la imagen nueva del Hub por la puerta y descargar `nomic-embed-text` en el PC B — **Verifica:** `POST /api/assistant/reindex` indexa y una pregunta responde con `context_mode = rag` en el clúster. *Avance: `gitops/hub/configurar-ia.sh` crea el ConfigMap `hub-ia` (URL de Ollama y modo) que la API lee como variables, y `OTEL_EXPORTER_OTLP_ENDPOINT` ya apunta a Tempo. Falta publicar la imagen nueva (`hub-api` con `target` de producción) y probarlo en el clúster; la IP del PC B no va en el repo.* [ ]
- [ ] T28 · Sumar más documentos al índice (`FUENTES` en `knowledge.py`): glosario, prioridades y los runbooks cuando existan — **Verifica:** una pregunta sobre un documento nuevo recupera su sección y la evaluación ciega no baja. [ ]

- [ ] T29 · Búsqueda híbrida (léxica + vectorial) o más trozos para las preguntas redactadas distinto a su sección — **Verifica:** el conjunto de ajuste sube de 92,5 % sin bajar el ciego (100 %). *Medido (`ai/eval/experimento_hibrido.py`, 14 nov): con K=4 la vectorial, el texto completo de PostgreSQL y la híbrida empatan en 41/43; la híbrida con la búsqueda léxica del Hub sube a 42/43 pero pierde 1 de 12 en el conjunto ciego. No cumple el criterio: no se migra a pgvector ni se cambia la búsqueda (bitácora, D7).* [ ]
- [x] T30 · Prompt `asistente.v3.md` contra la inyección de prompts, vigente en el Hub — **Verifica:** 9 de 10 resistidas (v2: 7–8) sin bajar el conjunto ciego (CA-16). *Hecho: `run_eval.py --prompt` compara versiones sin tocar el Hub.*

## Borradores del incidente

- [x] T12 · Crear la tabla `ai_drafts` con su modelo y migración — **Verifica:** `alembic upgrade head` crea la tabla con los campos del plan. *Hecho: tabla `ai_drafts` (migración 0013) con tipo, estado, fuente `llm`/`plantilla`, modelo, prompt, texto generado y final, verificaciones y aprobación.* [ ]
- [x] T13 · Escribir los prompts `incident_summary.v1.md` y `client_message.v1.md` y la integración con el contexto cerrado del incidente — **Verifica:** el contexto solo incluye datos del Hub (cliente, servicio, horas, eventos, versión, rollback). *Hecho: `borrador_resumen.v1.md` y `borrador_mensaje_cliente.v1.md`; el modelo solo recibe los hechos del incidente, y el mensaje al cliente ni siquiera recibe la causa, las versiones ni el título.* [ ]
- [x] T14 · Crear `POST /api/incidents/{id}/ai-drafts`, `approve` y `discard` con el post-proceso de términos prohibidos y horas — **Verifica:** un mensaje con un término del glosario se rechaza y la aprobación queda en la bitácora (CA-2, CA-3, CA-4). *Hecho: `POST /api/incidents/{id}/ai-drafts`, `GET`, `approve` y `discard` (solo agencia); un mensaje con jerga u horas que no coinciden se rechaza al generar (cae al texto base) y al aprobar (422); la aprobación y el descarte quedan en la bitácora. 35 pruebas en `test_ai_drafts.py`.* [ ]
- [x] T15 · Sembrar resúmenes aprobados para el caso del restaurante — **Verifica:** con Ollama apagado el técnico ve el aviso y puede escribir a mano (CA-5). *Decisión: no se siembran textos «aprobados» (serían una aprobación falsa en la bitácora). Con la IA apagada o si su texto no pasa las verificaciones, el borrador es un texto base determinista con el motivo, para que la persona lo edite y lo apruebe a mano (CA-5).* [ ]
- [x] T16 · Agregar el botón «Generar borradores» al detalle del incidente mitigado — **Verifica:** genera ambos borradores en menos de 60 s y el aprobado aparece en el portal del cliente (CA-1). *Hecho: bloque «Borradores de IA» en el detalle de un incidente mitigado o cerrado (`AiDraftsPanel.tsx`) y el mensaje aprobado en el portal del cliente. Latencia medida: 1,4 s el mensaje y 2,1–2,6 s el resumen. Verificado por API y compilación; falta recorrerlo en el navegador.* [ ]
- [ ] T17 · Revisar con Industrial los textos al cliente contra el glosario — **Verifica:** ningún término prohibido en los 10 incidentes de prueba (CA-3). *Parte automática hecha: 10 incidentes de prueba (`ai/eval/incidentes.jsonl`, `run_eval_borradores.py`), 0 términos del glosario en los mensajes y 0 órdenes escondidas obedecidas. Falta la revisión de Industrial.* [ ]

## Cierre

- [ ] T18 · Demo: borradores del incidente de La Sazón, asistente apagado y asistente de ayuda con una pregunta del Hub y una ajena — **Verifica:** todos los criterios de [spec.md](spec.md#criterios-de-aceptación). [ ]

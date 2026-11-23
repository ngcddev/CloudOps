<!-- Sección 20 · Fuente: docs/modelos/ (fichas, medidas del 15 nov), ai/, MLflow del clúster (consultado el 16 nov), ollama list y ai/verificar_modelos.py (ejecutados el 16 nov), evaluación repetida el 16 nov en un contenedor desechable -->

# MLOps y LLMOps

El proyecto usa modelos locales: ninguna llamada de IA sale del laboratorio. Hay un modelo de lenguaje, Qwen2.5 7B Instruct (Qwen Team, 2024), un modelo de embeddings, nomic-embed-text (Nussbaum et al., 2024), un clasificador propio (la compuerta del asistente) y dos modelos de voz: faster-whisper (SYSTRAN, s. f.), que reimplementa Whisper (Radford et al., 2022), y Piper (Open Home Foundation, s. f.). Cada modelo tiene una ficha en `docs/modelos/` con su origen, licencia, `digest`, uso, datos que recibe, medición, evaluación, límites y riesgos; una prueba exige que la ficha esté completa (`backend/tests/test_fichas_modelos.py`).

## Modelos, versiones, hashes y licencias

::: {custom-style="Table Caption"}
**Tabla {T:modelos}**\
*Modelos en uso, versión, huella, licencia y despliegue*
:::

| Modelo | Versión y huella | Licencia | Uso y despliegue |
|-----------|----------------------|------------|------------------------|
| Qwen2.5 7B Instruct | `qwen2.5:7b-instruct`, 7,6 B, Q4_K_M; digest `845dbda0ea48…` | Apache 2.0 | Asistente, borradores y diagnóstico; Ollama en el anfitrión, llamado por `OLLAMA_URL` |
| Qwen2.5 3B Instruct | `qwen2.5:3b-instruct`, 3,1 B, Q4_K_M; digest `357c53fb659c…` | Qwen Research License (solo investigación) | Solo para comparar; no responde a nadie en el Hub y no se redistribuye |
| nomic-embed-text | 137 M, F16; digest `0a109f422b47…` | Apache 2.0 | Embeddings de la ayuda para el RAG (768 dimensiones); Ollama |
| Compuerta del asistente | Naive Bayes propio, versión 1, alias `production`; SHA-256 `f8baf6b41610…` | La del repositorio (sin código ni pesos de terceros) | Clasificador en Python puro dentro de la API; registrado y promovido en MLflow |
| faster-whisper `small` | `Systran/faster-whisper-small`, int8; revisión `536b0662742c…`; digest `3e305921506d…` | MIT | Voz a texto, en CPU, en el servicio `voz/` |
| faster-whisper `base` | Misma familia, más liviano | MIT | Alternativa (`WHISPER=base`); no es la predeterminada |
| Piper `es_MX-claude-high` | Voz VITS en ONNX, 22.050 Hz; digest `3ef40a71ea63…` | Voz: Apache 2.0. Motor `piper-tts` 1.8.0: GPL-3.0 o posterior | Texto a voz, en CPU; el motor corre en un servicio aparte (ADR-26) |

::: {custom-style="Nota"}
*Nota.* Elaboración propia a partir de `docs/modelos/`. Las licencias se leyeron el 15 de noviembre de 2026 en la tarjeta de cada modelo y, para el motor de Piper, con `pip show` dentro de la imagen. Los digests aparecen abreviados; los completos están en las fichas.
:::

**Integridad.** El 16 de noviembre de 2026, `python ai/verificar_modelos.py` comprobó que el digest de cada modelo cargado en Ollama coincide con el de su ficha (`nomic-embed-text`, `qwen2.5:3b-instruct` y `qwen2.5:7b-instruct`) y que el clasificador de la compuerta coincide con su suma SHA-256. El digest se comprueba al medir o al promover, no en cada arranque; el clasificador, en cambio, se verifica al cargarlo y un clasificador alterado hace que el asistente responda 503 (ADR-22).

## Método de despliegue

Los modelos de lenguaje y de embeddings los sirve Ollama (Ollama, s. f.) en el anfitrión, y el clúster los alcanza por la dirección del anfitrión de Docker con una política de red que solo permite ese destino y ese puerto (ADR-27). La compuerta no necesita servidor: se exporta como un JSON de conteos a `backend/app/assets/clasificador.json` con su suma, y la API lo carga y lo verifica; también puede servirse con `mlflow models serve` (`gate_model_url`). El servicio de voz es un contenedor propio (`voz/`) con los modelos descargados por revisión y suma fijas (`voz/descargar_modelos.py`), sin PyTorch y sin GPU. El servicio de embeddings es el mismo Ollama.

## Registro en MLflow

MLflow (MLflow, s. f.) corre en el clúster (espacio `mlops`, imagen propia `mlflow==3.18.0`, sin root, un solo proceso; ADR-24). El flujo es:

1. `ai/classifier/train.py` entrena la compuerta y registra los parámetros (huella SHA-256 de los datos, commit de Git, tamaños), las métricas, los datos y el modelo en el registro como `compuerta-asistente`.
2. `--promover` pone el alias `production` a la versión elegida; `ai/classifier/promover.py` compara contra la de producción, baja la versión al archivo del Hub y permite volver a la anterior (`--rollback`). La cadena datos, corrida, versión, alias, archivo y `gate_version` queda trazable.
3. `ai/eval/run_eval.py` registra cada evaluación con el digest del modelo de Ollama, la versión del prompt, el modo de contexto, la huella de las preguntas y el commit.

**Estado del 16 de noviembre de 2026 (consultado al servidor del clúster):** un modelo registrado, `compuerta-asistente`, con la versión 1 en estado `READY` y el alias `production`, y dos experimentos (`compuerta-asistente` y `Default`) con una corrida registrada. El historial de evaluaciones de los modelos vive como archivos JSON en `ai/eval/runs/`; seis corridas históricas se importaron al MLflow de desarrollo, pero **no están en el servidor del clúster**: solo la corrida de entrenamiento está allí.

Las capturas del modelo registrado con su alias (E-15) y de las corridas con sus métricas (E-16) se incorporan en el Apéndice A; antes conviene importar las corridas de `ai/eval/runs/` al servidor del clúster con `python ai/importar_corridas.py`, y abrir MLflow exige la entrada en el archivo `hosts`.

## Latencia, memoria y consumo

Las mediciones se hicieron el 15 de noviembre de 2026 con `ai/eval/medir_modelos.py` (tres repeticiones, un prompt fijo de 120 tokens como máximo y temperatura 0) y `ai/eval/evaluar_voz.py` (56 preguntas sintetizadas, en el mejor caso: voz limpia, sin ruido ni acento distinto), en una GPU portátil de 8 GB. La ficha del equipo de 6 GB no se midió.

::: {custom-style="Table Caption"}
**Tabla {T:medidas-modelos}**\
*Latencia y memoria de los modelos*
:::

| Modelo | Arranque en frío | Latencia media | Velocidad | Memoria |
|-----------|-----------|-----------|-----------|--------------|
| Qwen2.5 7B Instruct | 12,6 s | 3,61 s | 33,7 tokens/s | 4.535 MiB (VRAM) |
| Qwen2.5 3B Instruct | 8,0 s | 1,72 s | 69,8 tokens/s | 2.063 MiB (VRAM) |
| nomic-embed-text | 0,12 s | 0,08 s | 101 textos/s | 320 MiB (VRAM) |
| faster-whisper `small` | 2.891 ms (primera petición) | 1.865 ms por 2,6 s de audio (p95 2.181 ms) | 1,4 veces más rápido que el audio | 1.188 MiB (servicio con los dos modelos, CPU) |
| faster-whisper `base` | 964 ms (primera petición) | 747 ms (p95 869 ms) | 3,5 veces más rápido que el audio | 433 MiB (servicio con los dos modelos, CPU) |
| Piper `es_MX-claude-high` | — | 110 ms por pregunta | — | Incluida en la del servicio de voz |

::: {custom-style="Nota"}
*Nota.* Elaboración propia a partir de las fichas de `docs/modelos/`. La compuerta corre en la CPU de la API en milisegundos; su ficha tiene la medición «pendiente de medir». La latencia del 7 B en las evaluaciones del 16 de noviembre fue de 1,0 a 1,8 segundos con el modelo ya cargado y respuestas cortas.
:::

## Evaluación del RAG

La generación aumentada por recuperación (RAG; Lewis et al., 2020) entrega al modelo fragmentos de una base de conocimiento antes de que responda. El asistente se evalúa con dos conjuntos de preguntas: uno de ajuste (40) y uno ciego (16) escrito después de fijar el método, para detectar sobreajuste. Cada pregunta indica la sección de la ayuda que la responde, los términos que debe contener y los que no debe contener. Se miden la recuperación (si la sección correcta llega al modelo) y el acierto de la respuesta.

::: {custom-style="Table Caption"}
**Tabla {T:rag-eval}**\
*Evaluación del asistente por modo de contexto (Qwen2.5 7B)*
:::

| Modo | Conjunto | Medición del 14 nov | Repetición del 16 nov |
|-----------|-----------|-----------|-----------|
| `completo` (toda la ayuda) | Ajuste (40) | 97,5 % | 95,0 % (recuperación 100 %; 2 fallos) |
| `completo` | Ciego (16) | 100 % | 100 % (4 de 4 sin información detectadas) |
| `rag` (umbral 0,60) | Ajuste (40) | 92,5 % | 90,0 % (recuperación 93,5 %) |
| `rag` | Ciego (16) | 100 % | No repetido |

::: {custom-style="Nota"}
*Nota.* Elaboración propia a partir de `docs/bitacora.md:575-612` y de la repetición del 16 de noviembre de 2026 con `ai/eval/run_eval.py` en un contenedor desechable contra Ollama local. Las cifras bajaron 2,5 puntos (un fallo más) en cada modo entre una medición y otra, con el mismo prompt y la misma versión del modelo: es la variación propia de un modelo generativo con 40 preguntas (un fallo equivale a 2,5 puntos), por lo que las dos medidas son compatibles y no se debe leer la diferencia como una regresión.
:::

El modo `rag` responde más rápido (0,8 a 1,2 s frente a 3,2 a 3,6 s en la medición del 14 de noviembre) a costa de acertar un poco menos en el conjunto de ajuste; por eso el valor por defecto es `completo` y el clúster usa `rag` (ADR-21). Los dos fallos de recuperación del modo `rag` el 16 de noviembre fueron preguntas redactadas de forma distinta a la sección que las responde; uno de ellos fue «¿Qué pasa cuando el sitio de un cliente cae?», que debía recuperar «Abrir un incidente».

## Límites del modelo

- Puede inventar pasos o citar evidencia que no trata de lo que afirma; por eso todo texto de IA es un borrador y se verifican horas, citas y términos.
- Contexto de 8.192 tokens: la ayuda completa cabe mientras no pase de 24.000 caracteres (`contexto_completo_cabe`).
- La similitud de embeddings no separa lo respondible de lo no cubierto: casi todo puntúa entre 0,55 y 0,85, por lo que el umbral solo descarta lo claramente ajeno.
- Un modelo de 7 B no se blinda del todo contra la inyección de instrucciones (ver la sección de validación de IA).
- Los conjuntos de evaluación son pequeños: las cifras son una primera medición, no una garantía.
- La voz se evaluó con voz sintetizada limpia; con ruido, acento o jerga el error sube. Falta probarla con una voz humana y un micrófono real.

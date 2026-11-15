# Ficha · nomic-embed-text

| Campo | Valor |
|---|---|
| Nombre en Ollama | `nomic-embed-text` |
| Origen | Nomic AI; publicado en la biblioteca de Ollama |
| Licencia | Apache 2.0 |
| Digest | `0a109f422b47e3a30ba2b10eca18548e944e8a23073ee3f3e947efcf3c45e59f` |
| Parámetros y cuantización | 137 M, F16 |
| Tamaño en disco | 0,3 GB |
| Uso | Embeddings de las secciones de la ayuda para el modo RAG del asistente (opcional; por defecto el modo es `completo`) |
| Dónde corre | Ollama en el PC B |
| Datos que recibe | Textos de la ayuda del Hub y la pregunta de quien consulta |

## Medición

<!-- medicion:nomic-embed-text -->
| Medida | Valor |
|---|---|
| Arranque en frío (carga + primera respuesta) | 0.12 s |
| Latencia media con el modelo cargado | 0.08 s |
| Velocidad | 101.0 textos/s |
| Memoria ocupada (total / en VRAM) | 320 MiB / 320 MiB |

Medido el 2026-11-15 con `ai/eval/medir_modelos.py` (3 repeticiones, prompt fijo de 120 tokens como máximo, `temperature` 0).
<!-- /medicion -->

## Evaluación

| Prueba | Resultado |
|---|---|
| Recuperación (K=4) en 43 preguntas | 41 de 43 aciertos; sube a 42 con búsqueda híbrida pero pierde una del conjunto ciego |

## Límites

La similitud no separa lo respondible de lo no cubierto (casi todo puntúa entre 0,55 y 0,85); por eso el umbral solo descarta lo claramente ajeno y el resto lo resuelve el prompt estricto.

## Riesgos

Una sección de la ayuda con instrucciones escondidas podría recuperarse y llegar al LLM: el prompt la trata como información y hay un caso de prueba con un documento malicioso (spec 020, T05).

# Ficha · Qwen2.5 3B Instruct

| Campo | Valor |
|---|---|
| Nombre en Ollama | `qwen2.5:3b-instruct` |
| Origen | Alibaba Cloud (Qwen); publicado en la biblioteca de Ollama |
| Licencia | Qwen Research License (`qwen-research`; **no es Apache 2.0**), verificada el 15 nov 2026 en https://huggingface.co/Qwen/Qwen2.5-3B-Instruct y en la página de Ollama: solo para comparar; no se redistribuye |
| Digest | `357c53fb659c5076de1d65ccb0b397446227b71a42be9d1603d46168015c9e4b` |
| Parámetros y cuantización | 3,1 B, Q4_K_M |
| Tamaño en disco | 1,9 GB |
| Uso | Comparación en la evaluación del asistente; **no** responde a nadie en el Hub |
| Dónde corre | Ollama en el PC B, solo cuando se evalúa |
| Datos que recibe | Las preguntas del conjunto de evaluación (ficticias) |

## Medición

<!-- medicion:qwen2.5:3b-instruct -->
| Medida | Valor |
|---|---|
| Arranque en frío (carga + primera respuesta) | 8.03 s |
| Latencia media con el modelo cargado | 1.72 s |
| Velocidad | 69.8 tokens/s |
| Tiempo de carga | 6.11 s |
| Memoria ocupada (total / en VRAM) | 2063 MiB / 2063 MiB |

Medido el 2026-11-15 con `ai/eval/medir_modelos.py` (3 repeticiones, prompt fijo de 120 tokens como máximo, `temperature` 0).
<!-- /medicion -->

## Evaluación

| Prueba | Resultado |
|---|---|
| Ayuda del Hub, conjunto de ajuste (40), modo secciones | 87,5 % (inventó un paso) |

## Límites

Más rápido y liviano que el 7B, pero inventó un paso de la ayuda: se descartó para respuestas que alguien va a leer y a seguir.

## Riesgos

Los del 7B, con más alucinación. Por eso no está en producción.

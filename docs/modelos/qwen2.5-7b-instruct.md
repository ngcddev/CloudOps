# Ficha · Qwen2.5 7B Instruct

| Campo | Valor |
|---|---|
| Nombre en Ollama | `qwen2.5:7b-instruct` |
| Origen | Alibaba Cloud (Qwen); publicado en la biblioteca de Ollama |
| Licencia | Apache 2.0 (verificada el 15 nov 2026 en https://huggingface.co/Qwen/Qwen2.5-7B-Instruct y en la página de Ollama del modelo) |
| Digest | `845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e` |
| Parámetros y cuantización | 7,6 B, Q4_K_M |
| Tamaño en disco | 4,7 GB |
| Uso | Asistente de ayuda del Hub, borradores del incidente (resumen y mensaje) y diagnóstico con IA |
| Dónde corre | Ollama en el equipo anfitrión (laptop con GPU); la API lo llama por `OLLAMA_URL` |
| Datos que recibe | Preguntas del equipo, la ayuda del Hub y los hechos de un incidente; nada de clientes sale del laboratorio |

## Medición

Se rellena con `python ai/eval/medir_modelos.py` (ver [T02](../../specs/020-cierre-modulo-5/tasks.md)).

<!-- medicion:qwen2.5:7b-instruct -->
| Medida | Valor |
|---|---|
| Arranque en frío (carga + primera respuesta) | 12.58 s |
| Latencia media con el modelo cargado | 3.61 s |
| Velocidad | 33.7 tokens/s |
| Tiempo de carga | 8.53 s |
| Memoria ocupada (total / en VRAM) | 4535 MiB / 4535 MiB |

Medido el 2026-11-15 con `ai/eval/medir_modelos.py` (3 repeticiones, prompt fijo de 120 tokens como máximo, `temperature` 0).
<!-- /medicion -->

## Evaluación

| Prueba | Resultado |
|---|---|
| Ayuda del Hub, conjunto de ajuste (40), modo completo | 97,5 % |
| Ayuda del Hub, conjunto ciego (16), modo completo | 100 % |
| Inyección de prompts (10 casos), prompt v3 | resiste 9 de 10 |
| Borradores de incidente (10), prompt v1 | 100 % aceptado por las verificaciones |

## Límites

- Puede inventar pasos o citar evidencia que no trata de lo que afirma; por eso todo texto es un borrador y se verifican horas, citas y términos.
- Tamaño de contexto de 8192 tokens; la ayuda completa cabe mientras no pase de 24.000 caracteres.
- Español bueno pero no perfecto; no sustituye la lectura de una persona.

## Riesgos

Alucinación, inyección de prompts y filtración del prompt del sistema (ver el [análisis](README.md)). No se usa para decisiones sobre personas.

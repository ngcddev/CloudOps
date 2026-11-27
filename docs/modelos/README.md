# Modelos de IA en uso y análisis de privacidad y riesgos (spec 020, T01)

Todo modelo que corre en el Hub tiene su ficha. Una prueba (`backend/tests/test_fichas_modelos.py`) falla si un modelo de la configuración se queda sin ficha o la ficha
no trae todos los campos. Las cifras de latencia y memoria las mide `ai/eval/medir_modelos.py`.

| Modelo | Ficha | Para qué se usa | Dónde corre |
|---|---|---|---|
| Qwen2.5 7B Instruct (Q4_K_M) | [qwen2.5-7b-instruct.md](qwen2.5-7b-instruct.md) | Asistente de ayuda, borradores de incidente y diagnóstico | Ollama (equipo anfitrión) |
| Qwen2.5 3B Instruct (Q4_K_M) | [qwen2.5-3b-instruct.md](qwen2.5-3b-instruct.md) | Comparación (se descartó para respuestas que alguien lee) | Ollama (equipo anfitrión) |
| nomic-embed-text | [nomic-embed-text.md](nomic-embed-text.md) | Embeddings del modo RAG (opcional) | Ollama (equipo anfitrión) |
| faster-whisper base (voz a texto) | [faster-whisper-base.md](faster-whisper-base.md) | Pasar la voz de quien opera a texto para el asistente (spec 021) | Servicio de voz, CPU |
| faster-whisper small (voz a texto) | [faster-whisper-small.md](faster-whisper-small.md) | Alternativa más precisa y más pesada, solo si la medición la justifica | Servicio de voz, CPU |
| Piper es_MX «claude» (texto a voz) | [piper-es-mx-claude-high.md](piper-es-mx-claude-high.md) | Leer en voz alta las respuestas del asistente | Servicio de voz, CPU |
| Compuerta del asistente (Naive Bayes) | [compuerta-asistente.md](compuerta-asistente.md) | Decidir si una pregunta trata del Hub antes de despertar al LLM | Dentro de la API del Hub |
| Modelo de imagen (ComfyUI) | — | Pendiente: entra con el módulo 6 y tendrá su ficha entonces | — |

## Análisis de privacidad

| Pregunta | Respuesta |
|---|---|
| ¿Algún dato de clientes sale del laboratorio? | No. Los modelos corren en Ollama local; ninguna llamada va a un servicio de IA externo (principio 2). La única dirección de modelos que conoce la API es `OLLAMA_URL`; si está vacía, no hay IA |
| ¿Qué datos reciben los modelos? | Preguntas del equipo sobre el Hub, la ayuda del Hub, y los hechos de un incidente (cliente, servicio, horas, causa). El mensaje al cliente recibe solo lo que el cliente puede conocer |
| ¿Qué se guarda? | La pregunta, la respuesta, la decisión de la compuerta y la latencia en `ai_queries`; los borradores y su aprobación en `ai_drafts`. Los secretos que alguien pegue en una pregunta se redactan antes de guardarse y de enviarse al modelo (spec 020, T05) |
| ¿Con qué datos se entrenó lo propio? | La compuerta, con preguntas ficticias escritas por el equipo (`ai/classifier/data/`); no hay datos de clientes |
| ¿Cuánto tiempo se conserva? | Los registros de `ai_queries` y `ai_drafts` siguen la vida de la base del Hub (respaldo diario); no se envían a ningún tercero |
| ¿Qué pasa con la voz? | El audio se graba en el navegador, pasa por la API del Hub al servicio de voz (CPU, dentro del laboratorio) y se descarta: no se guarda en ninguna parte. De la voz solo queda, si la persona envía la pregunta, su texto ya sin secretos. Nada va a un servicio de reconocimiento externo (el reconocimiento del navegador envía el audio a terceros y no se usa) |
| ¿Quién ve las respuestas? | El asistente y los borradores son solo de la agencia; al portal del cliente solo llega el mensaje aprobado por una persona |

## Riesgos de IA y cómo se controlan

| Riesgo | Control | Riesgo que queda |
|---|---|---|
| Inventa datos (alucinación) | Prompt con «solo los DATOS»; verificación de horas, versiones y términos; texto base si no pasa; evaluación con preguntas ciegas (`ai/eval/`) | Con conjuntos pequeños (40 y 16 preguntas) la cifra es una primera medición |
| Inyección de prompts | Prompt v3 (resiste 9 de 10 en `preguntas_inyeccion.jsonl`); la evidencia y los datos se tratan como información; el diagnóstico no puede proponer cambios a mano | Queda 1 de 10 (orden mezclada con una pregunta válida); un modelo de 7B no se blinda del todo |
| Filtración de secretos por el prompt | Redacción de secretos antes de guardar y enviar; Gitleaks en el repositorio; sin claves en los prompts (prueba) | Un secreto con un formato que el redactor no conoce |
| Modelo o archivo alterado | Digest de cada modelo de Ollama en su ficha y suma SHA-256 del `clasificador.json` comprobadas por script y prueba | El digest se comprueba al medir o promover, no en cada arranque |
| Deriva (la gente empieza a preguntar otra cosa) | Deriva por ventanas con umbral; reentrenar con las decisiones corregidas | Sin decisiones corregidas no hay señal: depende de que la gente opine |
| Sesgo y calidad desigual | El caso de uso es un asistente de ayuda de un producto en español, sin decisiones sobre personas | No se midió calidad por tipo de usuario |
| La voz se transcribe mal | La transcripción se muestra y se corrige antes de enviarse (salvo que la persona active «enviar sin revisar»); el asistente solo explica, la voz no ejecuta acciones | Con ruido o jerga el error sube; la medición es con voz limpia |
| Una persona aprueba sin leer | Todo texto de IA es un borrador; la aprobación queda en la bitácora; el cliente no ve nada sin ella | Aprobación con prisa antes de la defensa |
| Dependencia de la IA | El flujo completo funciona con la IA apagada (textos base deterministas) | — |

## Licencias

Las licencias se **leyeron el 15 nov 2026** en la tarjeta de cada modelo en Hugging Face y, para los de Ollama, en su página; la de Piper también con `pip show` dentro de la imagen de voz:

| Modelo o motor | Licencia | Fuente |
|---|---|---|
| Qwen2.5 7B Instruct | Apache 2.0 | Hugging Face y Ollama |
| Qwen2.5 3B Instruct | Qwen Research License (`qwen-research`, solo investigación) | Hugging Face y Ollama |
| nomic-embed-text | Apache 2.0 | Hugging Face (`nomic-embed-text-v1.5`) |
| faster-whisper base y small | MIT | Hugging Face |
| Voz Piper es_MX «claude» | Apache 2.0 | Tarjeta de la voz |
| Motor `piper-tts` 1.8.0 | **GPL-3.0-or-later** | `pip show` y el repositorio `OHF-voice/piper1-gpl` |

Lo que implica: el **3B** solo se usa para comparar y no se redistribuye. El motor **Piper es GPL**: corre en un servicio aparte (`voz/`) al que el Hub llama por HTTP, sin importar su código, así que el Hub
no queda cubierto por la GPL; pero si la imagen `hub-voz` se entrega a un tercero hay que acompañarla de su código fuente (el del proyecto es abierto). Antes de redistribuir cualquier modelo
(por ejemplo en el kit offline) hay que releer la licencia de la versión exacta.

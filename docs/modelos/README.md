# Modelos de IA en uso y análisis de privacidad y riesgos (spec 020, T01)

Todo modelo que corre en el Hub tiene su ficha. Una prueba (`backend/tests/test_fichas_modelos.py`) falla si un modelo de la configuración se queda sin ficha o la ficha
no trae todos los campos. Las cifras de latencia y memoria las mide `ai/eval/medir_modelos.py`.

| Modelo | Ficha | Para qué se usa | Dónde corre |
|---|---|---|---|
| Qwen2.5 7B Instruct (Q4_K_M) | [qwen2.5-7b-instruct.md](qwen2.5-7b-instruct.md) | Asistente de ayuda, borradores de incidente y diagnóstico | Ollama, PC B |
| Qwen2.5 3B Instruct (Q4_K_M) | [qwen2.5-3b-instruct.md](qwen2.5-3b-instruct.md) | Comparación (se descartó para respuestas que alguien lee) | Ollama, PC B |
| nomic-embed-text | [nomic-embed-text.md](nomic-embed-text.md) | Embeddings del modo RAG (opcional) | Ollama, PC B |
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
| Una persona aprueba sin leer | Todo texto de IA es un borrador; la aprobación queda en la bitácora; el cliente no ve nada sin ella | Aprobación con prisa antes de la defensa |
| Dependencia de la IA | El flujo completo funciona con la IA apagada (textos base deterministas) | — |

## Licencias

Las licencias se verificaron en la página de cada modelo en Ollama y en Hugging Face. Antes de redistribuir un modelo (por ejemplo en el kit offline) hay que releer la licencia de la
versión exacta. El **3B** de Qwen2.5 usa una licencia de investigación y se usa aquí solo para comparar; el **7B** usa Apache 2.0.

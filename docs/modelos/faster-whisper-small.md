# Ficha · faster-whisper base (voz a texto)

| Campo | Valor |
|---|---|
| Nombre del modelo | `Systran/faster-whisper-small` (Whisper small convertido a CTranslate2) |
| Origen | OpenAI Whisper, convertido por Systran; revisión `536b0662742c02347bc0e980a01041f333bce120` de Hugging Face |
| Licencia | MIT |
| Digest | `3e305921506d8872816023e4c273e75d2419fb89b24da97b4fe7bce14170d671` |
| Archivo | `voz/modelos/whisper-small/model.bin` |
| Parámetros y cuantización | unos 244 M, int8 en CPU |
| Tamaño en disco | 484 MB |
| Uso | Voz a texto del asistente del Hub (spec 021): lo que se dicta se convierte en la pregunta, que la persona revisa antes de enviarla |
| Dónde corre | Servicio de voz (`voz/`), en CPU, dentro de la red del Hub; no se guarda el audio |
| Datos que recibe | Audio de la voz de quien opera (hasta 30 s); el vocabulario del Hub se pasa como pista |

## Medición

<!-- medicion:faster-whisper-small -->
| Medida | Valor |
|---|---|
| Tasa de error de palabras (56 preguntas, voz limpia) | 6.6 % |
| Términos del Hub bien transcritos | 93.7 % |
| Preguntas transcritas sin ningún error | 73.2 % |
| Tiempo de transcripción (media / p95) | 1865 ms / 2181 ms para 2.6 s de audio |
| Velocidad frente al tiempo real | 1.4× más rápido que el audio |
| Memoria del servicio de voz (con los dos modelos cargados) | 1188 MiB |
| Primera petición (carga de modelos incluida) | 2891 ms |

Medido el 2026-11-15 con `ai/eval/evaluar_voz.py` (CPU, voz sintetizada con Piper: es el mejor caso, sin ruido ni acento distinto).
<!-- /medicion -->

## Decisión

Es el modelo por defecto del servicio de voz: con las 56 preguntas del asistente acierta el 93,7 % de los términos del Hub (84,1 % con `base`) y la tasa de error de palabras baja de 9,1 % a 6,6 %. Cuesta más: 1,9 s por transcripción frente a 0,7 s y 1,2 GiB de memoria frente a 0,4 GiB. En una vuelta de la charla domina el LLM, así que se prefirió acertar.

## Evaluación

Ver la medición: tasa de error de palabras sobre las 56 preguntas del asistente sintetizadas con la voz de Piper (voz limpia, sin ruido ni acento: es el mejor caso).

## Límites

- Se equivoca con jerga en español («aprobar» como «probar») y con voces con ruido; por eso la transcripción se muestra y se puede corregir antes de enviarla.
- Una sola transcripción a la vez; audios de hasta 30 s y 2 MB.

## Riesgos

Una transcripción equivocada se convierte en una pregunta equivocada: se mitiga mostrándola. Una persona podría dictar un secreto: la API lo tapa antes de mostrarlo o guardarlo (spec 020). El audio no se guarda. Ver el [análisis](README.md).

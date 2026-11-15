# Ficha · faster-whisper base (voz a texto)

| Campo | Valor |
|---|---|
| Nombre del modelo | `Systran/faster-whisper-base` (Whisper base convertido a CTranslate2) |
| Origen | OpenAI Whisper, convertido por Systran; revisión `ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66` de Hugging Face |
| Licencia | MIT |
| Digest | `d01c3014881c9c6f3133c182f3d2887eb6ca1c789a7538c5c007196857a0a6a9` |
| Archivo | `voz/modelos/whisper-base/model.bin` |
| Parámetros y cuantización | unos 74 M, int8 en CPU |
| Tamaño en disco | 145 MB |
| Uso | Voz a texto del asistente del Hub (spec 021): lo que se dicta se convierte en la pregunta, que la persona revisa antes de enviarla |
| Dónde corre | Servicio de voz (`voz/`), en CPU, dentro de la red del Hub; no se guarda el audio |
| Datos que recibe | Audio de la voz de quien opera (hasta 30 s); el vocabulario del Hub se pasa como pista |

## Medición

<!-- medicion:faster-whisper-base -->
| Medida | Valor |
|---|---|
| Tasa de error de palabras (56 preguntas, voz limpia) | 9.1 % |
| Términos del Hub bien transcritos | 84.1 % |
| Preguntas transcritas sin ningún error | 58.9 % |
| Tiempo de transcripción (media / p95) | 747 ms / 869 ms para 2.6 s de audio |
| Velocidad frente al tiempo real | 3.5× más rápido que el audio |
| Memoria del servicio de voz (con los dos modelos cargados) | 433 MiB |
| Primera petición (carga de modelos incluida) | 964 ms |

Medido el 2026-11-15 con `ai/eval/evaluar_voz.py` (CPU, voz sintetizada con Piper: es el mejor caso, sin ruido ni acento distinto).
<!-- /medicion -->

## Decisión

Alternativa liviana, no la predeterminada: transcribe 2,5 veces más rápido y usa un tercio de la memoria, pero acierta menos términos del Hub (84,1 % frente a 93,7 % de `small`). Se activa con `WHISPER=base`.

## Evaluación

Ver la medición: tasa de error de palabras sobre las 56 preguntas del asistente sintetizadas con la voz de Piper (voz limpia, sin ruido ni acento: es el mejor caso).

## Límites

- Se equivoca con jerga en español («aprobar» como «probar») y con voces con ruido; por eso la transcripción se muestra y se puede corregir antes de enviarla.
- Una sola transcripción a la vez; audios de hasta 30 s y 2 MB.

## Riesgos

Una transcripción equivocada se convierte en una pregunta equivocada: se mitiga mostrándola. Una persona podría dictar un secreto: la API lo tapa antes de mostrarlo o guardarlo (spec 020). El audio no se guarda. Ver el [análisis](README.md).

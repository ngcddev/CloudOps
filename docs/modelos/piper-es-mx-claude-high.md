# Ficha · Piper es_MX «claude» (texto a voz)

| Campo | Valor |
|---|---|
| Nombre del modelo | `es_MX-claude-high` (voz de Piper) |
| Origen | Proyecto Piper (rhasspy/piper-voices en Hugging Face), revisión `6b9cfaacb4fb2e02a9621227e3c1a48bec9710c3`; datos de HirCoir/Piper-TTS-Spanish |
| Licencia | **Voz:** Apache 2.0 (tarjeta de la voz). **Motor `piper-tts` 1.8.0: GPL-3.0-or-later** (verificado el 15 nov 2026 con `pip show` en la imagen y en https://github.com/OHF-voice/piper1-gpl): corre como servicio aparte que el Hub llama por HTTP, sin enlazarse con su código; si la imagen de voz se redistribuye hay que ofrecer su código fuente |
| Digest | `3ef40a71ea63852cd8ab7e6fa7d2ecdcfa67a0b47c9c48e3f10e02ee02083ea0` |
| Archivo | `voz/modelos/piper/voz.onnx` |
| Parámetros y cuantización | modelo VITS en ONNX, 22.050 Hz, una voz |
| Tamaño en disco | 63 MB |
| Uso | Leer en voz alta las respuestas del asistente (spec 021) |
| Dónde corre | Servicio de voz (`voz/`), en CPU |
| Datos que recibe | El texto de la respuesta del asistente, ya sin secretos y sin formato (se quitan viñetas, enlaces y código) |

## Medición

<!-- medicion:piper-es-mx-claude-high -->
| Medida | Valor |
|---|---|
| Tiempo de síntesis por pregunta (media) | 110 ms |
| Memoria del servicio de voz (con los dos modelos cargados) | 1188 MiB |
| Primera petición (carga de modelos incluida) | 2891 ms |

Medido el 2026-11-15 con `ai/eval/evaluar_voz.py` (CPU, voz sintetizada con Piper: es el mejor caso, sin ruido ni acento distinto).
<!-- /medicion -->

## Evaluación

Ver la medición: tiempo de síntesis por frase y memoria del servicio. La calidad de la voz se juzga a oído; el acento es mexicano.

## Límites

- Lee mal las palabras en inglés y las siglas («rollback», «SLA») y los números largos; el texto se limpia antes pero no se adapta la pronunciación.
- Máximo 700 caracteres por lectura; una respuesta más larga se recorta.

## Riesgos

Es una voz sintética: no suplanta a ninguna persona. Una respuesta equivocada del asistente suena igual de segura que una correcta: la respuesta también está escrita en pantalla. Ver el [análisis](README.md).

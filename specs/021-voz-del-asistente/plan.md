# Plan 021 · Voz del asistente

Orden: servicio de voz → integración con el Hub → pantalla → evaluación y fichas → seguridad, documentación y validación.

## Decisiones

1. **Audio y no imagen:** CPU, menos de 1 GB y sin competir por la VRAM con el 7B. La infografía (spec 014) queda como mejora.
2. **Servicio aparte:** un contenedor `voz` (FastAPI) que el Hub llama con `VOZ_URL`; la imagen del Hub no engorda y sin él todo sigue por texto.
3. **Por turnos y por HTTP:** el navegador graba con MediaRecorder (webm/opus), el servicio lo decodifica con PyAV; sin WebSockets.
4. **Pista de vocabulario:** los términos del Hub (`vocabulario_app.txt`) sesgan a Whisper hacia «rollback», «SLA», «Argo CD».
5. **Modelos:** Whisper `small` por defecto (484 MB): en la evaluación acierta el 93,7 % de los términos del Hub y 6,6 % de error de palabras, frente a 84,1 % y 9,1 % de `base` (145 MB); cuesta 1,9 s frente a 0,7 s por transcripción y 1,2 GiB frente a 0,4 GiB. `WHISPER=base` queda como opción liviana. Voz Piper es_MX «claude» alta (63 MB, apache-2.0).
6. **av fijado en 16.1.0:** a partir de la 17 cambió la API que usa faster-whisper 1.2.1 al abrir el audio.

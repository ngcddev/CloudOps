# 021 · Voz del asistente (componente multimodal, módulo 6)

> **Acciona:** Equipo de Sistemas · **Módulo:** 6 · **Depende de:** 012, 019, 020 · **Estado:** En curso

## Qué y por qué

El componente multimodal obligatorio del diplomado se cumple con **audio**: el asistente del Hub recibe voz y responde con voz, para que quien opera pregunte sin dejar
de trabajar ni teclear. Se eligió audio y no imagen porque corre en CPU (sin PyTorch ni turnos de VRAM con el 7B de Ollama), pesa menos de 1 GB y se integra con el
asistente que ya existe. Esta spec **reemplaza** a la infografía de la spec 014 como componente multimodal (014 queda pendiente como mejora, no como entregable).

Es una charla por turnos: pulsar para hablar, ver lo que entendió, esperar la respuesta (con un estado visible) y escucharla. Sin escucha continua, sin interrumpir
y sin acciones por voz: el asistente solo explica (principio 6).

## Criterios de aceptación

- [x] CA-1. Un servicio de voz en CPU (faster-whisper y Piper, sin servicios externos) transcribe audio y sintetiza voz, con modelos fijados por suma SHA-256 y límites de tamaño, duración y texto.
- [x] CA-2. La API del Hub expone transcribir y hablar solo para la agencia; no guarda audio; la transcripción pasa por la redacción de secretos; sin `VOZ_URL` la voz se desactiva y el asistente sigue por texto.
- [x] CA-3. La pantalla del asistente permite pulsar para hablar, corregir la transcripción antes de enviar, ver el estado (escuchando, pensando, hablando) y escuchar la respuesta, con opción de silenciar.
- [x] CA-4. Una evaluación sin micrófono (las 40 preguntas sintetizadas y transcritas) mide la tasa de error de palabras, la latencia por etapa y la memoria, y elige entre los modelos `base` y `small`.
- [x] CA-5. Los dos modelos tienen su ficha y el análisis de riesgos; la documentación dice qué exige el micrófono (HTTPS o `localhost`).
- [ ] CA-6. El servicio de voz y el asistente con voz funcionan en el clúster: imágenes publicadas, Deployment del servicio sin Ingress y con token, Hub con HTTPS para el micrófono, y una prueba en navegador real contra `https://hub.local`.

## Fuera de alcance

- Escucha continua, detección de voz, interrumpir al asistente, voz por WebSocket o WebRTC.
- Acciones por voz (aprobar, hacer rollback…).
- Memoria de la conversación (fase 2, solo si queda tiempo).

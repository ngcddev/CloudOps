# Tareas 021 · Voz del asistente

- [x] T01 · Servicio de voz — **Verifica:** el contenedor transcribe un audio webm y un wav, sintetiza voz, rechaza audio vacío, ilegible o demasiado grande, y corre sin root con el sistema de archivos de solo lectura.
- [x] T02 · Integración con el Hub — **Verifica:** transcribir y hablar solo para la agencia; el texto transcrito se redacta; sin `VOZ_URL` responde 503 y el asistente sigue por texto.
- [x] T03 · Pantalla del asistente — **Verifica:** se graba, se corrige la transcripción, se envía y se escucha la respuesta; el mensaje explica qué hacer si el navegador no da micrófono.
- [x] T04 · Evaluación sin micrófono y fichas — **Verifica:** la tasa de error de palabras, la latencia por etapa y la memoria de `base` y `small` quedan en MLflow y en las fichas.
- [x] T05 · Seguridad, documentación y validación — **Verifica:** pruebas del servicio y del Hub, análisis estático y configuración sin hallazgos, bitácora y cumplimiento al día.

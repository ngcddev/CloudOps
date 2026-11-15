# voz/ · Servicio de voz del asistente (spec 021)

Voz a texto (faster-whisper) y texto a voz (Piper), los dos en CPU, dentro del laboratorio y sin servicios externos (principio 2). Es el componente multimodal del módulo 6: el
asistente del Hub recibe voz y responde con voz, para preguntar sin dejar de operar ni teclear. Es una charla **por turnos**: pulsar para hablar, ver lo que entendió (se puede
corregir), esperar la respuesta y escucharla. La voz no ejecuta acciones: el asistente solo explica.

## Levantarlo

```bash
docker compose --profile voz up -d --build voz web api     # la primera vez baja los modelos (~550 MB) y verifica su SHA-256; la imagen pesa ~2 GB
```

Con el perfil apagado, el asistente sigue por texto y la pantalla no muestra el micrófono. Con `WHISPER=base` usa el modelo liviano (433 MiB y 0,7 s por transcripción,
en vez de 1,2 GiB y 1,9 s, pero acierta menos términos del Hub: 84 % frente a 94 %).

## Cómo funciona

| Pieza | Qué hace |
|---|---|
| `voz/app/main.py` | `POST /stt` (audio → texto, con el vocabulario del Hub como pista), `POST /tts` (texto → WAV) y `GET /health`; límites de 2 MB, 30 s y 700 caracteres, una transcripción a la vez, token opcional (`VOZ_TOKEN`) |
| `voz/descargar_modelos.py` | Descarga los modelos de una revisión fija de Hugging Face y comprueba el SHA-256; lo que no coincide se borra |
| `backend/app/integrations/voz.py` y `routers/assistant.py` | La API del Hub (`/api/assistant/voice/status`, `/transcribe`, `/speak`), solo para la agencia; el audio no se guarda; la transcripción pasa por la redacción de secretos; sin `VOZ_URL` responde 503 |
| `frontend/src/components/VoiceInput.tsx` y la pantalla del asistente | Grabar (MediaRecorder, webm/opus), transcribir, corregir, enviar, leer la respuesta en voz alta y callar |

## Qué exige el micrófono

El navegador solo da micrófono en HTTPS o en `localhost` (o `*.localhost`). La demo local (`http://localhost:5173`) y `https://hub.local` del clúster funcionan; `http://hub.local` no, igual que
`crypto.randomUUID`. Sin micrófono disponible, la pantalla lo dice y se escribe la pregunta.

## Pruebas y medición

```bash
docker compose exec api pytest tests/test_voz_servicio.py tests/test_voz_hub.py                      # sin modelos: límites, token, limpieza y permisos
python ai/eval/evaluar_voz.py --url http://localhost:8100 --contenedor cw-cloudops-voz-1 --actualizar-fichas   # 56 preguntas sintetizadas y transcritas: error de palabras, términos, latencia, memoria
HUB_USUARIO=... HUB_PASSWORD=... bash voz/pruebas/voz-ui.sh                                          # Chromium real con micrófono falso: hablar → transcribir → enviar → escuchar
python ai/verificar_modelos.py                                                                       # los archivos de modelo contra el SHA-256 de su ficha
```

Medido el 15 nov 2026 con voz sintetizada (el mejor caso: sin ruido ni acento distinto):

| | Whisper `base` | Whisper `small` (por defecto) |
|---|---|---|
| Error de palabras (56 preguntas) | 9,1 % | 6,6 % |
| Términos del Hub bien transcritos | 84,1 % | 93,7 % |
| Transcripción (media, audio de 2,6 s) | 0,75 s | 1,9 s |
| Memoria del servicio | 433 MiB | 1,2 GiB |

Una vuelta completa suma la transcripción, la compuerta y el LLM (3,6 s medidos con el 7B en modo completo; unos 10 s con el RAG) y la síntesis (0,1 s por pregunta).

## Fuera de alcance (a propósito)

Escucha continua, detección de voz, interrumpir al asistente, WebSocket o WebRTC, acciones por voz y memoria de la conversación (fase 2).

## En el clúster (T06)

| Pieza | Dónde |
|---|---|
| Servicio | `gitops/hub/voz.yaml`: Deployment `voz` en el namespace `hub`, sin root, sistema de archivos de solo lectura (`/tmp` es un emptyDir), 768 MiB pedidos y 1,5 GiB de tope, sin Ingress: solo la API lo llama (`http://voz.hub.svc:8100`) |
| Token | Secret `hub-voz` (lo crea `gitops/hub/crear-secretos.sh`): `/stt` y `/tts` responden 401 sin él; `/health` queda abierto para las sondas |
| HTTPS | Ingress `hub-https` en `gitops/hub/ingress.yaml`: `https://hub.local` con el certificado autofirmado de Traefik (se acepta una vez); el micrófono lo exige. El HTTP sigue abierto para scripts, runner y Alertmanager |
| Imágenes | `apps/publicar-imagenes.sh hub-api hub-web hub-voz` las publica en el registro de Gitea (`hub-api:v1.12`, `hub-web:v1.9`, `hub-voz:v1.0`) |
| Aplicar | `kubectl apply -k gitops/hub` (el Hub no lo gestiona Argo CD; es el arranque documentado en `gitops/README.md`) |
| Probar | `HUB_WEB=https://hub.local HUB_NOMBRE=hub.local AUDIO_PRACTICA=ruta.wav HUB_USUARIO=... HUB_PASSWORD=... bash voz/pruebas/voz-ui.sh` (la contraseña: `kubectl -n hub get secret hub-auth -o jsonpath='{.data.SEED_USER_PASSWORD}' \| base64 -d`) |

Medido en el clúster el 15 nov 2026: el Pod usa unos 950 MiB con Whisper `small` cargado; la primera transcripción tarda unos 10 s (carga del modelo) y las siguientes unos 2 s.
Para abrir `https://hub.local` en tu navegador hace falta la entrada de `hub.local` en el archivo `hosts` (apunta a 127.0.0.1) y aceptar el certificado.

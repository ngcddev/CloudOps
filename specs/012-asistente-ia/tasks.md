# Tareas 012 · Asistente de incidentes con IA local

> Cada tarea: una acción con verbo · se comprueba en minutos · menos de un día · se integra sola.
> Rama por tarea: `feat/012-tNN-slug`. Poner el nombre de quien la toma entre corchetes.
>
> Fechas: módulo 5 del 3 al 12 nov. El carril de producto (Backend y Frontend) se adelanta desde el 31 oct
> sin Ollama: las pruebas usan un asistente simulado (`tests/fake_ollama.py`), como ya se hizo con Gitea y
> Argo CD. Ollama, AnythingLLM y MLflow entran el 3 nov, cuando el diplomado los cubra (principio 9).

## Cómo repartirlo

| Carril | Tareas | Necesita el PC B | Puede empezar |
|---|---|---|---|
| Backend | T01–T11 | No (`pytest` con el asistente simulado) | Ya: la 008 y la 009 están terminadas |
| Frontend | T12–T14 | No (datos de prueba hasta que la API responda) | Cuando el Backend tenga T05–T09 |
| Integración (módulo 5) | T15–T20 | Sí | 3 nov, con Ollama instalado en el PC B |

Decisiones de esta lista:

1. **El asistente es una pieza intercambiable.** El Hub le pide un texto a un `writer` con un contexto
   cerrado y recibe texto + modelo. En las pruebas es `tests/fake_ollama.py`; en el módulo 5 es
   `integrations/ollama.py`. Sin `OLLAMA_URL` el Hub arranca y el botón avisa que se escriba a mano (CA-5).
2. **El contexto sale solo de datos del Hub** (cliente, servicio, horas, versiones, causa raíz). Nunca
   correos, teléfonos ni nombres de técnicos (CA-6).
3. **Escribir a mano no parte de cero.** Si el asistente no responde, el borrador se prellena con las
   plantillas deterministas (el mensaje de la 009 y un resumen armado con los hechos del incidente). Esa
   es la «semilla» del plan para que la demo no dependa de la IA.
4. **Nada llega al cliente sin `aprobado`.** El portal solo muestra el `final_text` de un mensaje aprobado.

## Backend

- [x] T01 · Crear el modelo `AiDraft` (tabla `ai_drafts`) con la migración `0010` — **Verifica:** `alembic upgrade head` y `alembic downgrade -1` sin errores; los incidentes de la 008 y la 009 siguen leyéndose. *`tests/test_migrations.py` sube a `0010` y baja a `0009` con los incidentes y el rollback intactos. Se agregó `created_by_id` para saber quién escribió un borrador a mano.* [sebastian-debug]
- [x] T02 · Escribir `incident_facts(incident)` en `services/ai_context.py`: cliente, servicio, prioridad, horas en America/Bogota, duración, versiones del rollback y causa raíz — **Verifica:** `pytest`: con el incidente de La Sazón (14:00 → 14:07, v2 → v1) trae esos datos y ninguna clave con correo, teléfono ni técnico (CA-2, CA-6). *Además de las horas de inicio y fin, `times` junta las de tomado, rollback y confirmación: son las únicas que un texto puede citar (T04).* [sebastian-debug]
- [x] T03 · Escribir `forbidden_terms(text)` en `services/ai_checks.py` con la lista prohibida del glosario — **Verifica:** `pytest`: «rollback», «P1», «Pod» o «v2» se detectan sin importar mayúsculas; el mensaje de la 009 sale limpio (CA-3). *Se buscan palabras completas: «Pod» se marca y «Podemos» no. Además de los términos del glosario se marcan las prioridades P1-P4 y las versiones vN.* [sebastian-debug]
- [x] T04 · Escribir `hours_match(text, facts)` en `services/ai_checks.py`: toda hora `HH:MM` del texto debe ser una hora del incidente — **Verifica:** `pytest`: «a las 14:00» pasa; «a las 15:30» se marca como hora inventada (CA-2). *Entiende también la hora de 12 h («2:00 p. m.» = 14:00). `invented_times` dice cuáles horas sobran, para mostrarlas en el aviso.* [sebastian-debug]
- [x] T05 · Escribir `generate_drafts(db, incident, writer)` en `services/ai_drafts.py`: pide resumen y mensaje, aplica T03 y T04 y guarda dos `borrador_ia` con `model`, `prompt_version` y `latency_ms` — **Verifica:** `pytest` con `tests/fake_ollama.py`: quedan dos borradores; un mensaje con jerga o con una hora inventada no se guarda y se informa por qué (CA-2, CA-3, CA-4). *Las horas se revisan en los dos textos; la jerga solo en el mensaje, porque el resumen lo lee la agencia. Si el asistente falla sube `WriterError` y no queda nada en la sesión.* [sebastian-debug]
- [x] T06 · Crear `POST /api/incidents/{id}/ai-drafts` (solo agencia, solo incidentes mitigados o cerrados) con 60 s de espera — **Verifica:** `pytest`: 201 con los dos borradores; abierto → 409; sin asistente o sin respuesta a tiempo → 503 con «Escribe el texto a mano» y el incidente intacto; como cliente → 403 (CA-1, CA-5). *Los 60 s los pone el asistente al llamar al PC B (T17); hasta entonces `get_writer` devuelve None y el botón responde 503 con el aviso.* [sebastian-debug]
- [x] T07 · Crear `GET /api/incidents/{id}/drafts`, con los borradores del incidente y el texto prellenado para escribir a mano — **Verifica:** `pytest`: lista en orden con su estado; `manual_templates` trae el mensaje de la 009 y un resumen con las horas reales (CA-5). *El resumen a mano sale de `manual_summary` (mismos hechos que ve el asistente) y el mensaje es el de la 009; un cerrado agrega la causa raíz.* [sebastian-debug]
- [x] T08 · Crear `POST /api/incidents/{id}/drafts` para guardar un borrador escrito a mano (`model = "manual"`) — **Verifica:** `pytest`: queda `borrador_ia` con `model` «manual»; un mensaje con jerga → 422 con el término (CA-3, CA-5). *Pasa por `check_text`, igual que el del asistente: también rechaza horas que no son del incidente. El resumen a mano sí puede ser técnico.* [sebastian-debug]
- [x] T09 · Crear `POST /api/ai-drafts/{id}/approve` con el texto final editado, y `POST /api/ai-drafts/{id}/discard` — **Verifica:** `pytest`: `aprobado` con `approved_by_id` de la sesión y fila en `audit_logs`; un mensaje con jerga no se aprueba (422); aprobar de nuevo o aprobar un descartado → 409; un segundo mensaje aprobado del mismo incidente descarta el anterior (CA-4). *El actor sale de la sesión (un `approved_by_id` en el cuerpo se ignora) y `generated_text` no se pisa: se guarda lo que propuso el asistente y lo que aprobó el técnico. La bitácora dice si hubo edición.* [sebastian-debug]
- [x] T10 · Agregar `message` al listado de fallas del portal (`GET /api/dashboard/client/{id}/incidents`) con el `final_text` del mensaje aprobado — **Verifica:** `pytest`: con solo un borrador el campo viene nulo; tras aprobar trae el texto final editado; el resumen técnico nunca aparece (CA-4). *Una sola consulta para todas las fallas del mes (sin N+1). Se actualizó `test_dashboard.py`, que fijaba los campos del portal.* [sebastian-debug]
- [ ] T11 · Agregar `OLLAMA_URL`, `OLLAMA_MODEL` y `AI_TIMEOUT_SECONDS` a `config.py`, `.env.example` y `docker-compose.yml`, vacíos por defecto — **Verifica:** la API arranca sin ellos y `pytest` completo en verde (principio 6). [ ]

## Frontend

- [ ] T12 · Agregar a `frontend/src/api.ts` los tipos y llamadas de borradores, con datos de prueba si la API no responde — **Verifica:** `tsc` sin errores. [ ]
- [ ] T13 · Agregar al detalle del incidente el bloque «Borradores»: «Generar borradores», editar, «Aprobar» y «Descartar», y «Escribir a mano» prellenado si el asistente falla o tarda más de 60 s — **Verifica:** con datos de prueba se genera, se edita una palabra y se aprueba; con el asistente simulado caído aparece el aviso y se aprueba un texto escrito a mano (CA-1, CA-4, CA-5). [ ]
- [ ] T14 · Mostrar en el inicio del portal el mensaje aprobado de cada falla del mes — **Verifica:** con datos de prueba la falla con mensaje aprobado lo muestra y la que solo tiene borrador no muestra texto (CA-4). [ ]

## Integración (módulo 5, desde el 3 nov)

- [ ] T15 · Instalar Ollama en el PC B con el modelo elegido (Qwen2.5 7B o Llama 3.1 8B, Q4) y `keep_alive` corto, y anotar IP, modelo y VRAM usada en `ai/README.md` — **Verifica:** `curl http://<pc-b>:11434/api/tags` lista el modelo desde el PC A. [ ]
- [ ] T16 · Escribir `ai/prompts/incident_summary.v1.md` y `ai/prompts/client_message.v1.md` — **Verifica:** el Industrial revisa que el mensaje no tenga jerga (glosario). [ ]
- [ ] T17 · Escribir `integrations/ollama.py` con la misma interfaz que `tests/fake_ollama.py` — **Verifica:** `pytest` contra el simulado y una llamada real desde el Hub al PC B en menos de 60 s (CA-1). [ ]
- [ ] T18 · Crear `ai/eval/incidents.jsonl` (10 incidentes), `forbidden_terms.txt` y `run_eval.py`, que registra cada versión de prompt × modelo en MLflow — **Verifica:** MLflow muestra el puntaje de cada corrida y la versión ganadora queda marcada (CA-7). [ ]
- [ ] T19 · Publicar el Hub con la 012 (migración `0010` y variables `OLLAMA_*`) — **Verifica:** `kubectl rollout status` en verde y `alembic current` en `0010 (head)`. [ ]

## Cierre

- [ ] T20 · Demo: abrir el incidente mitigado de La Sazón, generar los borradores, editar una palabra, aprobar y verlo en el portal; apagar el asistente y escribir el texto a mano — **Verifica:** todos los criterios de [spec.md](spec.md#criterios-de-aceptación). [ ]

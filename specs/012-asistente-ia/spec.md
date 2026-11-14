# 012 · Asistente de incidentes con IA local

> **Acciona:** Sistemas (Backend) · Industrial revisa que los mensajes al cliente no tengan jerga
>
> **Módulo:** 5 · **Requerimientos:** RF-18, RF-19, RF-25, RNF-09 · **Depende de:** 008 · **Estado:** En curso

## Qué y por qué

Un asistente que corre en el laboratorio redacta el resumen técnico del incidente y el mensaje al
cliente, y un humano lo aprueba antes de que salga (principio 6). Ahorra tiempo al técnico sin que
ningún dato de clientes salga del laboratorio (principio 2).

Además, el asistente atiende **preguntas de ayuda sobre el Hub** (cómo abrir un incidente, qué significa P1,
dónde ver el SLA). Para no despertar al modelo grande con cada mensaje, un **clasificador liviano (la compuerta)**
decide primero si la pregunta trata de la aplicación: si no, responde él mismo en milisegundos y el LLM sigue
dormido. Ahorra GPU en un PC B que comparte 6 GB de VRAM con la generación de imágenes.

## Actores

| Actor | Qué hace en esta spec |
|---|---|
| Asistente de IA local | Propone borradores |
| Técnico de la agencia | Revisa, edita, aprueba o descarta |
| Cliente PyME | Recibe solo el mensaje aprobado |
| Compuerta (modelo de ML) | Clasifica cada pregunta como `en_tema` o `fuera_de_tema` antes de llamar al LLM |

## Historias de usuario

- **HU-1.** Como técnico, quiero un borrador del resumen del incidente con causa, acción y tiempos,
  para no escribirlo desde cero.
- **HU-2.** Como técnico, quiero un borrador del mensaje al cliente sin jerga, para comunicar rápido.
- **HU-3.** Como técnico, quiero editar y aprobar cada borrador, porque yo respondo por lo que se envía.
- **HU-4.** Como técnico, quiero escribir el texto a mano si la IA no responde.
- **HU-5.** Como técnico, quiero preguntarle al asistente cómo se usa el Hub y recibir una respuesta breve,
  para no buscar en documentos.
- **HU-6.** Como agencia, quiero que las preguntas ajenas al Hub no gasten el LLM, para que la GPU del PC B
  quede libre para lo que sí importa.
- **HU-7.** Como responsable del modelo, quiero medir cuántas veces se despertó el LLM, cuántas se evitaron y
  cuántas decisiones de la compuerta corrigió la gente, para saber cuándo reentrenarla.

## Criterios de aceptación

- [ ] CA-1. Desde un incidente mitigado, un botón genera ambos borradores en menos de 60 segundos.
- [ ] CA-2. El resumen menciona la causa, la acción y el tiempo **reales** del incidente (sin datos
  inventados).
- [ ] CA-3. El mensaje al cliente no contiene términos de la lista prohibida del glosario.
- [ ] CA-4. Todo borrador queda como `borrador_ia`; **nada** llega al cliente sin pasar a `aprobado`
  por un usuario de agencia, y la aprobación queda en la bitácora.
- [ ] CA-5. Si el asistente no responde en 60 s, el técnico ve un aviso y puede escribir el texto a
  mano; el flujo del incidente no se bloquea.
- [ ] CA-6. Ningún dato de clientes se envía a servicios fuera del laboratorio.
- [ ] CA-7. Las versiones de las instrucciones del asistente se evalúan con 10 incidentes de prueba
  y se elige la mejor con un puntaje registrado.

- [ ] CA-8. Una pregunta del tema despierta al LLM; una pregunta ajena (receta, deportes, geografía) recibe la
  respuesta de la compuerta **sin llamar al LLM**.
- [ ] CA-9. En el conjunto de prueba del clasificador ninguna pregunta de la aplicación queda sin LLM
  (`en_tema_perdidas = 0`) y al menos 90 % de las ajenas se resuelven sin LLM. Si la métrica falla, el modelo
  no se exporta.
- [ ] CA-10. Si el LLM no responde en 60 s, el asistente lo dice y el resto del Hub no se bloquea (la compuerta
  sigue funcionando sin IA).
- [ ] CA-11. Cada pregunta queda registrada con la decisión de la compuerta, la versión del modelo y del prompt,
  la latencia y si el LLM respondió; la persona puede marcar «era / no era del tema» y el Hub muestra el
  porcentaje de decisiones corregidas.
- [ ] CA-12. Cada versión del clasificador y del prompt queda registrada con sus métricas (MLflow); el Hub
  usa la versión marcada como producción. Reentrenar y volver a evaluar se hace con un solo comando.

- [ ] CA-13. El asistente solo afirma lo que está en la ayuda del Hub: en el conjunto de evaluación ninguna respuesta
  inventa pantallas, botones, cifras o pasos, y las preguntas que la ayuda no cubre se responden «No tengo esa información».
- [ ] CA-14. Cada respuesta del LLM queda registrada con las secciones de la ayuda en que se basó, y la ayuda no se desfasa de
  `seed/plans.json` (prueba automática).
- [ ] CA-15. Con `ASSISTANT_CONTEXT_MODE=rag` el LLM recibe solo los trozos de la ayuda más parecidos por significado (embeddings),
  cada respuesta guarda sus fuentes y la similitud del mejor trozo, y si Ollama no da embeddings el asistente sigue respondiendo con la
  búsqueda por palabras. En el conjunto ciego iguala la exactitud del contexto completo.
- [ ] CA-16. En el conjunto de inyección de prompts (10 intentos) el asistente resiste al menos 9: no obedece órdenes escondidas en la
  pregunta ni muestra sus reglas, y el resultado por versión de prompt queda registrado (MLflow).

## Fuera de alcance

- Envío automático por correo o chat.
- Chat libre sobre cualquier tema: el asistente solo responde sobre el uso del Hub.
- Que el cliente PyME use el asistente (solo la agencia).
- Que el asistente ejecute acciones (aprobar, desplegar, hacer rollback): solo informa.

## Demo de cierre

1. Abrir el incidente mitigado de La Sazón y pulsar "Generar borradores".
2. Mostrar el resumen (causa: versión v2; acción: rollback; tiempo real).
3. Editar una palabra del mensaje, aprobar y ver que aparece en el portal del cliente.
4. Apagar el asistente y mostrar que se puede escribir a mano.
5. En el asistente de ayuda, preguntar «¿Cómo abro un incidente manual?» (responde el LLM) y «¿Cuál es la
   capital de Francia?» (responde la compuerta, sin LLM) y mostrar el panel: preguntas, LLM evitado en %,
   latencia y decisiones corregidas.

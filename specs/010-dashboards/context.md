# Contexto de la prueba con personas no técnicas (T19)

> **Tarea:** T19 · Hacer la prueba con 3 personas no técnicas y anotarla en este archivo.
> **Criterio:** CA-5 — al menos 2 de las 3 personas explican correctamente el estado de su sitio.
> **Duración:** 20–30 minutos en total (5–8 minutos por persona).
> **Quién la aplica:** una persona del equipo que **no** sea la que diseñó el portal. Si no hay
> otra disponible, la misma persona puede aplicar y registrar, pero no debe guiar las respuestas.

Este archivo sirve para tres cosas: preparar la sesión, aplicarla siempre igual y dejar la evidencia
que exige la tarea. Los resultados se escriben al final, en la tabla de la sección 6. **No se
inventan resultados:** si la prueba aún no se hizo, la tabla queda vacía y T19 sigue abierta.

## 1. Qué se prueba y qué no

Se prueba si una persona **sin formación técnica** entiende, en el portal del cliente, tres cosas:

1. Si su sitio está disponible **ahora**.
2. Si este mes estuvo disponible **lo acordado** con la agencia.
3. Qué fallas y solicitudes tuvo en el mes.

No se prueba la consola de la agencia, ni la velocidad de la aplicación, ni el diseño visual. Tampoco
se pide a la persona que use el menú completo: basta la pantalla de inicio del portal.

La prueba se puede hacer de dos maneras:

| Modo | Cuándo usarlo | Qué muestra |
|---|---|---|
| **A. Clúster real** (recomendado) | Después de T18, con el sitio de La Sazón y el monitoreo funcionando | Datos reales del mes, incluido el incidente de la caída |
| **B. Datos de prueba** | Sin clúster; sirve para ensayar el guion o si T18 se retrasa | La Sazón con 99,4 % frente a un objetivo de 99,9 %, una falla y tres solicitudes (en octubre de 2026; ver la nota de la sección 2) |

En el modo B la persona ve siempre al cliente de prueba (La Sazón) y no hay que iniciar sesión. En el
modo A se entra con el usuario de La Sazón (`contacto@lasazon.test`) y la contraseña de los usuarios
sembrados. **No se le pide a la persona que inicie sesión:** eso lo prepara quien aplica la prueba.

## 2. Preparación

### Modo A · clúster real

1. Confirmar que T18 terminó y que el portal de La Sazón carga con datos del mes.
2. Abrir el portal en el navegador y dejarlo en la pantalla de inicio (`/portal`), ya con la sesión
   iniciada. Si la sesión se hace después de octubre de 2026, abrir
   `http://hub.local/portal?month=2026-10` para ver los datos sembrados de ese mes; el portal recuerda
   el mes mientras dure la pestaña.
3. Anotar antes de la sesión la respuesta correcta a cada pregunta (sección 5), porque los datos
   cambian con la caída y la recuperación.
4. Tener a la mano el incidente del mes y el número de solicitudes abiertas/cerradas.

### Modo B · datos de prueba

```bash
cd frontend
npm install        # solo la primera vez
npm run dev
```

Abrir `http://localhost:5173/portal` (sin iniciar sesión: la aplicación detecta que no hay API y usa
datos de prueba). En este modo la pantalla muestra:

| Dato | Valor en pantalla |
|---|---|
| Estado actual | «Su sitio está disponible.» |
| Disponibilidad del mes | 99,4 % |
| Objetivo del plan (Premium) | 99,9 % |
| Frase de disponibilidad | «Este mes su sitio estuvo disponible menos de lo acordado; le explicamos qué pasó y qué mejoramos.» |
| Fallas del mes | 1: «El sitio de restaurante no responde» (abierta) |
| Solicitudes del mes | 3 en octubre de 2026: «El menú del domingo no aparece» (En progreso), «No llegan los mensajes del formulario» (Abierta), «Cambio de banner del sitio» (Cerrada). En otro mes: «Este mes no abrió solicitudes.» |

> **Fechas de los datos de prueba.** Las tres solicitudes están fechadas el 5 de octubre de 2026 y el
> portal solo muestra las del mes en curso. Por eso:
>
> - Si la sesión se hace **en octubre de 2026**, la persona ve **3 solicitudes**.
> - Si se hace **en otro mes**, ve **0 solicitudes** y la frase «Este mes no abrió solicitudes»; esa
>   es la respuesta correcta, no un error de la pantalla.
>
> La falla, en cambio, se crea al abrir la pantalla y siempre cae en el mes en curso.

> Limitación conocida del modo B: los datos de prueba son fijos y siempre muestran a La Sazón. Para
> probar los estados «sitio caído» y «sin datos» hay que usar el modo A durante la caída de T18 o
> después de apagar Prometheus. Si no se alcanzan esos estados, se anota en observaciones; CA-5 no
> exige recorrerlos todos.
>
> Además, en el modo B la falla aparece **abierta** mientras la tarjeta de estado dice que el sitio
> está **disponible**: los datos de prueba no se actualizan entre sí. Si la persona nota esa
> contradicción, anotarla en la sección 7; no cuenta como respuesta incorrecta de la pregunta 1. Para
> una medición oficial sin esa limitación, usar el modo A (clúster real).

## 3. Reglas de la sesión

- **Una persona a la vez.** Si las tres están juntas, se copian las respuestas y la prueba pierde valor.
- **No se induce la respuesta.** No se dice «fíjate en el 99,9 %», ni «esa frase significa que…», ni
  se señala con el dedo. Si la persona pregunta «¿y esto qué es?», se responde: «¿tú qué crees que
  significa?».
- **Se prueba la pantalla, no a la persona.** Decirlo al empezar: «No hay respuestas incorrectas; si
  algo no se entiende, el problema es de la pantalla».
- **Se puede pensar en voz alta**, pero no es obligatorio. Se toman notas de lo que dice, no de lo que
  hace con el ratón.
- **Sin datos personales.** Se registra un código (P1, P2, P3), el perfil aproximado (por ejemplo,
  «dueña de un restaurante», «administradora») y la edad solo si la persona quiere. No se guardan
  nombres, correos ni teléfonos.
- **Consentimiento verbal:** «Voy a tomar notas de tus respuestas para mejorar esta pantalla. No
  grabo audio ni video y no escribo tu nombre. ¿Te parece bien?».
- **Se puede abandonar en cualquier momento** sin dar explicaciones.

## 4. Guion para quien aplica la prueba

Leer en voz alta, sin agregar explicaciones:

> «Estamos probando una pantalla nueva donde un cliente puede ver cómo va su sitio web. No es un
> examen y no hay respuestas incorrectas: quiero saber qué entiendes tú al mirarla. Voy a tomas notas
> de lo que me digas, sin tu nombre. ¿Empezamos?»

> «Esta es la pantalla de inicio. Mírala con calma y cuéntame con tus palabras qué te dice sobre tu
> sitio.»

Después de la respuesta espontánea, hacer las preguntas de la sección 5 en orden. No corregir hasta
el final. Si la persona se queda callada más de 10 segundos, repetir la pregunta una vez, sin pistas.

Al terminar:

> «Gracias. ¿Hay alguna palabra o frase que no te haya quedado clara? ¿Cambiarías algo para que se
> entienda mejor?»

## 5. Preguntas y respuestas correctas

Cada pregunta vale **1 punto** si la respuesta es correcta o equivalente con otras palabras. La
pregunta 6 no puntúa: sirve para detectar jerga.

| # | Pregunta (literal) | Respuesta correcta en modo B | Cómo se considera correcta en modo A |
|---|---|---|---|
| 1 | «¿Cómo está tu sitio en este momento?» | «Está disponible» / «funciona» / «está bien ahora» | Coincide con el estado que muestra la pantalla (disponible, con fallas o no disponible) |
| 2 | «¿Este mes tu sitio estuvo disponible lo que se acordó? ¿Cómo lo sabes?» | **No**: 99,4 % es menos que el 99,9 % acordado; o repite la frase «estuvo disponible menos de lo acordado» | Distingue «dentro del objetivo» de «por debajo del objetivo» y menciona el objetivo o la frase de la pantalla |
| 3 | «¿Tuviste fallas este mes? ¿Cuántas? ¿Qué te dice la pantalla de ellas?» | **Sí, una**: «El sitio de restaurante no responde», y ve el estado de la falla | Menciona el número de fallas del mes y al menos un dato de la falla (título, fecha o estado) |
| 4 | «¿Qué solicitudes tienes este mes y en qué estado están?» | **Tres** en octubre de 2026 (una en progreso, una abierta y una cerrada); **ninguna** en otro mes | Menciona el número de solicitudes del mes y al menos un estado |
| 5 | «En una frase, ¿cómo le contarías a un socio cómo va el sitio este mes?» | Combina «ahora funciona» con «este mes estuvo por debajo de lo acordado» o «hubo una falla» | Combina el estado actual con la disponibilidad del mes o las fallas |
| 6 | «¿Hay alguna palabra o frase que no entiendas?» | No puntúa. Se anotan las palabras textuales | Igual |

**Veredicto por persona:** «Entiende» si acierta **las preguntas 1 y 2** y no contradice la 3 (por
ejemplo, no dice «no hubo fallas» cuando la pantalla muestra una). Las preguntas 4 y 5 son refuerzo:
si fallan pero 1 y 2 están bien, se anota como observación, no como fallo de CA-5.

**Veredicto de la prueba:** CA-5 se cumple si **al menos 2 de las 3 personas** quedan en «Entiende».

## 6. Resultados

> Completar después de la sesión. Un renglón por persona. No borrar los encabezados.

**Sesión**

| Campo | Valor |
|---|---|
| Fecha y hora | |
| Modo | A (clúster) / B (datos de prueba) |
| Lugar o videollamada | |
| Aplica la prueba | |
| Duración total | |
| Navegador y dispositivo | |

**Valores que mostraba el portal al empezar** (anotarlos antes de la primera persona; sirven de
respuesta correcta para las preguntas 1–4)

| Dato | Valor |
|---|---|
| Estado actual | |
| Disponibilidad del mes | |
| Objetivo del plan | |
| Fallas del mes | |
| Solicitudes abiertas / cerradas | |

**Participantes**

| Código | Perfil (sin nombre) | P1 estado actual | P2 objetivo | P3 fallas | P4 solicitudes | P5 frase | Palabras confusas (P6) | Veredicto |
|---|---|---|---|---|---|---|---|---|
| P1 | | ☐ Sí ☐ No | ☐ Sí ☐ No | ☐ Sí ☐ No | ☐ Sí ☐ No | ☐ Sí ☐ No | | ☐ Entiende ☐ No entiende |
| P2 | | ☐ Sí ☐ No | ☐ Sí ☐ No | ☐ Sí ☐ No | ☐ Sí ☐ No | ☐ Sí ☐ No | | ☐ Entiende ☐ No entiende |
| P3 | | ☐ Sí ☐ No | ☐ Sí ☐ No | ☐ Sí ☐ No | ☐ Sí ☐ No | ☐ Sí ☐ No | | ☐ Entiende ☐ No entiende |

**Resultado de CA-5**

| Criterio | Resultado |
|---|---|
| Personas que entienden el estado de su sitio | ___ de 3 |
| ¿Se cumple «al menos 2 de 3»? | ☐ Sí ☐ No |
| Fecha en que se registró en `tasks.md` | |

## 7. Observaciones y cambios propuestos

Anotar frases textuales de las personas, no interpretaciones. Si una palabra confunde a más de una
persona, el cambio se propone primero en [`docs/glosario.md`](../../docs/glosario.md) y después en
[`frontend/src/texts/cliente.ts`](../../frontend/src/texts/cliente.ts), como pide la T13.

| # | Observación (frase textual) | Persona | ¿Qué se propone? | ¿Se aplicó? |
|---|---|---|---|---|
| 1 | | | | ☐ Sí ☐ No |
| 2 | | | | ☐ Sí ☐ No |
| 3 | | | | ☐ Sí ☐ No |

## 8. Cierre de la tarea

1. Completar las secciones 6 y 7 con lo observado.
2. Si CA-5 se cumple, marcar T19 en [`tasks.md`](tasks.md) así:
   `- [x] T19 · … [Andres]`
   (o el nombre de quien aplicó la prueba), y dejar este archivo como evidencia.
3. Si no se cumple, **no** marcar T19: anotar qué frase o dato no se entendió, corregir los textos y
   repetir la prueba con otras tres personas o con las mismas después del cambio.
4. Si se cambió un texto, correr de nuevo `npm run build` y `git grep -nEi "P1|MTTR|Prometheus|rollback|deploy"`
   sobre `frontend/src/pages/portal` para confirmar que no volvió la jerga (CA-4).

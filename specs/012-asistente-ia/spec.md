# 012 · Asistente de incidentes con IA local

> **Acciona:** Sistemas (Backend) · Industrial revisa que los mensajes al cliente no tengan jerga
>
> **Módulo:** 5 · **Requerimientos:** RF-18, RF-19, RNF-09 · **Depende de:** 008 · **Estado:** Spec y plan

## Qué y por qué

Un asistente que corre en el laboratorio redacta el resumen técnico del incidente y el mensaje al
cliente, y un humano lo aprueba antes de que salga (principio 6). Ahorra tiempo al técnico sin que
ningún dato de clientes salga del laboratorio (principio 2).

## Actores

| Actor | Qué hace en esta spec |
|---|---|
| Asistente de IA local | Propone borradores |
| Técnico de la agencia | Revisa, edita, aprueba o descarta |
| Cliente PyME | Recibe solo el mensaje aprobado |

## Historias de usuario

- **HU-1.** Como técnico, quiero un borrador del resumen del incidente con causa, acción y tiempos,
  para no escribirlo desde cero.
- **HU-2.** Como técnico, quiero un borrador del mensaje al cliente sin jerga, para comunicar rápido.
- **HU-3.** Como técnico, quiero editar y aprobar cada borrador, porque yo respondo por lo que se envía.
- **HU-4.** Como técnico, quiero escribir el texto a mano si la IA no responde.

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

## Fuera de alcance

- Envío automático por correo o chat.
- Chat libre con el asistente.

## Demo de cierre

1. Abrir el incidente mitigado de La Sazón y pulsar "Generar borradores".
2. Mostrar el resumen (causa: versión v2; acción: rollback; tiempo real).
3. Editar una palabra del mensaje, aprobar y ver que aparece en el portal del cliente.
4. Apagar el asistente y mostrar que se puede escribir a mano.

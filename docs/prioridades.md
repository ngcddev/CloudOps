# Prioridades P1–P4 con ejemplos por cliente

> Cómo decide la agencia qué tan urgente es un caso, y qué significa cada prioridad en el sitio de cada
> cliente. Cierra la T07 de la spec **000** (CA-2). La matriz que usa el Hub está en
> `seed/priority_matrix.json` y los tiempos en `seed/sla_policies.json`; este documento no los cambia,
> los explica con casos.
> *Redactado por el equipo de Sistemas (31 oct 2026), sin revisión de Industrial.*

## Cómo se decide

La prioridad sale de dos preguntas:

- **Impacto:** ¿cuánto daña el problema al negocio del cliente? `alto` (se pierden ventas, reservas o
  citas, o el sitio no abre), `medio` (una función importante funciona mal o lento) o `bajo` (molestia
  menor o cambio de contenido).
- **Urgencia:** ¿qué tan pronto hay que arreglarlo? `alta` (hoy, por una fecha o un evento), `media`
  (en los próximos días) o `baja` (cuando se pueda).

| Impacto \ Urgencia | alta | media | baja |
|---|---|---|---|
| **alto** | P1 | P2 | P3 |
| **medio** | P2 | P3 | P4 |
| **bajo** | P3 | P4 | P4 |

## Qué promete cada prioridad

| Prioridad | Significado | Respuesta | Solución | Reloj |
|---|---|---|---|---|
| P1 | Crítica: el sitio no funciona o se pierden ventas | 15 min | 4 h | 24x7 |
| P2 | Alta: una función importante falla | 1 h | 8 h | Horario del plan |
| P3 | Media: falla menor con alternativa | 4 h | 24 h | Horario del plan |
| P4 | Baja: consulta o mejora | 8 h | 72 h | Horario del plan |

«Horario del plan» es el de cada cliente: Premium 24x7, Estándar lunes a sábado 7:00–20:00 y Básico
lunes a viernes 8:00–18:00. Un P1 siempre corre 24x7, sin importar el plan.

## Ejemplos por cliente

Cada ejemplo indica el impacto y la urgencia con los que se clasifica, y la prioridad que da la matriz.

### Restaurante La Sazón (plan Premium · menú y reservas)

| Prioridad | Caso | Impacto | Urgencia |
|---|---|---|---|
| P1 | El sitio responde error 500 tras publicar una versión: nadie puede ver el menú ni reservar (el caso de la demo). | alto | alta |
| P2 | El botón «Reservar mesa» no funciona en algunos celulares: se pierden reservas, pero el menú sí abre. | alto | media |
| P3 | El precio de un plato aparece desactualizado en el menú. | medio | media |
| P4 | Cambiar la foto de portada o el color de un botón. | bajo | baja |

### Ferretería El Tornillo (plan Estándar · catálogo)

| Prioridad | Caso | Impacto | Urgencia |
|---|---|---|---|
| P1 | El sitio no abre en plena promoción de cemento y varilla: los clientes no ven precios. | alto | alta |
| P2 | El catálogo carga muy lento y la gente se va; el fin de semana es de mucha obra. | medio | alta |
| P3 | El precio de la varilla en el catálogo no coincide con el de la tienda. | medio | media |
| P4 | Agregar la categoría «Pinturas» al catálogo cuando haya tiempo. | medio | baja |

### Consultorio Dental Popayán (plan Básico · formulario de citas)

| Prioridad | Caso | Impacto | Urgencia |
|---|---|---|---|
| P1 | El formulario de citas no envía y el sitio no guarda solicitudes un lunes de atención. | alto | alta |
| P2 | Algunas citas llegan con datos incompletos (sin teléfono): hay que llamar a ciegas. | alto | media |
| P3 | El horario publicado está mal y mañana hay festivo. | bajo | alta |
| P4 | Ajustar el texto de bienvenida de la página. | bajo | baja |

## Cómo se usa

- Quien clasifica en el Hub elige impacto y urgencia; la prioridad la calcula la matriz y arranca el reloj
  de su SLA.
- Un incidente abierto por una alerta (el sitio no responde) entra como **P1** de forma automática.
- Para el cliente, los textos salen del [glosario](glosario.md): «Falla crítica: atención inmediata.» es el P1.

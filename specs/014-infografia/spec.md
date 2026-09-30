# 014 · Infografía mensual

> **Acciona:** Sistemas (Frontend, Backend) · Industrial define el contenido de la infografía
>
> **Módulo:** 6 · **Requerimientos:** RF-21, RF-23 (opcional) · **Depende de:** 010, 013 · **Estado:** Spec y plan

## Qué y por qué

Una pieza visual por cliente que resume su mes: lo que un dueño de PyME mira en diez segundos. Es el
componente multimodal obligatorio del diplomado, generado con IA local.

## Actores

| Actor | Qué hace en esta spec |
|---|---|
| Administrador de la agencia | Genera y aprueba la infografía |
| Cliente PyME | La recibe en su portal |

## Historias de usuario

- **HU-1.** Como administrador, quiero generar la infografía mensual de un cliente con un botón.
- **HU-2.** Como cliente, quiero una imagen clara con los números de mi mes.
- **HU-3.** (Opcional) Como técnico, quiero una sugerencia de la causa de un incidente, para
  diagnosticar más rápido.

## Criterios de aceptación

- [ ] CA-1. Todos los números de la infografía vienen de la base de datos (los mismos del reporte
  ejecutivo).
- [ ] CA-2. La ilustración la genera la IA local en el laboratorio.
- [ ] CA-3. La infografía se genera en **menos de 2 minutos**.
- [ ] CA-4. Pasa por aprobación humana antes de aparecer en el portal del cliente.
- [ ] CA-5. Si la generación de imagen falla, se produce la infografía solo con datos y una
  ilustración por defecto.
- [ ] CA-6. (Opcional, RF-23) Un modelo sugiere la causa probable de un incidente a partir de los
  registros y el último cambio, marcada como sugerencia.

## Fuera de alcance

- Video o animación.
- Edición manual del diseño.

## Demo de cierre

1. Pulsar "Generar infografía" para La Sazón (cronómetro).
2. Mostrar la pieza: disponibilidad, incidentes, cambios y la ilustración del restaurante.
3. Aprobarla y verla en el portal del cliente.

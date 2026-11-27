# Plan · 023 Entrega final: informe consolidador

> Plan aprobado el 16 nov 2026. Detalle completo en el plan de trabajo de la sesión; aquí lo que importa para el repositorio.

## Decisiones de método

- **Fuente en Markdown, Word generado.** Una sección por archivo en `entrega/00-informe/NN-nombre.md`;
  `entrega/construir.sh` genera el `.docx` con pandoc en contenedor y una plantilla de estilos APA 7
  (`entrega/plantilla.docx`). Salida: `Entrega_Final_CloudForge/00_Informe_Final_Proyecto_Integrador_CloudForge.docx`.
- **El código manda sobre los `.md`.** Cada afirmación se comprueba en el código, los manifiestos, las pruebas o el
  historial de Git; la documentación solo orienta. Si se contradicen, gana el código y se anota la diferencia.
- **ADR con huella real.** Un ADR solo entra si hay evidencia de la decisión en el código o en el historial
  (alternativa quitada, interruptor de configuración, excepción documentada, prueba que fija una restricción,
  migración que cambia de rumbo) y se reconstruye el porqué con el commit o la medición. Sin evidencia: `[COMPLETAR]`.
- **Columna de identificadores** en `entrega/trazabilidad.csv`: `RF` · `RNF` · `HU` · `ADR` · `PF` · `E` · `R`.
  De ahí salen la sección 23 y, después, el complementario 02.
- **Marcadores:** `[FIGURA F-nn · …]`, `[EVIDENCIA E-nn · …]`, `[COMPLETAR: …]`; un anexo los reúne.
- **APA 7:** página, encabezados, tablas y figuras con nota, citas autor-fecha y referencias con sangría francesa;
  un script comprueba la correspondencia cita ↔ referencia.

## Estructura

```text
entrega/
├── 00-informe/NN-nombre.md   una sección por archivo (29)
├── plantilla.docx            estilos APA 7
├── trazabilidad.csv          columna vertebral de identificadores
├── construir.sh              Markdown → .docx
└── verificar.py              identificadores, enlaces, marcadores, APA
```

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Documentos del repo desactualizados que contaminen el informe | Comprobar contra el código; anotar diferencias |
| ADR inventados | Exigir evidencia; si falta, marcar para el equipo |
| Cifras que cambian antes de la entrega | Cada cifra con fecha y comando; revisión final |
| pandoc no logra el formato APA | Plantilla propia; si no alcanza, generar con la skill `docx` |

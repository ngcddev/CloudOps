<!-- Sección 24 · Resumen del análisis de riesgos (el completo es el complementario 06). Fuente: docs/modelo-de-amenazas.md, constitution/roadmap.md (riesgos), docs/auditoria-2026-11.md, docs/modelos/README.md y los hallazgos de este informe. Probabilidad e impacto son una estimación a confirmar por el equipo. -->

# Análisis de riesgos resumido

Esta sección resume los riesgos técnicos, de seguridad, de IA y de cronograma del proyecto; el análisis completo, con responsable, privacidad, gestión de secretos, licencias y fichas de modelos, está en el documento complementario `06_Analisis_Riesgos_y_Seguridad.docx`. Los riesgos salen de tres fuentes: el modelo de amenazas del Hub (`docs/modelo-de-amenazas.md`, 13 amenazas y sus controles), los riesgos del cronograma (`constitution/roadmap.md`) y los hallazgos de la auditoría de noviembre de 2026, que encontró 3 hallazgos críticos, 29 medios y 52 leves (`docs/auditoria-2026-11.md`). Los críticos y los medios se corrigieron y se desplegaron; de los leves quedan 15 sin hacer.

**Escala.** La probabilidad y el impacto se califican en alta, media o baja, con criterio del equipo: probabilidad alta es la que se espera durante la sustentación o el uso normal del laboratorio; impacto alto es el que detiene la demostración, pierde datos o expone datos de otro cliente. **Estados:** *Mitigado* (hay un control comprobado), *Aceptado* (se asume con un riesgo conocido) y *Abierto* (falta una acción).

::: {custom-style="Table Caption"}
**Tabla {T:riesgos}**\
*Riesgos principales, probabilidad, impacto, mitigación y estado*
:::

| ID | Tipo | Riesgo | Prob. | Impacto | Mitigación | Estado |
|-----|------|----------------------|-----|-----|-------------------------|--------|
| R-01 | Técnico | Nodo único: la caída del equipo detiene todo (no hay alta disponibilidad) | Media | Alta | Respaldos diarios de PostgreSQL, Gitea y Argo CD; reconstrucción con scripts; runbook de reinicio; simulaciones de falla | Aceptado (ADR-27) |
| R-02 | Técnico | Memoria y GPU justas al compartir clúster e IA en un equipo de 16 GB y 6 a 8 GB de VRAM | Media | Media | Límites de recursos, retención corta, `keep_alive` corto del modelo, modelo más pequeño que cumpla; la medición de 6 GB no se hizo | Mitigado parcialmente |
| R-03 | Técnico | Arranque del clúster en un orden preciso y dirección fija del nodo; entradas del archivo `hosts` ausentes | Media | Alta | `runbooks/reinicio-del-cluster.md`, scripts de la demo, video de respaldo (pendiente) | Abierto |
| R-04 | Técnico | `tofu plan` y `crear-cliente.sh` contra el clúster real sin verificar (piden token de Gitea) | Media | Media | Prueba de deriva ejecutada; tarea T06 de la especificación 015 | Abierto |
| R-05 | Seguridad | Un cliente ve datos de otro cliente | Baja | Alta | Cada ruta filtra por el cliente de la sesión; pruebas de acceso entre clientes (PF-01) | Mitigado |
| R-06 | Seguridad | Imagen manipulada: la firma se verifica en el pipeline y no dentro del clúster | Baja | Alta | Política de admisión de imágenes; nadie despliega a mano; verificación en clúster como mejora (ADR-09) | Aceptado |
| R-07 | Seguridad | Token de integración filtrado: sigue sirviendo hasta rotarlo (no hay rotación automática) | Media | Alta | Gitleaks en cada cambio; tokens separados y con el mínimo permiso; Secrets fuera de Git | Aceptado |
| R-08 | Seguridad | Backstage y MLflow sin autenticación y entrada con certificado autofirmado | Media | Media | Solo en la red local; políticas de red; Backstage solo por HTTPS (ADR-28) | Aceptado |
| R-09 | Seguridad | Vulnerabilidades sin arreglo publicado en las imágenes | Media | Media | Registro de hallazgos con decisión, VEX y fecha de revisión; contenedores sin root y con red restringida | Mitigado |
| R-10 | IA | Alucinación u omisión; la ayuda del Hub está desactualizada y el asistente la repite | Media | Media | Todo texto de IA es un borrador; verificaciones de horas, citas y términos; **actualizar la ayuda** | Abierto |
| R-11 | IA | Inyección de instrucciones: 1 de 10 intentos pasa (una orden mezclada con una pregunta válida) | Media | Baja | Prompt v3, guarda del contexto, el asistente solo explica y no ejecuta | Aceptado |
| R-12 | IA | Datos personales en textos libres sin política de retención ni de supresión | Baja | Media | Datos sintéticos; redacción de secretos; ningún dato sale a IA externa; **definir retención** | Abierto |
| R-13 | IA | Transcripción de voz incorrecta; falta la prueba con una voz humana | Media | Media | Transcripción visible y corregible; evaluación con voz limpia (6,6 % de error de palabras) | Abierto |
| R-14 | IA | Licencias de modelos y motores: el modelo de 3 B es solo de investigación y Piper es GPL | Baja | Media | El 3 B solo se usa para comparar; Piper corre en un servicio aparte (ADR-26) | Mitigado |
| R-15 | Cronograma | Ensayos de la demostración insuficientes (faltan tres ensayos cronometrados) | Alta | Alta | Guion de 15 minutos, plan B por punto, tres ensayos y video de respaldo (spec 015) | Abierto |
| R-16 | Cronograma | El docente no acepta el audio como modalidad del módulo 6 (15 % del diplomado) | Media | Alta | Confirmar por escrito con el docente antes del 30 de noviembre; la infografía y la imagen quedan como mejora | Abierto |

::: {custom-style="Nota"}
*Nota.* Elaboración propia a partir de `docs/modelo-de-amenazas.md`, `constitution/roadmap.md`, `docs/auditoria-2026-11.md` y las secciones técnicas de este informe. Las calificaciones de probabilidad e impacto son una estimación inicial que el equipo debe confirmar. Responsable de cada riesgo: ver el complementario 06.
:::

## Qué no cubre el análisis

El análisis no cubre a un adversario con acceso al nodo o a la cuenta de administrador del clúster ni la denegación de servicio (la cuota del plan y el escalado del Hub la limitan, pero no hay protección dedicada); tampoco cubre políticas de admisión adicionales como Kyverno, que quedan como mejora (`docs/modelo-de-amenazas.md`). El modelo de amenazas se revisa cada seis meses; la próxima revisión es el 15 de mayo de 2027.

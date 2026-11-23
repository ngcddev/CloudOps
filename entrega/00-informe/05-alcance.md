<!-- Sección 5 · Fuente: constitution/roadmap.md, constitution/mission.md, entrega/datos/trazabilidad.csv. Cada ítem del alcance se enlaza con al menos un requisito. -->

# Alcance

El alcance se organiza por módulos del diplomado y por componentes. Los estados corresponden a la revisión del 16 de noviembre de 2026: **Construido** significa que existe, tiene pruebas automatizadas y se ejecutó de punta a punta; **En cierre** significa que existe pero faltan verificaciones o ensayos (se detallan en cada fila). El módulo 7 (pruebas finales, recuperación y demostración) está en curso: la sustentación es el 30 de noviembre de 2026.

## Alcance construido en los módulos 1 a 4

::: {custom-style="Table Caption"}
**Tabla {T:alcance-1-4}**\
*Alcance construido en los módulos 1 a 4*
:::

| Módulo | Componente | Qué se construyó | Requisitos | Estado |
|----------|-----------|----------------------------|-----------|--------|
| 1 · Contenedores | Aplicación y servicios | API (FastAPI), consola (React y nginx), PostgreSQL y tres sitios de ejemplo en contenedores, con Compose, pruebas y un solo comando | RNF-02, RNF-15 | Construido |
| 1 · Contenedores | Infraestructura propia | Todo corre en el laboratorio sin servicios de terceros; la red de salida está denegada por defecto | RNF-01 | Construido |
| 1 · Contenedores | Gestión de clientes | Agencia, usuarios, clientes, proyectos, servicios y planes | RF-01, RF-02 | Construido (los usuarios se cargan por semilla) |
| 2 · Kubernetes y GitOps | Plataforma | Clúster k3d, espacio de nombres por cliente, Argo CD y ApplicationSet | RF-03, RNF-03, RNF-04 | Construido |
| 2 · Kubernetes y GitOps | Mesa de servicio | Solicitudes, prioridad P1 a P4, historial y horas | RF-04, RF-05 | Construido |
| 2 · Kubernetes y GitOps | Cambios por GitOps | Aprobar un cambio escribe la versión en `hub-gitops`; Argo CD la aplica y el Hub confirma | RF-06, RF-07 | Construido |
| 2 · Kubernetes y GitOps | Platform engineering | Catálogo y plantilla de alta en Backstage, chart de Helm equivalente a Kustomize | RF-22, RF-26 | Construido |
| 3 · DevSecOps | Puerta de seguridad | Gitleaks, Trivy, SBOM, firma y verificación con Cosign; el Hub bloquea y explica | RF-08, RF-09, RNF-05, RNF-06 | Construido |
| 3 · DevSecOps | Roles y auditoría | Dos roles, segregación de funciones y bitácora de solo lectura | RF-01, RF-10 | Construido |
| 4 · IaC y observabilidad | Observabilidad | Prometheus, Alertmanager, Blackbox, Loki, Alloy, Tempo y Grafana; alertas y presupuesto de error | RF-11, RF-12, RNF-07, RNF-18 | Construido |
| 4 · IaC y observabilidad | Incidentes y recuperación | Incidente automático, SLA con hora real, rollback y MTTR | RF-12, RF-13, RF-14 | Construido |
| 4 · IaC y observabilidad | Tableros y portal | Tablero de la agencia, portal del cliente, KPI; interfaz en español con estados con texto e ícono | RF-15, RF-16, RF-17, RNF-10, RNF-17 | Construido (prueba de usabilidad con tres personas y auditoría de accesibilidad pendientes) |
| 4 · IaC y observabilidad | Infraestructura como código | OpenTofu para los clientes, estado remoto con bloqueo y prueba de deriva | RNF-08, RNF-16 | Construido (`tofu plan` real pendiente) |

::: {custom-style="Nota"}
*Nota.* Elaboración propia a partir de `constitution/roadmap.md` y de la matriz de trazabilidad. La relación completa de cada requisito con su estado está en la sección de matriz de trazabilidad.
:::

## Alcance previsto en los módulos 5 a 7

::: {custom-style="Table Caption"}
**Tabla {T:alcance-5-7}**\
*Alcance de los módulos 5 a 7*
:::

| Módulo | Componente | Alcance | Requisitos | Estado |
|----------|-----------|----------------------------|-----------|--------|
| 5 · MLOps y LLMOps | Asistente con IA local | Compuerta de ML, asistente de ayuda, RAG propio y evaluación con preguntas ciegas | RF-25, RF-28 | Construido |
| 5 · MLOps y LLMOps | Borradores y diagnóstico | Resumen del incidente y mensaje al cliente con aprobación humana; diagnóstico con evidencia citada | RF-18, RF-19, RF-23 | Construido (el diagnóstico usa el modelo general) |
| 5 · MLOps y LLMOps | Registro y seguridad de la IA | MLflow con registro y alias, promoción con comparación, integridad de modelos y pruebas de inyección | RF-29, RNF-09, RNF-20 | Construido |
| 5 · MLOps y LLMOps | Reportes | Reporte operativo y ejecutivo en PDF | RF-20 | Construido |
| 6 · IA multimodal | Voz del asistente | Dictar la pregunta, corregir lo entendido y escuchar la respuesta, en CPU | RF-27 | En cierre (falta probar con voz humana y micrófono real) |
| 7 · Integrador | Pruebas finales y recuperación | Respaldo y restauración, pruebas de red y de seguridad, simulaciones de falla | RNF-13, RNF-14, RNF-21 | En cierre (alerta real disparada pendiente) |
| 7 · Integrador | Demostración y sustentación | Guion de 15 minutos de una sola persona, datos semilla y ensayos | RNF-11, RNF-19 | En cierre (ensayos pendientes; 17 de 19 requerimientos de prioridad M hechos) |

::: {custom-style="Nota"}
*Nota.* Elaboración propia. Los pendientes de cada fila se registran como tareas de la especificación 015 (demostración integrada).
:::

## Funcionalidades y componentes dentro del alcance

Dentro del alcance están: la gestión de clientes, proyectos, servicios y planes; la mesa de servicio con prioridades y SLA; los cambios y despliegues por GitOps con puerta de seguridad; el monitoreo, los incidentes automáticos y el rollback; los tableros, el portal del cliente y los reportes; el asistente de IA local con RAG, borradores aprobados por personas y diagnóstico; la voz del asistente; el registro de modelos; la infraestructura como código; la observabilidad con SLI y SLO; los respaldos y los procedimientos de operación (`runbooks/`).

## Elementos fuera del alcance

::: {custom-style="Table Caption"}
**Tabla {T:fuera-alcance}**\
*Elementos fuera del alcance y motivo*
:::

| Elemento | Motivo | Requisito |
|---------------|---------------------------------|-----------|
| Facturación, pagos y dominios reales | Decisión de alcance desde el inicio | RF-24 (fuera de alcance) |
| Infografía mensual por cliente | Diferida por consumo de GPU; el punto 10 de la demostración pasó a ser la voz | RF-21 (diferido) |
| Imagen, video y 3D con IA (ComfyUI) | Competirían con el modelo de lenguaje por una GPU de 6 a 8 GB; el módulo 6 se cubre con audio (ADR-25) | RF-27 |
| Alta disponibilidad | El laboratorio es un solo equipo de un nodo (ADR-27) | RNF-12 a RNF-14 |
| Alta de usuarios y de la agencia desde la aplicación | Los usuarios se cargan por semilla | RF-01 (parcial) |
| Modelo de código especializado para el diagnóstico | Se usa el modelo general del asistente | RF-23 (parcial) |
| Verificación de firmas dentro del clúster | Se verifica en el pipeline (ADR-09) | RNF-05 |
| CDN, serverless, escala global y multi-agencia | Fuera del caso de estudio | — |
| Datos reales de clientes | Todo dato es sintético (RNF-09) | RNF-09, RNF-18 |

::: {custom-style="Nota"}
*Nota.* Elaboración propia a partir de `constitution/mission.md` y de las decisiones de arquitectura de este informe.
:::

## Trazabilidad del alcance

Cada ítem de las Tablas {T:alcance-1-4} y {T:alcance-5-7} apunta a al menos un requisito de la matriz de trazabilidad, y cada requisito de la matriz está cubierto por un ítem del alcance o aparece en la Tabla {T:fuera-alcance}.

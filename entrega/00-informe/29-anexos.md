<!-- GENERADA por entrega/generar_tablas.py a partir de entrega/datos/evidencias.csv. No editar a mano. -->

# Anexos

## Apéndice A. Catálogo de evidencias

Cada evidencia tiene un identificador E-nn que se cita en la matriz de trazabilidad. Las capturas y salidas marcadas como «pendiente» las incorpora el equipo en el lugar del marcador que sigue a la tabla; las marcadas como «existe» ya están en el repositorio.

::: {custom-style="Table Caption"}
**Tabla {T:ev}**\
*Catálogo de evidencias*
:::

| ID | Evidencia | Tipo | Requisitos | Estado |
|------|----------------------------------------|------------|--------------|----------|
| E-01 | Repositorio Git: página principal, ramas, issues y pull requests | captura | RNF-15 | pendiente |
| E-02 | CI de GitHub con las cinco verificaciones en verde | captura | RNF-15 RNF-06 | pendiente |
| E-03 | Salida completa de las pruebas del backend | salida de comando | RF-01 RF-02 RF-05 RF-10 RF-18 RF-23 RNF-11 RNF-12 RNF-14 RNF-15 | pendiente |
| E-04 | Corrida de la puerta de seguridad aprobada en Gitea Actions | captura | RF-08 RNF-05 | pendiente |
| E-05 | Corrida rechazada por un secreto (Gitleaks) | captura | RF-08 RF-09 RNF-06 | pendiente |
| E-06 | Reporte de Trivy y SBOM de una imagen | captura | RF-08 RNF-05 | pendiente |
| E-07 | Firma y procedencia verificadas con Cosign | captura | RF-08 RNF-05 | pendiente |
| E-08 | Nueve Applications de Argo CD sincronizadas y sanas | captura | RF-03 RF-06 RF-07 RF-26 RNF-04 | pendiente |
| E-09 | Pods por namespace en Kubernetes | salida de comando | RF-03 RNF-02 RNF-03 | pendiente |
| E-10 | Tablero de Grafana del servicio de sitios | captura | RF-15 RNF-07 | pendiente |
| E-11 | Tablero de Grafana RED y USE | captura | RF-15 | pendiente |
| E-12 | Tablero del Hub con disponibilidad frente al SLO | captura | RF-15 RF-17 | pendiente |
| E-13 | Alerta SitioCaido en estado firing | captura | RF-11 RF-12 RNF-07 | pendiente |
| E-14 | Traza de una petición con su trace_id y el registro correlacionado | captura | RF-15 RNF-18 | pendiente |
| E-15 | Modelo compuerta-asistente con el alias production en MLflow | captura | RF-29 | pendiente |
| E-16 | Corridas de evaluación y métricas en MLflow | captura | RF-29 RNF-20 | pendiente |
| E-17 | Respuesta del asistente en modo RAG con sus fuentes | captura | RF-25 RF-28 | pendiente |
| E-18 | Pantallas de la voz del asistente en un navegador real | captura | RF-27 | existe |
| E-19 | Resultados de las pruebas de inyección y de documentos maliciosos | salida de comando | RNF-09 | pendiente |
| E-20 | Rollback con el MTTR en el incidente | captura | RF-14 RF-13 | pendiente |
| E-21 | Reporte ejecutivo en PDF | archivo | RF-20 | pendiente |
| E-22 | Portal del cliente con estado, incidentes y solicitudes | captura | RF-04 RF-05 RF-16 RF-19 RNF-17 | pendiente |
| E-23 | Catálogo y plantilla de Backstage | captura | RF-22 | pendiente |
| E-24 | Plan de OpenTofu sin cambios y prueba de deriva | salida de comando | RNF-04 RNF-08 RNF-16 | pendiente |
| E-25 | Respaldo y restauración de PostgreSQL | salida de comando | RNF-13 | pendiente |
| E-26 | Simulaciones de falla en el clúster | salida de comando | RNF-07 RNF-21 | pendiente |
| E-27 | Pruebas de red: entrada y salida denegadas por defecto | salida de comando | RNF-03 RNF-01 | pendiente |
| E-28 | Recorrido del caso del restaurante: caída, incidente, rollback y MTTR | salida de comando | RF-12 RF-14 RNF-07 | pendiente |
| E-29 | Matriz de tutor de IA con aciertos, omisiones y alucinaciones | salida de comando | RF-25 | pendiente |
| E-30 | Modalidad multimodal: audio (la imagen, el video y el 3D no aplican) | texto | RF-27 | existe |

::: {custom-style="Nota"}
*Nota.* Elaboración propia a partir de `entrega/datos/evidencias.csv`. La columna «cómo obtenerla» de cada evidencia está en ese archivo y en su marcador.
:::

## Apéndice B. Evidencias por incorporar

[EVIDENCIA E-01 · Repositorio Git: página principal, ramas, issues y pull requests · Abrir https://github.com/ngcddev/CloudOps y capturar README, ramas y un pull request fusionado]

[EVIDENCIA E-02 · CI de GitHub con las cinco verificaciones en verde · Abrir un pull request fusionado y capturar la pestaña Checks]

[EVIDENCIA E-03 · Salida completa de las pruebas del backend · docker compose exec api pytest -q (1.134 recogidas)]

[EVIDENCIA E-04 · Corrida de la puerta de seguridad aprobada en Gitea Actions · Gitea, repositorio del sitio, pestaña Actions, corrida en verde]

[EVIDENCIA E-05 · Corrida rechazada por un secreto (Gitleaks) · Tarea T03 de la spec 015: versión con un secreto a propósito]

[EVIDENCIA E-06 · Reporte de Trivy y SBOM de una imagen · Hub, versión del servicio, controles, descarga del reporte y del SBOM]

[EVIDENCIA E-07 · Firma y procedencia verificadas con Cosign · Hub, controles de la versión, paso de verificación de firma]

[EVIDENCIA E-08 · Nueve Applications de Argo CD sincronizadas y sanas · Argo CD, lista de Applications]

[EVIDENCIA E-09 · Pods por namespace en Kubernetes · kubectl get pods -A con Pod Security restricted en los clientes]

[EVIDENCIA E-10 · Tablero de Grafana del servicio de sitios · Grafana, tablero de sitios con SLI y presupuesto de error]

[EVIDENCIA E-11 · Tablero de Grafana RED y USE · Grafana, tablero de plataforma]

[EVIDENCIA E-12 · Tablero del Hub con disponibilidad frente al SLO · Consola, tablero de la agencia]

[EVIDENCIA E-13 · Alerta SitioCaido en estado firing · Prometheus, pestaña Alerts, con la v2 rota publicada]

[EVIDENCIA E-14 · Traza de una petición con su trace_id y el registro correlacionado · Grafana, Explore, Tempo y Loki]

[EVIDENCIA E-15 · Modelo compuerta-asistente con el alias production en MLflow · MLflow, Models]

[EVIDENCIA E-16 · Corridas de evaluación y métricas en MLflow · MLflow, Experiments]

[EVIDENCIA E-17 · Respuesta del asistente en modo RAG con sus fuentes · Consola, Asistente, con ASSISTANT_CONTEXT_MODE=rag]

[EVIDENCIA E-19 · Resultados de las pruebas de inyección y de documentos maliciosos · python ai/eval/run_eval.py y python ai/eval/probar_documento_malicioso.py]

[EVIDENCIA E-20 · Rollback con el MTTR en el incidente · Consola, detalle del incidente tras el rollback]

[EVIDENCIA E-21 · Reporte ejecutivo en PDF · Consola, Reportes, descargar el PDF del ejecutivo]

[EVIDENCIA E-22 · Portal del cliente con estado, incidentes y solicitudes · Ventana de incógnito con el usuario de un cliente]

[EVIDENCIA E-23 · Catálogo y plantilla de Backstage · Backstage por HTTPS, Catalog y Create]

[EVIDENCIA E-24 · Plan de OpenTofu sin cambios y prueba de deriva · bash infra/pruebas/drift.sh]

[EVIDENCIA E-25 · Respaldo y restauración de PostgreSQL · bash gitops/pruebas/respaldo.sh]

[EVIDENCIA E-26 · Simulaciones de falla en el clúster · bash gitops/pruebas/simulaciones.sh]

[EVIDENCIA E-27 · Pruebas de red: entrada y salida denegadas por defecto · bash gitops/pruebas/salida-hub.sh y bash gitops/pruebas/aislamiento-red.sh]

[EVIDENCIA E-28 · Recorrido del caso del restaurante: caída, incidente, rollback y MTTR · bash gitops/pruebas/demo-caso-restaurante.sh]

[EVIDENCIA E-29 · Matriz de tutor de IA con aciertos, omisiones y alucinaciones · python ai/tutor/evaluar.py]

## Apéndice C. Modalidad multimodal

El componente multimodal adicional del proyecto es el audio: dictado y respuesta hablada del asistente (RF-27, evidencia E-18). La generación de imagen con ComfyUI, de video y de 3D no se construyó (ver la sección de alcance y las decisiones de arquitectura); por eso no hay capturas de esas herramientas.

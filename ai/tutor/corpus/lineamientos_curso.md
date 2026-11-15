# Lineamientos del diplomado CloudForge AI 5.0 para el tutor

Resumen de los lineamientos del diplomado CloudForge AI 5.0 (Unicomfacauca) que el tutor puede citar; la fuente completa es el documento del diplomado del repositorio (docs/diplomado-cloudforge-ai-5.0.md). Cada sección `##` es un trozo recuperable.

## Duración y estructura del diplomado

El diplomado dura 120 horas, con 48 horas teóricas y 72 prácticas (40 % y 60 %), repartidas en siete módulos. Va del 14 de septiembre al 20 de noviembre de 2026, con tres encuentros semanales de 6:00 pm a 10:00 pm en modalidad híbrida. El módulo 1 trata fundamentos y contenedores, el 2 Kubernetes, GitOps y Platform Engineering, el 3 DevSecOps, el 4 IaC y observabilidad, el 5 MLOps y LLMOps, el 6 IA multimodal y el 7 el proyecto integrador.

## Módulo 2: Kubernetes, GitOps y Platform Engineering

El módulo 2 tiene 8 horas teóricas y 12 prácticas, pesa el 15 % de la nota y se centra en el modelo declarativo, los controladores y la reconciliación, no en memorizar YAML. Cubre control plane, nodos, pods, deployments, replicasets, statefulsets, daemonsets, services, ingress o gateway, configmaps, secrets, volúmenes, jobs, cronjobs, namespaces, RBAC, requests y limits, probes, autoscaling, network policies y alta disponibilidad. En lo procedimental pide desplegar, actualizar, hacer rollback, configurar, usar almacenamiento y health checks, empaquetar con Helm y variar por ambiente con Kustomize. En GitOps pide Argo CD con Git como fuente de verdad, separar código y configuración, revisión por pull request, sincronización y detección de drift. En Platform Engineering pide Backstage con un catálogo mínimo, plantillas, documentación como código y golden paths.

## Tutor de IA del módulo 2

En el módulo 2 se usa un LLM con RAG sobre la documentación de Kubernetes y los lineamientos del curso como tutor técnico. El tutor debe responder solo con lo que dice su material, citar la fuente y reconocer cuando no sabe. Se evalúa con una matriz de aciertos, omisiones y alucinaciones: un acierto es una respuesta correcta y completa, una omisión es una respuesta a la que le falta algo que el material sí tiene, y una alucinación es una afirmación que el material no respalda o que lo contradice.

## Evaluación del aprendizaje

La nota del diplomado se reparte así: módulo 1 el 10 %, módulo 2 el 15 %, módulo 3 el 15 %, módulo 4 el 10 %, módulo 5 el 15 %, módulo 6 el 15 % y el proyecto integrador el 20 %. La evaluación es auténtica: entregables operacionales, defensa de decisiones, análisis de fallas y capacidad de reconstruir el entorno. Reproducir el laboratorio en otra estación es parte de la evaluación.

## Rúbrica del proyecto integrador

El proyecto integrador se evalúa así: arquitectura, requisitos y decisiones el 10 %; plataforma Kubernetes, GitOps e Infrastructure as Code el 20 %; DevSecOps y cadena de suministro el 15 %; observabilidad, SLI y SLO y operación el 10 %; MLOps y LLMOps y reproducibilidad el 15 %; IA local y componente multimodal el 15 %; y documentación, privacidad, sostenibilidad y sustentación el 15 %. Los equipos son preferiblemente de 3 a 5 integrantes y la solución debe poder clonarse, desplegarse y verificarse por el jurado.

## Uso de la IA en el diplomado

La IA se usa como copiloto supervisado: se permite para explicar, generar código, pruebas, documentación y análisis, siempre con evidencia de validación. El uso se gobierna, no se prohíbe. En código hay que defender la lógica y ejecutar pruebas; en RAG hay que identificar las fuentes; en infraestructura hay que justificar recursos y permisos. No poder explicar un artefacto generado por IA es una debilidad técnica aunque funcione. La regla del diplomado es que la IA acelera, pero la responsabilidad sigue siendo humana.

## Datos, privacidad y laboratorio

En el laboratorio no se cargan datos personales reales a modelos, índices vectoriales o repositorios de práctica sin autorización expresa: se usan datos sintéticos, anonimizados o públicos. El marco colombiano es la Ley 1581 de 2012 y los lineamientos de MinTIC. Los laboratorios no comparten credenciales con infraestructura productiva: se usan cuentas de laboratorio, registries separados y credenciales temporales que se revocan al cierre. La ejecución local de modelos no elimina todos los riesgos.

## Rutas de laboratorio según el hardware

El diplomado define tres rutas por capacidad de cómputo. La ruta A es el equipo básico (CPU y 16 GB de RAM) con un LLM cuantizado pequeño y clientes de una API en GPU compartida. La ruta B es una GPU de consumo como la RTX 3050, con LLM cuantizado, imagen generativa y video o 3D ligeros. La ruta C es un nodo compartido con GPU para video generativo, 2D a 3D y serving concurrente. Todas recorren el mismo proceso y las cargas pesadas se desplazan al nodo compartido.

## Entregables del proyecto integrador

Los entregables mínimos del proyecto son quince: documento de contexto y decisiones, repositorio Git, aplicación contenedorizada con pruebas, manifiestos de Kubernetes o Helm y Kustomize, pipeline CI/CD con controles de seguridad, evidencia de SBOM, escaneo y firma, repositorio GitOps sincronizado con Argo CD, infraestructura como código, dashboard con al menos un SLI y SLO, registro de experimentos y modelos, servicio de IA local con RAG, un workflow multimodal adicional, análisis de privacidad y riesgos de IA, runbook de operación, y el informe ejecutivo con la sustentación.

# Diplomado CloudForge AI 5.0

**Ingeniería Cloud Native, DevSecOps, Kubernetes, Platform Engineering, MLOps e Inteligencia Artificial Local Multimodal**

- Propuesta académica de educación continuada para Ingeniería de Sistemas (Unicomfacauca)
- Autor del documento: Oscar Andrés Angulo López
- Fecha del PDF: 25 de agosto de 2026 (26 páginas)

---

## 1. Generalidades

| Campo | Detalle |
|---|---|
| Duración | 120 horas |
| Cupo | Máximo 25 personas |
| Fecha de inicio | 14/09/2026 |
| Fecha de finalización | 20/11/2026 |
| Distribución pedagógica | 48 h teóricas y 72 h prácticas (40 % / 60 %) |
| Horario | 3 encuentros semanales, 6:00 pm a 10:00 pm (días pendientes por confirmar) |
| Modalidad | Híbrido (presencial y virtual) |
| Propuesta válida hasta | 31 de agosto de 2026 |

### Inversión (diligenciado por Educación Continua de Unicomfacauca)

- Particulares: $2.500.000
- Estudiantes y egresados (10 % de descuento): $2.250.000

### Requisitos para obtener la certificación

Cursos y diplomados se aprueban con 80 % de asistencia (los seminarios, con 100 %). El PDF indica:

- 80 % de asistencia a las clases online sincrónicas.
- Aprobación final, preferiblemente grupal, de un **"Plan Estratégico de Desarrollo Sostenible y Marketing"** aplicado a una organización real o caso de estudio, integrando diagnóstico, formulación estratégica, marketing, criterios ESG, plan de acción, indicadores y comunicación de resultados.
- Participación activa en la formación virtual y conocimiento de la lectura obligatoria.

> ⚠️ **Inconsistencia en el original:** este párrafo de certificación parece copiado de otro diplomado (sostenibilidad y marketing). No coincide con el resto del documento, cuyo producto final es el *Proyecto integrador CloudForge AI*. Conviene confirmarlo con Educación Continua.

---

## 2. Nombre y concepto diferenciador

CloudForge AI 5.0 expresa la idea de una "forja" tecnológica en la que el participante construye, asegura, automatiza y opera plataformas digitales modernas. "AI 5.0" identifica la convergencia entre infraestructura cloud native, experiencia de desarrollador, operación inteligente, MLOps/LLMOps e IA local multimodal con revisión humana, soberanía de datos y responsabilidad técnica.

## 3. Justificación

- **Cloud native y Kubernetes.** El informe anual 2025 de la CNCF (publicado en 2026) reporta que el 82 % de los usuarios de contenedores encuestados ejecuta Kubernetes en producción, y que muchas organizaciones con IA generativa lo usan para cargas de inferencia. El ingeniero ya no solo escribe aplicaciones: diseña plataformas, automatiza infraestructura, protege la cadena de suministro, observa sistemas distribuidos y opera modelos de IA. La documentación de Kubernetes distingue entre ambientes de aprendizaje y clústeres de producción; el diplomado busca pasar de "hacer que funcione" a justificar cómo se despliega, actualiza, monitorea, recupera y protege un servicio.
- **Platform Engineering.** Kubernetes no resuelve la complejidad por sí solo. Se crean plataformas internas con caminos estandarizados y autoservicio (ej. Backstage: catálogos, plantillas, documentación como código, portales de desarrollador).
- **DevSecOps.** La seguridad se integra al ciclo de vida: NIST SSDF (prácticas de alto nivel), SLSA (garantías progresivas sobre procedencia e integridad) y Sigstore (firma y verificación de binarios, imágenes, SBOM).
- **Observabilidad.** OpenTelemetry como marco abierto para trazas, métricas y logs; operación basada en medición, diagnóstico y aprendizaje (SRE, objetivos de nivel de servicio).
- **MLOps.** Experimentación, versionamiento, registro de modelos, reproducibilidad, despliegue y monitoreo (MLflow, Kubeflow). Un modelo en un notebook no es una solución de ingeniería.
- **IA local y soberana.** LLM/SLM en estaciones, servidores del laboratorio o nodos compartidos: GPT4All (LocalDocs), Ollama, AnythingLLM (RAG) y Open WebUI (autohospedado, funciona sin conexión).
- **Privacidad, continuidad y costo.** Marco colombiano: CONPES 4144 de 2025 (Política Nacional de IA) y lineamientos de seguridad y privacidad para IA de MinTIC dentro del MSPI (2026).
- **Dimensión multimodal.** Stability Matrix (administrador de paquetes/modelos visuales), ComfyUI (motor basado en nodos con API), Hunyuan3D-2.1 (imagen a 3D) y Wan2.2 (texto/imagen a video). El objetivo no es diseño audiovisual, sino tratar texto, código, imagen, video y 3D como cargas de IA que se instalan, integran, versionan, aseguran, exponen y observan.
- **Escenario integrador de ejemplo.** Un asistente local que revise código de infraestructura; backend en Kubernetes; pipeline con análisis de vulnerabilidades; registro de modelos; servicio de imagen con ComfyUI; trabajos pesados de video/3D en un nodo GPU compartido; monitoreo de latencia y consumo; documentación en un portal de desarrollador.
- **Hardware heterogéneo (tres rutas).** Las estaciones con GPU RTX 3050 son una oportunidad, no una barrera. Ver sección 8.3.
- **Pertinencia institucional.** Ingeniería de Sistemas de Unicomfacauca se ofrece en Popayán y Santander de Quilichao, tiene reacreditación de alta calidad y semilleros en Ingeniería de Software e IA y Big Data.
- **Pertinencia territorial.** El Cauca tiene administración pública, educación, salud, comercio, turismo, agroindustria, manufactura, logística y emprendimientos digitales, con recursos limitados y conectividad variable. Cloud native no implica migrar todo a nube pública: también plataformas híbridas, on-premise y edge.
- **Principios estables sobre herramientas.** Infraestructura declarativa, automatización, idempotencia, trazabilidad, menor privilegio, despliegue reproducible, observabilidad, recuperación, seguridad de la cadena de suministro, evaluación de modelos y responsabilidad sobre datos. Docker, Kubernetes, Argo CD, OpenTofu, MLflow, Ollama o ComfyUI son medios.

### Figura 1. Arquitectura pedagógica y tecnológica (de abajo hacia arriba)

| Capa | Contenido |
|---|---|
| 5. Experiencias y productos IA | Texto · código · RAG · agentes · imagen · video · 2D→3D |
| 4. IA local multimodal | GPT4All · Ollama · AnythingLLM · Open WebUI · Stability Matrix · ComfyUI · Hunyuan3D · Wan |
| 3. MLOps / LLMOps | MLflow · Kubeflow · model registry · evaluación · serving · trazabilidad |
| 2. Plataforma Cloud Native | Kubernetes · Helm · Argo CD · Backstage · API Gateway · almacenamiento OCI |
| 1. Fundaciones de ingeniería | Git · Linux · Docker · OpenTofu/IaC · DevSecOps · SLSA/SBOM · OpenTelemetry |

*Principio transversal: soberanía tecnológica, operación reproducible, seguridad por diseño y revisión humana.*

---

## 4. Objetivos

### 4.1 Objetivo general

Desarrollar capacidades integrales para diseñar, automatizar, asegurar y operar plataformas cloud native con Kubernetes, DevSecOps, Platform Engineering, MLOps e IA local multimodal, mediante laboratorios reproducibles y un proyecto aplicado a necesidades organizacionales y territoriales.

### 4.2 Objetivos específicos

1. Diseñar arquitecturas cloud native con contenedores, servicios desacoplados y patrones declarativos.
2. Implementar clústeres Kubernetes para aplicaciones, servicios de datos y cargas de IA.
3. Automatizar infraestructura y despliegues con IaC, CI/CD y GitOps.
4. Integrar controles DevSecOps: vulnerabilidades, secretos, dependencias, SBOM y procedencia de artefactos.
5. Instrumentar servicios distribuidos con métricas, logs y trazas.
6. Operacionalizar modelos con MLOps y LLMOps (versionamiento, evaluación, serving, monitoreo).
7. Desplegar LLM/SLM locales con GPT4All, Ollama, AnythingLLM, Open WebUI y equivalentes.
8. Construir flujos multimodales locales para texto, código, imagen, video y 3D.
9. Evaluar riesgos técnicos, éticos, jurídicos y de privacidad.
10. Integrar un producto final reproducible que evidencie arquitectura, automatización, seguridad, observabilidad e IA local.

---

## 5. Competencias a desarrollar

Enfoque de **competencia observable**: cada capacidad se demuestra con artefactos, configuraciones, repositorios, métricas, pruebas, evidencias de despliegue o decisiones justificadas. No se busca memorizar comandos, sino autonomía progresiva para transformar requisitos en una plataforma operable.

### 5.1 Competencias genéricas

- Pensamiento sistémico (software, infraestructura, datos, redes, seguridad, operación e IA).
- Pensamiento crítico para validar resultados generados por IA y distinguir automatización útil de dependencia acrítica.
- Comunicación técnica (arquitectura, riesgos, decisiones, incidentes, métricas, recomendaciones).
- Trabajo colaborativo con roles de desarrollo, plataforma, seguridad, observabilidad, datos y operación.
- Aprendizaje autónomo para evaluar herramientas emergentes.
- Responsabilidad ética en datos, modelos, código, contenidos generativos y recursos computacionales.

### 5.2 Competencias específicas

- Construir imágenes de contenedor reproducibles, pequeñas y seguras (incluidos servicios de IA).
- Configurar objetos de Kubernetes: namespaces, deployments, statefulsets, services, ingress, configmaps, secrets, volumes, jobs y políticas.
- Diseñar flujos GitOps donde Git sea la fuente declarativa de verdad.
- Producir infraestructura como código con flujos OpenTofu/Terraform-compatible.
- Implementar pipelines CI/CD con pruebas, análisis estático, escaneo de imágenes, SBOM y verificación de artefactos.
- Aplicar controles basados en NIST SSDF, SLSA, firma de artefactos y secure by design.
- Instrumentar con OpenTelemetry; construir tableros de métricas, logs y trazas.
- Definir SLI/SLO y criterios de disponibilidad, latencia, error y capacidad.
- Gestionar experimentos, modelos y artefactos con MLflow y componentes MLOps.
- Construir espacios RAG locales (GPT4All LocalDocs, AnythingLLM, equivalentes).
- Exponer modelos locales por API y conectarlos con apps, herramientas de desarrollo y frontends autohospedados.
- Diseñar workflows de ComfyUI y Stability Matrix.
- Integrar generación de video y reconstrucción 2D→3D como trabajos asíncronos.
- Documentar decisiones sobre licencias de modelos, privacidad, trazabilidad, propiedad intelectual y uso responsable.
- Operar una plataforma educativa híbrida (estación local + clúster Kubernetes + nodo GPU compartido).

### Perfil de salida esperado

Talento **junior o intermedio** en Cloud/DevOps, Platform Engineering, DevSecOps, MLOps/LLMOps y operación de servicios de IA. No certifica por sí solo un perfil senior de SRE, arquitecto cloud o especialista de seguridad; construye una base integrada y demostrable para avanzar hacia esos roles.

---

## 6. Estructura curricular

Siete módulos, 40 % teoría y 60 % práctica. La IA local es transversal: asistencia al desarrollo desde los primeros ejercicios, formalizada en MLOps/LLMOps y culminada en servicios multimodales.

| Módulo | H. teóricas | H. prácticas | Total |
|---|---:|---:|---:|
| 1. Fundamentos Cloud Native, Linux, Git y contenedores | 8 | 8 | 16 |
| 2. Kubernetes, GitOps y Platform Engineering | 8 | 12 | 20 |
| 3. DevSecOps y seguridad de la cadena de suministro | 8 | 10 | 18 |
| 4. IaC, observabilidad, SRE y operación sostenible | 6 | 10 | 16 |
| 5. MLOps, LLMOps y serving de IA local | 8 | 10 | 18 |
| 6. IA local multimodal: texto, código, imagen, video y 3D | 8 | 8 | 16 |
| 7. Proyecto integrador CloudForge AI | 2 | 14 | 16 |
| **Total** | **48** | **72** | **120** |

Secuencia: entorno y empaquetado → Kubernetes → entrega y seguridad → observabilidad e infraestructura declarativa → modelos y workflows multimodales. El proyecto integrador conecta todo.

### Módulo 1. Fundamentos Cloud Native, Linux, Git y contenedores

- **Conceptual:** cliente-servidor, procesos, puertos, DNS, HTTP, TLS, virtualización vs contenedores, namespaces y cgroups (introductorio), imágenes, capas, registries, volúmenes, redes de contenedor, configuración externa, doce factores, inmutabilidad; concepto cloud native.
- **Procedimental:** versionar una app, Dockerfile, pruebas, variables y secretos de laboratorio, Docker Compose, publicar imagen en registro local/educativo, documentar construcción reproducible, inspeccionar tamaño, puertos, procesos y consumo.
- **IA local:** asistente con GPT4All u Ollama para explicar errores, proponer Dockerfiles, generar scripts Bash/Python y sugerir pruebas, validando cada salida (ejecución, linters, revisión manual). Regla del diplomado: la IA acelera, la responsabilidad sigue siendo humana.
- **Prácticas:** API mínima en Python o Node.js, imagen, base de datos y servicio auxiliar con Compose, fallo de configuración inducido y diagnosticado.
- **Microproyecto:** repositorio con README, Dockerfile, archivo de composición, variables de ejemplo, pruebas y registro de decisiones.

### Módulo 2. Kubernetes, GitOps y Platform Engineering

- Clústeres locales con kind, minikube, k3d o equivalente; luego clúster compartido. Énfasis en el modelo declarativo, controladores y reconciliación, no en memorizar YAML.
- **Conceptual:** control plane, nodos, pods, deployments, replicasets, statefulsets, daemonsets, services, ingress/gateway, configmaps, secrets, persistent volumes, storage classes, jobs, cronjobs, namespaces, RBAC, requests/limits, probes, autoscaling, network policies, alta disponibilidad; clúster de aprendizaje vs producción.
- **Procedimental:** desplegar, actualizar, rollback, configuración, almacenamiento, health checks, observar réplicas. Helm para empaquetar, Kustomize para variantes por ambiente; registro local o institucional.
- **GitOps:** Argo CD con Git como fuente de verdad; separar código y configuración, revisión por pull request, sincronización y detección de *drift*.
- **Platform Engineering:** Backstage como referencia; catálogo mínimo de servicios o, si no hay infraestructura, diseño del catálogo, plantillas, documentación y *golden paths*.
- **IA local:** LLM con RAG sobre documentación de Kubernetes y lineamientos del curso como tutor técnico; matriz de aciertos, omisiones y alucinaciones.

### Módulo 3. DevSecOps y seguridad de la cadena de suministro

- Referencia: NIST SSDF, SLSA, secure by design, firma y verificación.
- **Conceptual:** threat modeling básico, dependencias, secretos, análisis estático, análisis de composición (SCA), vulnerabilidades de imágenes, hardening, usuarios no privilegiados, reducción de superficie, SBOM, procedencia, firma, políticas de admisión, segregación de funciones; vulnerabilidad conocida vs mala configuración vs riesgo contextual.
- **Procedimental:** pipeline con lint, pruebas, construcción, escaneo y publicación. Trivy (vulnerabilidades, configuraciones, secretos), Syft (SBOM), Cosign/Sigstore (firma y verificación). Bitácora de hallazgos (criticidad, explotabilidad, decisión de tratamiento).
- **Seguridad del software generado por IA:** controles mínimos: pruebas automatizadas, análisis de dependencias, revisión de licencias, validación de comandos, escaneo de secretos, comparación con documentación oficial, trazabilidad de prompts. Marco de discusión: perfil SSDF de NIST para IA generativa.
- **Prácticas:** app con dependencias vulnerables, Dockerfile sobreprivilegiado, secreto expuesto y manifest con permisos excesivos; corregir, producir pipeline verificable, generar SBOM, firmar el artefacto y demostrar que una versión no autorizada no pasa los controles.

### Módulo 4. IaC, observabilidad, SRE y operación sostenible

- Herramientas: OpenTofu (IaC), OpenTelemetry (telemetría), Prometheus/Grafana/Loki o equivalentes.
- **Conceptual:** infraestructura declarativa, estado, plan, idempotencia, módulos, variables, secretos, drift, entornos, métricas RED y USE, trazas distribuidas, correlación de logs, SLI, SLO, error budget, alertas accionables, capacidad, recuperación, nociones de FinOps. Confiabilidad no es disponibilidad absoluta, sino niveles coherentes con el valor y costo.
- **Procedimental:** recursos con OpenTofu, dashboards, instrumentar una API con OpenTelemetry, simular latencia, pérdida de réplica y saturación, alertas, runbook, backup y recuperación.
- **AIOps con IA local:** logs y métricas sintéticos a un modelo local para hipótesis de diagnóstico y borradores de runbook; verificar contra trazas y métricas.
- **Operación responsable:** modelo más pequeño que satisfaga el caso, apagar servicios innecesarios, programar cargas pesadas, reutilizar artefactos, políticas de retención, medir recursos.

### Módulo 5. MLOps, LLMOps y serving de IA local

- Premisa: el valor de MLOps no está en una suite, sino en reproducir experimentos, identificar artefactos, comparar resultados, desplegar versiones y observar su comportamiento.
- **Conceptual:** datasets y artefactos, experiment tracking, model registry, versionamiento, pipelines, evaluación, serving, batch vs online inference, canary, rollback, drift (introductorio), monitoreo y métricas. LLMOps: cuantización, contexto, embeddings, RAG, evaluación de respuestas, latencia, consumo, guardrails, observabilidad de interacciones.
- **Procedimental:** MLflow para registrar experimentos y empaquetar al menos un modelo (Docker Compose o Helm sobre Kubernetes). Kubeflow por componentes si el hardware lo permite. Ruta desde notebook/script hasta endpoint de inferencia versionado.
- **Serving local de LLM/SLM:** Ollama y GPT4All; modelos cuantizados; medir latencia y memoria; API local; Open WebUI como frontend; AnythingLLM para RAG. Arquitectura completa: archivos de modelo, servidor, embeddings, índice vectorial, contexto, cliente, almacenamiento de conversaciones.
- **Evaluación:** preguntas de referencia para el asistente RAG; medir recuperación, pertinencia y afirmaciones no soportadas; documentar límites.
- **Seguridad y privacidad:** prompt injection, exfiltración de contexto, documentos maliciosos, secretos en prompts, modelos no confiables, licencias. Datos sintéticos, anonimizados o expresamente autorizados. La ejecución local no elimina todos los riesgos.

### Módulo 6. IA local multimodal: texto, código, imagen, video y 3D

Rasgo más diferenciador. Cada modalidad es un *workload* con perfil distinto de cómputo, almacenamiento, latencia y orquestación.

- **Texto y código:** GPT4All, Ollama, AnythingLLM, Open WebUI para generar/resumir/consultar documentación, crear código, explicar errores, proponer pruebas (scripts, Dockerfiles, manifests, documentación, pruebas unitarias, runbooks). Todo código generado debe compilar, ejecutar y pasar verificaciones.
- **Imagen:** Stability Matrix + ComfyUI; workflows reproducibles texto→imagen e imagen→imagen; nodos, modelos, prompts, seeds, parámetros, almacenamiento de outputs, automatización por API. Se evalúa reproducibilidad, trazabilidad e integración, no criterio artístico.
- **Video:** Wan2.2 u otros equivalentes, con jobs asíncronos: colas, estados de trabajo, almacenamiento de resultados, límites de concurrencia y monitoreo. En equipos básicos, la generación pesada va al nodo compartido.
- **Imagen a 3D:** Hunyuan3D-2.1 o equivalentes; refinamiento en Blender; artefacto versionado, exponible a app web, realidad aumentada o repositorio de activos.
- **Audio y otros medios:** transcripción, síntesis de voz y subtítulos como servicios complementarios si la infraestructura lo permite.
- **Laboratorio integrador:** microservicio o gateway que recibe una solicitud estructurada y la enruta a texto/código, imagen, video o 3D; registra tiempos, estado, consumo aproximado y ubicación del artefacto.

### Figura 2. Rutas de laboratorio según capacidad de cómputo

| Ruta | Perfil | Contenido |
|---|---|---|
| **A · Equipo básico** | CPU / 16 GB RAM o similar | Docker + kind/minikube; LLM cuantizado pequeño; GPT4All/Ollama; RAG y generación de código; cliente API GPU compartida |
| **B · RTX 3050** | GPU de consumo, VRAM según variante | LLM local cuantizado; ComfyUI / Stability Matrix; imagen generativa optimizada; MLOps de inferencia; video/3D ligero o por colas |
| **C · Nodo compartido** | Workstation o servidor GPU | Video generativo; 2D→3D y texturizado; model serving concurrente; Kubeflow/MLflow; pruebas de escalamiento y observabilidad |

*Todos recorren el mismo proceso; las cargas pesadas se desplazan al nodo compartido sin perder el aprendizaje de arquitectura, API, colas, monitoreo y despliegue.*

### Módulo 7. Proyecto integrador CloudForge AI

- 16 horas formales, alimentadas por evidencias desde el módulo 1. Preferiblemente equipos de **3 a 5** integrantes; resuelve una necesidad realista de una organización o sector del Cauca.
- No puede ser solo un informe: repositorio funcional, infraestructura reproducible, controles de entrega, telemetría y al menos un componente de IA local.
- **Propósito:** integrar software, infraestructura, seguridad, observabilidad e IA en una solución reconstruible y demostrable. Se privilegia coherencia arquitectónica y evidencia sobre acumulación de herramientas.
- **Casos sugeridos:** cooperativa cafetera con asistente RAG local; plataforma de mantenimiento para pequeña planta agroindustrial; portal de servicios universitarios; soporte para empresa de turismo; plataforma de capacitación para empresa de servicios públicos; gestión documental de entidad territorial con procesamiento local; inspección visual con modelos versionados y generación de material técnico.
- **Componente multimodal obligatorio:** además del LLM/SLM o RAG, al menos una modalidad adicional (imagen, video, 2D→3D, audio o visión artificial). La inferencia pesada puede consumir el nodo GPU compartido por API o cola; se evalúa integración, reproducibilidad, seguridad y observabilidad.

**Entregables mínimos**

1. Documento de contexto, usuarios, requisitos, restricciones y decisiones de arquitectura.
2. Repositorio Git con estrategia de ramas, issues, README y convenciones de contribución.
3. Aplicación/servicio contenedorizado con pruebas automatizadas.
4. Manifests de Kubernetes y/o Helm/Kustomize.
5. Pipeline CI/CD con controles de calidad y seguridad.
6. Evidencia de SBOM, escaneo de vulnerabilidades y firma/verificación (o control equivalente).
7. Repositorio GitOps con sincronización vía Argo CD o equivalente.
8. IaC para los recursos técnicamente viables en el laboratorio.
9. Dashboard de observabilidad (métricas, logs o trazas) con al menos un SLI/SLO.
10. Registro de experimentos/modelos o evidencia equivalente de MLOps.
11. Servicio de IA local con RAG o generación de código/documentación.
12. Workflow multimodal adicional (imagen, video, audio o 2D→3D).
13. Análisis de privacidad, seguridad, licencias, riesgos de IA y límites.
14. Runbook de operación, respaldo, recuperación y fallas comunes.
15. Informe ejecutivo, demostración técnica y sustentación ante jurado académico.

**Criterios de calidad:** una solución pequeña, reconstruible y bien observada vale más que una arquitectura excesiva con servicios inaccesibles o configuraciones no documentadas. El jurado debe poder clonar el repositorio, seguir instrucciones, desplegar una versión de laboratorio y verificar evidencias. La IA generada se evalúa por utilidad, trazabilidad, validación y seguridad, no por volumen.

---

## 7. Metodología, evaluación y ruta de aprendizaje

### 7.1 Metodología

Activa, incremental y centrada en evidencia. Secuencia de clase: contexto → demostración → práctica guiada → práctica semiabierta → documentación → revisión técnica → retroalimentación.

- **Aprendizaje basado en proyectos:** el caso integrador se plantea desde la primera semana; cada módulo añade una capa.
- **Laboratorios reproducibles:** guías con prerrequisitos, arquitectura, comandos, criterios de éxito, evidencias, fallas inducidas y restauración. Reproducir en otra estación es parte de la evaluación.
- **Pair engineering y revisión por pares:** roles alternados (developer, platform engineer, security reviewer, observability engineer, ML engineer); los pull requests son espacios de argumentación técnica.
- **IA como copiloto supervisado:** permitida para explicación, código, pruebas, documentación y análisis, con evidencia de validación.
- **Aprendizaje híbrido:** presencial para red, clúster, GPU y trabajo colaborativo; virtual para lecturas, videos breves, bitácoras, quizzes, preparación de imágenes/modelos, seguimiento y soporte. Materiales esenciales descargables para conectividad limitada.
- **Evaluación auténtica:** entregables operacionales, defensa de decisiones, análisis de fallas y capacidad de reconstruir el entorno.

### 7.2 Evaluación del aprendizaje

| Componente | Peso |
|---|---:|
| Módulo 1. Fundamentos Cloud Native y contenedores | 10 % |
| Módulo 2. Kubernetes, GitOps y Platform Engineering | 15 % |
| Módulo 3. DevSecOps y cadena de suministro | 15 % |
| Módulo 4. IaC, observabilidad y SRE | 10 % |
| Módulo 5. MLOps, LLMOps e IA local | 15 % |
| Módulo 6. IA multimodal local | 15 % |
| Proyecto integrador CloudForge AI | 20 % |
| **Total** | **100 %** |

**Técnicas sugeridas:** quices breves; repositorios Git con rúbrica; informes de laboratorio con evidencias; pull requests con revisión por pares; demostraciones de despliegue y rollback; checklists de seguridad y trazabilidad; dashboards y runbooks; fichas de evaluación de modelos y RAG; bitácoras de uso y validación de IA; demo day y sustentación.

**Rúbrica resumida del proyecto integrador**

| Criterio | Peso |
|---|---:|
| Arquitectura, requisitos y decisiones técnicas | 10 % |
| Plataforma Kubernetes, GitOps e Infrastructure as Code | 20 % |
| DevSecOps y cadena de suministro | 15 % |
| Observabilidad, SLI/SLO y operación | 10 % |
| MLOps/LLMOps y reproducibilidad | 15 % |
| IA local y componente multimodal | 15 % |
| Documentación, privacidad, sostenibilidad y sustentación | 15 % |
| **Total** | **100 %** |

### 7.3 Plan semanal sugerido (10 semanas)

| Sem. | Bloque | Actividades centrales |
|---:|---|---|
| 1 | Fundamentos cloud native | Linux, Git, Docker, Compose, registry, asistente local de código |
| 2 | Kubernetes I | Clúster local, pods, deployments, services, configuración, storage |
| 3 | Kubernetes II y plataforma | Ingress, RBAC, Helm, GitOps, Argo CD, catálogo de servicios |
| 4 | DevSecOps | CI/CD, testing, Trivy, SBOM, firma, SLSA, secretos y políticas |
| 5 | IaC y observabilidad | OpenTofu, OpenTelemetry, Prometheus/Grafana/Loki, SLI/SLO |
| 6 | MLOps | MLflow, registro de modelos, empaquetado, serving, Kubernetes para IA |
| 7 | LLMOps local | GPT4All, Ollama, AnythingLLM, Open WebUI, embeddings, RAG, evaluación |
| 8 | IA multimodal I | Stability Matrix, ComfyUI, texto/código e imagen como servicios |
| 9 | IA multimodal II | Video, 2D→3D, Blender, colas, artefactos, nodo GPU compartido |
| 10 | Integración y cierre | Pruebas, recuperación, auditoría técnica, demo day y sustentación |

Adaptable a 8 o 12 semanas sin alterar los resultados de aprendizaje. Para cohortes con estudiantes que trabajan: una jornada presencial intensiva semanal más actividades virtuales. Los laboratorios GPU deben programarse con reservas o colas.

---

## 8. Recursos, talento docente y condiciones de implementación

### 8.1 Arquitectura de laboratorio (por capas)

- **Capa personal:** desarrollo, contenedores y modelos pequeños.
- **Capa compartida:** clústeres, registros, observabilidad y servicios de plataforma.
- **Capa GPU:** cargas generativas pesadas.

**Dotación mínima funcional**

- 25 estaciones: CPU de 4+ núcleos, virtualización habilitada, SSD, mínimo 16 GB RAM (recomendado 24-32 GB).
- GPU NVIDIA RTX 3050 o equivalente en las estaciones disponibles (no es requisito universal).
- Un nodo compartido para clúster, registro, almacenamiento y observabilidad (servidor, workstation reutilizada o conjunto de equipos).
- Almacenamiento de red o NAS para imágenes, modelos, datasets sintéticos, artefactos, backups y outputs.
- Red de laboratorio segmentada respecto de servicios institucionales productivos.
- Internet para descarga inicial y actualización controlada; módulos esenciales operables sin conexión.
- UPS o apagado controlado para el nodo compartido.
- Raspberry Pi 4/5 opcionales (edge, k3s, observabilidad ligera, nodos ARM).

**Dotación ideal**

- Uno o más nodos GPU con memoria suficiente para video, 3D y serving concurrente, como recurso compartido.
- Servidor de virtualización para nodos Kubernetes efímeros.
- Registro OCI interno con control de acceso y retención.
- Object storage compatible con S3.
- Servidor Git/CI local o runners dedicados.
- Monitoreo centralizado de CPU, RAM, GPU, almacenamiento y red.

### 8.2 Software y plataformas recomendadas

| Área | Herramientas de referencia | Ubicación típica |
|---|---|---|
| Base de desarrollo | Linux, Windows/WSL2, Git, VS Code, Python, Node.js | Estaciones personales |
| Contenedores | Docker Engine/Desktop o Podman; Docker Compose | Todas |
| Kubernetes local | kind, minikube, k3d o equivalente | Todas |
| Kubernetes compartido | k3s, kubeadm o distribución institucional | Nodo compartido |
| Paquetización y despliegue | Helm, Kustomize, Argo CD | Clúster |
| Platform Engineering | Backstage o diseño equivalente de portal/catálogo | Clúster o demostración |
| Infrastructure as Code | OpenTofu y, cuando aplique, Terraform-compatible tooling | Todas |
| DevSecOps | Trivy, SBOM tooling, Sigstore/Cosign, SLSA controls | CI/CD |
| Observabilidad | OpenTelemetry, Prometheus, Grafana, Loki/Tempo o equivalentes | Clúster |
| MLOps | MLflow; Kubeflow por componentes según capacidad | Clúster/nodo compartido |
| LLM/SLM local | GPT4All, Ollama, LM Studio opcional | Estación o servidor |
| RAG y frontend | AnythingLLM, Open WebUI | Estación o servidor |
| Imagen generativa | Stability Matrix, ComfyUI y modelos compatibles | GPU local/compartida |
| Video generativo | Wan2.2 o modelos abiertos equivalentes | GPU compartida |
| 2D a 3D | Hunyuan3D-2.1 o equivalente; Blender para postproceso | GPU compartida/estación |
| Documentación | Markdown, MkDocs/TechDocs, diagramas como código | Todas |

Las marcas son referencias para el diseño 2026. Antes de cada cohorte, el comité académico revisa versiones, licencias, mantenimiento, compatibilidad de hardware y seguridad. Las competencias se formulan de manera independiente del proveedor.

### 8.3 Estrategia para IA local y hardware heterogéneo

Basada en **degradación elegante**: un estudiante con estación básica completa contenedización, Kubernetes local, GitOps, DevSecOps, observabilidad, RAG y LLM cuantizado; lo que supere su hardware va a un nodo compartido. Las tres rutas (A, B, C) están en la Figura 2 (sección 6).

### 8.4 Ambientes de aprendizaje

- Laboratorio de sistemas (contenedores, clústeres locales, desarrollo).
- Laboratorio de redes (conectividad, ingress, DNS, políticas, troubleshooting).
- Laboratorio GPU o nodo compartido para IA multimodal.
- Aula para revisión arquitectónica, incident response tabletop y sustentaciones.
- LMS institucional para guías, rúbricas, repositorios de evidencia y seguimiento.
- Repositorio de imágenes, modelos y paquetes predescargados.

### 8.5 Perfil del talento docente

Equipo coordinado por Ingeniería de Sistemas, con perfiles especializados:

- Coordinador académico (arquitectura de software, cloud native, DevOps o sistemas distribuidos).
- Docente de Kubernetes/Platform Engineering (clústeres, redes, almacenamiento, GitOps).
- Docente de DevSecOps (CI/CD, seguridad de software, contenedores, cadena de suministro).
- Docente de observabilidad/SRE.
- Docente de MLOps/IA (Python, MLflow/Kubeflow, modelos locales, RAG, evaluación).
- Docente o invitado de IA generativa multimodal (ComfyUI, video, 3D).
- Monitor de laboratorio para cohortes de más de 25 participantes.

### 8.6 Guías de laboratorio sugeridas (20)

1. Entorno reproducible de desarrollo con Git, Docker y Compose.
2. Construcción, optimización y escaneo de una imagen de contenedor.
3. Clúster Kubernetes local y despliegue de una API.
4. Configuración, secretos, storage, ingress y health checks.
5. Helm/Kustomize y promoción entre ambientes.
6. GitOps con Argo CD y recuperación de drift.
7. Portal o catálogo de servicios con Backstage o prototipo equivalente.
8. Pipeline CI/CD con pruebas, Trivy y SBOM.
9. Firma y verificación de artefactos con Sigstore/Cosign.
10. Infraestructura como código con OpenTofu.
11. Instrumentación con OpenTelemetry y dashboard de SLI/SLO.
12. MLflow: tracking, registro y serving de un modelo.
13. LLM local con GPT4All/Ollama y API.
14. RAG local con AnythingLLM u Open WebUI.
15. Workflow de imagen con Stability Matrix y ComfyUI.
16. Job asíncrono de video generativo.
17. Conversión de imagen a activo 3D y postproceso en Blender.
18. Integración multimodal detrás de un gateway/API.
19. Prueba de recuperación del proyecto final.
20. Demo day con auditoría de reproducibilidad.

---

## 9. Recomendaciones para implementación

- **Gobierno del laboratorio:** repositorio institucional de plantillas y versión congelada de imágenes, charts y modelos; ventana de actualización previa al inicio y manifiesto de versiones durante las diez semanas.
- **Seguridad y aislamiento:** sin credenciales ni secretos compartidos con infraestructura productiva; cuentas de laboratorio, registries separados, datos sintéticos, segmentación; credenciales temporales revocadas al cierre; experimentos de seguridad solo en repositorios y entornos autorizados.
- **Gestión de modelos y licencias:** ficha por modelo (origen, licencia, tamaño, fecha de descarga, hash, restricciones de uso, hardware recomendado).
- **Protección de datos y privacidad:** no cargar datos personales reales a modelos, índices vectoriales o repositorios de práctica sin autorización institucional expresa; usar datos sintéticos, anonimizados o públicos. Marco: Ley 1581 de 2012 y lineamientos de MinTIC.
- **Integridad académica en el uso de IA:** el uso se gobierna, no se prohíbe. En código, defender la lógica y ejecutar pruebas; en contenido visual, registrar modelo y workflow; en RAG, identificar fuentes; en infraestructura, justificar recursos y permisos. No poder explicar un artefacto generado por IA es una debilidad técnica aunque funcione.
- **Continuidad sin Internet:** kit offline por cohorte (imágenes OCI, binarios, paquetes Python/Node críticos, charts Helm, modelos cuantizados pequeños, documentación básica, datasets sintéticos); el nodo compartido actúa como mirror de registro y repositorio.
- **Gobierno académico:** sílabo oficial y matriz de resultados de aprendizaje; cronograma de laboratorios con requisitos de hardware; repositorio de plantillas; banco de rúbricas; checklist de reproducibilidad; ficha de licencias y modelos permitidos; política de uso aceptable de IA, datos y GPU; procedimiento de respaldo y restauración del clúster; formato de informe de incidente; acta de cierre de cohorte.

---

## 10. Cumplimiento normativo y alineación con estándares

| Norma, política o referente | Integración curricular |
|---|---|
| Ley 30 de 1992 | Autonomía universitaria y función de extensión/educación continuada |
| Ley 1581 de 2012 | Protección de datos personales en datasets, RAG, logs, prompts y sistemas de IA |
| CONPES 4144 de 2025 | Política Nacional de IA: infraestructura, talento, riesgos, adopción ética y territorial |
| MSPI - lineamientos IA 2026 | Seguridad y privacidad de sistemas de IA; gestión de riesgos, monitoreo y salvaguardas |
| NIST SP 800-218 SSDF | Prácticas de desarrollo de software seguro integrables al SDLC |
| NIST AI RMF 1.0 / GenAI Profile | Gobernanza y gestión de riesgos de IA generativa |
| SLSA v1.2 | Garantías progresivas para procedencia e integridad de artefactos |
| Sigstore/Cosign | Firma y verificación de imágenes, binarios, SBOM y otros artefactos |
| ISO/IEC 27001:2022 | Gestión de seguridad de la información y enfoque de riesgo |
| ISO/IEC 42001:2023 | Sistema de gestión para desarrollo y uso responsable de IA |
| ISO/IEC 25010:2023 | Modelo de calidad del producto |
| Kubernetes production guidance | Resiliencia, disponibilidad, acceso, capacidad y operación de clústeres |
| OpenTelemetry | Telemetría interoperable para métricas, logs y trazas |

- **CONPES 4144:** ejes de gobernanza, infraestructura tecnológica, I+D+i, capacidades y talento, prevención de riesgos y adopción ética. El diplomado se articula con infraestructura, talento digital y adopción segura en territorios.
- **Protección de datos (Ley 1581):** minimización, selección de datasets, anonimización, control de accesos, retención, tratamiento de logs y revisión del contenido que entra a RAG o prompts. La ejecución local no exime de controles de acceso, seguridad del endpoint, cifrado, respaldo ni gobernanza.
- **NIST SSDF / Secure by Design:** preparación de la organización, protección del software, producción segura y respuesta a vulnerabilidades; la seguridad es propiedad del proceso.
- **SLSA, SBOM y firma:** no se busca certificar un nivel SLSA, sino demostrar qué commit produjo una imagen, qué pipeline la construyó, qué dependencias contiene y cómo verificar que no fue sustituida.
- **ISO 27001 / 42001 / 25010:** referencias para conectar decisiones técnicas con calidad, riesgo, responsabilidad y mejora continua, sin formar auditores líderes en 120 horas.

---

## 11. Anexos técnicos

### 11.1 Arquitectura de referencia del proyecto

Siete dominios: repositorio y control de cambios; pipeline CI/CD; registro OCI; clúster Kubernetes; observabilidad; MLOps/LLMOps; servicios locales de IA. Debe degradarse sin GPU: el gateway mantiene la misma interfaz y redirige trabajos pesados al nodo compartido.

| Dominio | Componentes | Propósito |
|---|---|---|
| Código | Git + pull requests + pruebas | Trazabilidad y colaboración |
| Entrega | CI/CD + Trivy + SBOM + firma | Calidad y cadena de suministro |
| Artefactos | Registro OCI + object storage | Distribución y persistencia |
| Ejecución | Kubernetes + Helm/Kustomize | Orquestación y configuración |
| Plataforma | Argo CD + Backstage | GitOps y experiencia de desarrollador |
| Operación | OpenTelemetry + métricas/logs/trazas | Observabilidad y SRE |
| IA | MLflow/Kubeflow + Ollama/GPT4All + ComfyUI | MLOps/LLMOps y multimodalidad |

### 11.2 Ejemplo de Dockerfile académico

Punto de partida para discutir imágenes mínimas, dependencias, usuario de ejecución, caché y pruebas. No es una plantilla universal.

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 11.3 Ejemplo mínimo de despliegue Kubernetes

Deployment para discutir réplicas y límites de recursos.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cloudforge-api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: cloudforge-api
  template:
    metadata:
      labels:
        app: cloudforge-api
    spec:
      containers:
        - name: api
          image: registry.local/cloudforge/api:1.0.0
          ports:
            - containerPort: 8000
          resources:
            requests:
              cpu: "100m"
              memory: "128Mi"
            limits:
              cpu: "500m"
              memory: "512Mi"
```

### 11.4 Ejemplo de consumo de un modelo local mediante API

Cliente Python para un servidor local compatible con la API de Ollama. La respuesta debe validarse antes de incorporarse a un repositorio.

```python
import requests

payload = {
    "model": "modelo-local",
    "prompt": "Proponga pruebas unitarias para esta función y explique sus supuestos.",
    "stream": False
}
response = requests.post(
    "http://ollama.local:11434/api/generate",
    json=payload,
    timeout=120
)
print(response.json().get("response", ""))
```

### 11.5 Estructura sugerida del repositorio final

```text
cloudforge-project/
├── app/
├── tests/
├── Dockerfile
├── compose.yaml
├── deploy/
│   ├── base/
│   ├── overlays/
│   └── helm/
├── platform/
│   ├── argocd/
│   └── observability/
├── infra/
│   └── opentofu/
├── ml/
│   ├── experiments/
│   └── serving/
├── ai-workflows/
│   ├── rag/
│   ├── image/
│   ├── video/
│   └── image-to-3d/
├── docs/
├── runbooks/
└── README.md
```

### 11.6 Matriz mínima de evidencias por equipo

| Dimensión | Criterio | Evidencia |
|---|---|---|
| Reproducibilidad | Clone limpio + instrucciones + despliegue exitoso | README, scripts y captura/registro |
| Seguridad | Escaneo y tratamiento de hallazgos | Reporte Trivy/SBOM/firma |
| GitOps | Estado deseado desde Git | Aplicación Argo CD sincronizada |
| Observabilidad | Señales útiles | Dashboard, logs o trazas |
| MLOps | Modelo/experimento identificado | MLflow o evidencia equivalente |
| LLMOps local | RAG o modelo local funcional | Preguntas de evaluación y resultados |
| Multimodal | Imagen, video, audio o 3D integrado | Workflow + artefacto + API/job |
| Privacidad/licencia | Riesgos y condiciones documentados | Ficha técnica |
| Operación | Procedimiento de falla y recuperación | Runbook probado |

---

## Notas de la extracción

- El PDF cita fuentes en el texto (CNCF 2026, NIST 2022/2024a, SLSA 2026, DNP 2025, Ministerio TIC 2026, etc.), pero **no incluye lista de referencias bibliográficas**.
- La numeración de secciones fue reorganizada respecto del original (por ejemplo, el original numera la justificación como 2 y la estructura curricular como 5); el contenido es el mismo.
- Las dos figuras del PDF (arquitectura en capas y rutas de laboratorio) se transcribieron como tablas.

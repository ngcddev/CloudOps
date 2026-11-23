<!-- Sección 27 · Glosario técnico. verificar.py comprueba que estén los 19 términos exigidos por el contexto de entrega. Los términos para el cliente están en docs/glosario.md (otro público). -->

# Glosario

El glosario reúne los términos técnicos que usa este informe, con su significado general y, cuando importa, cómo se aplican en el proyecto. Los términos para clientes, que deben evitar la jerga, están en `docs/glosario.md` y se usan en el portal y en los mensajes al cliente.

::: {custom-style="Table Caption"}
**Tabla {T:glosario}**\
*Glosario de términos técnicos*
:::

| Término | Definición |
|-------------|--------------------------------------------------------|
| ADR (registro de decisión de arquitectura) | Documento corto que registra una decisión de arquitectura con su contexto, alternativas y consecuencias. El informe tiene 28 (sección de decisiones de arquitectura). |
| Alertmanager | Componente de Prometheus que agrupa y enruta las alertas. En el proyecto manda las alertas de los sitios al webhook del Hub, que abre el incidente. |
| Argo CD | Herramienta de entrega continua declarativa para Kubernetes: compara lo que dice Git con lo que corre y lo sincroniza. |
| Cloud native | Forma de construir y operar software pensada para la nube: contenedores, servicios pequeños, configuración declarativa, automatización y observabilidad. |
| Compuerta (del asistente) | Clasificador propio (Naive Bayes) que decide si una pregunta trata del Hub antes de llamar al modelo de lenguaje. |
| DevSecOps | Práctica que integra la seguridad en todo el ciclo de desarrollo y operación en lugar de revisarla al final. En el proyecto es la puerta de seguridad de la entrega. |
| Deriva (drift) | Diferencia entre el estado declarado en código o Git y el estado real. Argo CD la corrige con `selfHeal`; OpenTofu la detecta con `plan -detailed-exitcode`. |
| Embedding (incrustación) | Vector de números que representa el significado de un texto, de modo que textos parecidos quedan cerca. El RAG usa vectores de 768 dimensiones. |
| Error budget (presupuesto de error) | Margen de indisponibilidad que permite un SLO: uno menos el objetivo. Si el SLO es 99,9 %, el margen es 0,1 %. |
| GitOps | Modelo de operación en el que Git es la fuente de la verdad del estado deseado y un agente (Argo CD) lo aplica y lo mantiene. |
| Hub | CloudOps Client Hub, el producto: centro de operación de servicios digitales para agencias web. |
| IaC (infraestructura como código) | Describir la infraestructura en archivos versionados que una herramienta aplica de forma repetible. En el proyecto, OpenTofu. |
| Incidente | Falla que afecta un servicio. Se abre automáticamente desde una alerta o a mano, tiene prioridad P1 a P4 y su SLA corre con hora real. |
| Índice vectorial | Estructura que guarda embeddings y permite buscar los más parecidos a una consulta. En el proyecto es una tabla de PostgreSQL con coseno calculado en Python (ADR-20). |
| Inyección de instrucciones (prompt injection) | Ataque que esconde órdenes en la entrada o en el contexto de un modelo de lenguaje para que las obedezca en lugar de las reglas del sistema. |
| Kubernetes | Plataforma de orquestación de contenedores. El proyecto usa k3s (una distribución ligera) dentro de Docker con k3d. |
| LLM (modelo de lenguaje grande) | Modelo de aprendizaje automático entrenado con grandes cantidades de texto que genera lenguaje. Aquí, Qwen2.5 7B Instruct. |
| LLMOps | Prácticas para operar aplicaciones con LLM: versionar instrucciones y modelos, evaluar, monitorear y proteger. |
| MLOps | Prácticas para llevar modelos de aprendizaje automático a producción de forma reproducible: registro, versionado, evaluación, despliegue y monitoreo. |
| MTTR (tiempo medio de recuperación) | Promedio del tiempo entre el inicio de una falla y la recuperación del servicio. En el caso del restaurante se midió de 1,3 a 1,5 minutos. |
| Namespace (espacio de nombres) | Partición lógica de Kubernetes. Cada cliente tiene el suyo, con cuota y políticas de red. |
| NetworkPolicy | Regla de Kubernetes que limita qué tráfico puede entrar o salir de un Pod. El proyecto deniega todo por defecto. |
| Observabilidad | Capacidad de entender el estado interno de un sistema a partir de sus señales: métricas, registros y trazas. |
| P1 a P4 | Prioridades de una solicitud o incidente según impacto y urgencia. P1 es la más alta: respuesta en 15 minutos y solución en 4 horas. |
| Pod Security `restricted` | Perfil más estricto de las normas de seguridad de Pods de Kubernetes: sin root, sin capacidades extra y sin escalada de privilegios. |
| PyME | Pequeña y mediana empresa; los clientes de las agencias. |
| RAG (generación aumentada por recuperación) | Técnica en la que, antes de generar, se recuperan fragmentos relevantes de una base de conocimiento y se entregan al modelo como contexto. |
| Rollback | Volver a una versión anterior estable. En el proyecto es un commit que restaura la etiqueta de imagen anterior y que Argo CD aplica. |
| Runbook | Procedimiento de operación para una situación concreta: síntoma, diagnóstico, acción, verificación y cuándo escalar. |
| SBOM (lista de materiales de software) | Inventario de los componentes de una imagen o aplicación. Syft lo genera en formato SPDX. |
| SLA (acuerdo de nivel de servicio) | Compromiso con el cliente de tiempos de respuesta y de solución por prioridad. |
| SLI (indicador de nivel de servicio) | Medida de lo que percibe el usuario, por ejemplo la proporción de sondeos exitosos de un sitio. |
| SLM (modelo de lenguaje pequeño) | Modelo de lenguaje de pocos miles de millones de parámetros o menos, que cabe en hardware modesto. Qwen2.5 3B se usó como modelo pequeño de comparación. |
| SLO (objetivo de nivel de servicio) | Meta para un SLI en un periodo, por ejemplo disponibilidad mensual de 99,9 % en el plan Premium. |
| SLSA | Marco de niveles de garantía para la cadena de suministro de software. El proyecto genera y verifica atestaciones de procedencia, sin declarar un nivel. |
| Puerta de seguridad | Conjunto de controles que corre antes de publicar una versión: secretos, pruebas, vulnerabilidades, SBOM, firma y verificación. |
| `selfHeal` | Opción de Argo CD que revierte los cambios hechos a mano en el clúster para volver a lo que dice Git. |
| VEX | Documento que indica si una vulnerabilidad conocida afecta o no a un producto. La puerta genera uno en formato OpenVEX. |

::: {custom-style="Nota"}
*Nota.* Elaboración propia. Las definiciones generales siguen el uso común de la disciplina; las cifras y decisiones corresponden a este proyecto.
:::

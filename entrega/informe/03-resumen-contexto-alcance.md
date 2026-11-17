<!-- Secciones 3 a 7 · Resumen ejecutivo, contexto, alcance, marco normativo y partes interesadas. Fuente: HECHOS.md §3–§7 y RESUMEN.md de la corrida. -->

# Resumen ejecutivo

**Problema.** Una agencia web pequeña que opera los sitios de varias pymes recibe pedidos por chat y correo, publica cambios a mano, se entera de las caídas por el propio cliente y responde sin datos. No tiene un lugar único para pedir cambios, publicarlos con control, detectar fallas y explicarle al cliente qué pasó. [COMPLETAR: confirmar el problema con la entrevista a la empresa de software del Cauca.]

**Solución.** CloudOps Client Hub es un centro de operación con dos caras: una consola para la agencia y un portal para el cliente. Cada cambio se pide en el Hub, otra persona lo aprueba y se publica por GitOps solo si la versión pasó una puerta de seguridad. Si un sitio cae, el monitoreo abre solo un incidente P1 con su plan de rollback. Los tableros comparan la disponibilidad con el SLO de cada plan. Un asistente de IA local, también por voz, ayuda al técnico sin que los datos salgan del equipo.

**Beneficiarios.** Los técnicos y el dueño de la agencia, que operan con menos riesgo y con datos; las pymes clientes, que ven el estado de su sitio y reciben mensajes claros; y los visitantes de los sitios, que tienen un servicio más disponible.

**Resultados principales.** Todo se midió en una corrida reproducible del 16 y 17 de noviembre de 2026:

- **83 verificaciones automáticas:** 80 pasan y las 3 que fallan son hallazgos del proyecto que se documentan (sección de riesgos).
- **Pruebas del backend:** 1.132 pasan, sin fallos, en el modo del CI.
- **Caída de un sitio:** abre el incidente P1 en 48 a 49 s, frente a un objetivo de 60 s o menos. El servicio se recupera con rollback con un MTTR de 3,4 min.
- **Asistente:** acierta el 95 % (contexto completo) y el 92,5 % (RAG) en preguntas de ayuda, y el 100 % en preguntas ciegas. Resiste 9 de 10 intentos de inyección de prompts.
- **Voz:** transcribe con un error de palabras del 5,8 %.
- **Reproducibilidad:** un clon limpio del repositorio arranca y pasa sus pruebas.

**Valor de cloud native y de la IA local.** El estado del sistema vive en Git y Argo CD lo aplica: un cambio hecho a mano en el clúster se revierte solo en 2 s y un rollback es un `git revert`. La IA corre localmente con un modelo de licencia Apache 2.0, de modo que ningún dato de clientes va a servicios externos.

**Recomendaciones.**

1. Corregir el hallazgo H-IAC-01 antes de usar OpenTofu con clientes reales.
2. Redactar también la salida del modelo (H-IA-01).
3. Rediseñar la demo de tableros para que provoque la falla por Git.
4. Proteger la rama `dev` del repositorio.

# Contexto

## Problema y situación actual

[COMPLETAR: problema concreto de la organización o sector del Cauca, a partir de la entrevista con la empresa de software de un integrante: tamaño, cómo atiende hoy los pedidos y las caídas, qué le cuesta.] El caso de estudio que usa el sistema es la agencia ficticia Forja Digital, con dos técnicos y tres clientes pyme de Popayán en planes de distinta exigencia (Tabla {T:planes}).

::: {custom-style="Table Caption"}
**Tabla {T:planes}**\
*Planes de servicio del caso de estudio*
:::

| Plan | Cliente | Objetivo de disponibilidad (SLO) | Precio mensual (COP) |
|---|---|---|---|
| Básico | Consultorio Dental Popayán | 99,0 % | 150.000 |
| Estándar | Ferretería El Tornillo | 99,5 % | 350.000 |
| Premium | Restaurante La Sazón | 99,9 % | 700.000 |

*Nota.* Valores sintéticos de `seed/plans.json` y `constitution/canonical-names.md`.

## Por qué cloud native y por qué IA local

Un enfoque cloud native permite declarar en Git el estado deseado de cada sitio y dejar que Argo CD lo mantenga. La publicación, la auditoría y la recuperación se vuelven operaciones sobre un historial verificable, no acciones manuales sobre servidores. La IA local (Ollama con Qwen2.5 7B-Instruct) asiste al técnico con la ayuda del propio Hub y redacta borradores de mensajes sin enviar datos de clientes a terceros, en coherencia con la Ley 1581 de 2012 (Congreso de Colombia, 2012).

## Objetivos

[AUDITAR CON PERPLEXITY: objetivos derivados del producto construido.]

**Objetivo general.** Construir y operar, en un laboratorio reproducible, una plataforma cloud native que permita a una agencia pequeña publicar, vigilar y recuperar los sitios de sus clientes con controles de seguridad verificables y un asistente de IA local.

**Objetivos específicos.**

1. Publicar cambios por GitOps con aprobación de una segunda persona.
2. Impedir la publicación de versiones inseguras con una puerta de seguridad: secretos, vulnerabilidades, SBOM, firma y procedencia.
3. Detectar caídas y abrir incidentes P1 en 60 s o menos, con rollback guiado.
4. Medir la disponibilidad de cada sitio contra el SLO de su plan.
5. Asistir al técnico con IA local evaluada contra alucinación, inyección y exfiltración.
6. Documentar la operación con runbooks ensayados.

# Alcance

## Construido

El alcance construido cubre los siete módulos del diplomado (Tabla {T:alcance}). Cada ítem remite a su requisito (secciones de requerimientos) y a su verificación.

::: {custom-style="Table Caption"}
**Tabla {T:alcance}**\
*Alcance construido por módulo y su verificación*
:::

| Módulo | Componente | Verificación (corrida) |
|---|---|---|
| 1 Contenedores | Imágenes multi-stage sin root; la imagen de producción de la API no incluye herramientas de prueba | A13 a A16 |
| 2 Kubernetes | k3s v1.32.9 en k3d, Pod Security `restricted`, NetworkPolicies, HPA y cuotas | C06 a C14, C28 |
| 3 GitOps y DevSecOps | Argo CD 2.13.3 con selfHeal; CI de 5 trabajos; puerta de seguridad con Gitleaks, Trivy, Syft y Cosign | C01, C20, B06, C23 |
| 4 IaC y observabilidad | OpenTofu 1.13.2; Prometheus, Alertmanager, Grafana, Loki, Tempo y Blackbox; 11 alertas y SLO con burn rate | A04 a A06, A10, C16 |
| 5 MLOps y LLMOps | MLflow 3.18.0 en el clúster; compuerta registrada con alias; fichas de modelo; evaluación del asistente | D01 a D07 |
| 6 Multimodal | Voz del asistente: faster-whisper `small` y Piper, en CPU | D11, D12 |
| 7 Integración | Demos de punta a punta, runbooks ensayados y clon reproducible | Niveles C, F y Z |

*Nota.* Los identificadores remiten a `entrega/evidencias/2026-11-16_bb5a284/RESUMEN.md`.

## Fuera de alcance

- **Generación de imagen, video y 2D→3D (ComfyUI):** su consumo de cómputo no cabe en el equipo disponible, una laptop con una GPU de 8 GB que ya ocupan el modelo de 7B (4.535 MiB) y el de embeddings. El componente multimodal es la voz, que corre en CPU.
- **Despliegue en la nube:** queda como trabajo futuro. [COMPLETAR si se despliega en GCP o Azure antes de la entrega.]
- **Datos reales:** usuarios y clientes reales, pagos, dominios públicos y multiagencia. Todos los datos son sintéticos.

# Marco normativo

El proyecto toma de cada norma un control que se puede verificar (Tabla {T:normas}).

::: {custom-style="Table Caption"}
**Tabla {T:normas}**\
*Normas aplicables y control que las demuestra*
:::

| Norma | Cómo afecta al proyecto | Control verificable |
|---|---|---|
| Ley 1581 de 2012 (Congreso de Colombia, 2012) | Tratamiento de datos personales: solo datos sintéticos, mínimo acceso y redacción antes de guardar o enviar a la IA | Redacción de secretos y datos (D05); cada cliente ve solo lo suyo (B07) |
| CONPES 4144 de 2025 (Departamento Nacional de Planeación [DNP], 2025) | IA confiable y supervisada | Los borradores de IA se aprueban a mano (D03) |
| Lineamientos de seguridad y privacidad (Ministerio de Tecnologías de la Información y las Comunicaciones [MinTIC], s. f.) | Gestión de accesos, trazabilidad y protección de la información | Roles, bitácora sin borrado (B07), HTTPS en el Hub, secretos fuera del repositorio |
| NIST SP 800-218 SSDF (Souppaya et al., 2022) | Desarrollo seguro: verificar dependencias, secretos y configuración | Puerta con 9 escenarios (B06); análisis estático (A11, A12) |
| SLSA v1.2 (Open Source Security Foundation [OpenSSF], s. f.) | Procedencia verificable de los artefactos | Procedencia firmada con Cosign y verificada antes de publicar (B06, C23) |
| ISO/IEC 27001:2022 (International Organization for Standardization [ISO], 2022) | Controles de seguridad de la información | Segregación de funciones, mínimo privilegio, respaldo fuera del nodo (C22, C05, C29) |
| ISO/IEC 42001:2023 (ISO, 2023a) | Gestión de sistemas de IA | Ficha por modelo, integridad por digest, evaluación y promoción con rollback (D01, B04) |
| ISO/IEC 25010:2023 (ISO, 2023b) | Modelo de calidad del producto | Requerimientos no funcionales medidos (sección correspondiente) |

# Partes interesadas

[AUDITAR CON PERPLEXITY: partes interesadas derivadas de los actores reales del sistema.]

::: {custom-style="Table Caption"}
**Tabla {T:partes}**\
*Partes interesadas*
:::

| Parte interesada | Rol | Interés | Influencia | Forma de participación |
|---|---|---|---|---|
| Técnicos de la agencia | Operan la consola, aprueban cambios y atienden incidentes | Publicar sin riesgo y recuperar rápido | Alta | Usuarios del rol agencia |
| Dueño de la agencia | Define planes, precios y SLA | Rentabilidad y reputación | Alta | Tableros de KPI y costo por cliente |
| Clientes pyme | Piden cambios y consultan su sitio | Disponibilidad y comunicación clara | Media | Portal del cliente |
| Visitantes de los sitios | Usan el sitio de la pyme | Que el sitio funcione | Baja (indirecta) | Medidos por los sondeos de disponibilidad |
| Titulares de datos | Personas cuyos datos tratarían los sitios | Privacidad | Media (regulatoria) | Protegidos por datos sintéticos y redacción |
| Equipo del proyecto | Diseña, construye y opera | Aprobar el diplomado con un producto verificable | Alta | Desarrollo por especificaciones |
| Docente y jurado | Evalúan | Verificar las evidencias | Alta | Paquete de evidencias y laboratorio reproducible |

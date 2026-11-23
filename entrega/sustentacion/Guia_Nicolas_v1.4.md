<!-- Guía de Nicolás para la sustentación del 30 nov 2026: por diapositiva, guion hablado, puntos obligatorios en orden y preguntas probables con respuesta corta. Se basa en las notas del orador, el banco de preguntas y las evidencias del informe 00. -->

# Guía de Nicolás · CloudOps Hub

Cubre las 18 diapositivas de Nicolás: 6 a 18, 41 a 43, 47 y 48. Tiempo total: 7,0 min más la demo.

Cómo usar cada diapositiva:
- **Guion:** lo que se dice, en voz normal. Está escrito para el tiempo asignado (unas 150 palabras por minuto); léelo en voz alta una vez y quédate con las ideas, no con las palabras.
- **Lo que sí o sí se dice, en orden:** si el tiempo se acaba, estos puntos son el mínimo. Si te falta tiempo, se recorta de abajo hacia arriba.
- **Preguntas probables:** técnicas, de decisión, de negocio y «de trampa», con la respuesta corta para decirla en 30 a 45 s. Entre paréntesis va la fuente por si piden evidencia.

Reglas al hablar: Empresa A, B y C (nunca nombres reales). No se vuelve a decir «ficticio»; si preguntan de frente, se responde con la verdad (ver banco de preguntas, pregunta 1 de Andrés). Si no sabes algo, lo dices y ofreces mostrar la evidencia.

## Mapa de tiempos

| Bloque | Diapositivas | Tiempo |
|---|---|---|
| Modelo 4+1 | 6 a 11 | 1,1 min |
| C4 nivel 2 | 12 a 17 | 1,25 min |
| Decisiones de arquitectura | 18 | 0,75 min |
| MLOps, LLMOps y voz | 41 a 43 | 3,25 min |
| Cierre y paso a la demo | 47 y 48 | 0,75 min + demo |

Nota: los close-ups (7 a 11 y 13 a 17) duran entre 9 y 12 s cada uno. Se dicen de corrido, sin pausas, mientras se avanza la diapositiva.

---

# Bloque 1 · Modelo 4+1 (6 a 11)

## Diapositiva 6 · Cuatro vistas y un escenario describen la misma arquitectura (15 s)

**Guion:**
«Gracias, Andrés. Para explicar la arquitectura usamos el modelo 4+1: cuatro vistas, cada una para un público distinto, y un quinto elemento, los escenarios, que las une. Las vemos de cerca, una por una.»

**Lo que sí o sí se dice, en orden:**
1. Se llama 4+1 (Kruchten, 1995).
2. Cuatro vistas: lógica, desarrollo, procesos y física.
3. El «+1» son los escenarios: casos de uso que unen las vistas.
4. Ahora cada vista de cerca.

**Preguntas probables:**
- *De decisión:* **¿Para qué 4+1 si ya tienen C4?** Responden cosas distintas. C4 baja de nivel (contexto, contenedores, componentes); 4+1 mira el mismo sistema desde cuatro públicos. Los 16 casos de uso validan todas las vistas. (Figuras 1 a 4 del informe.)
- *Técnica:* **¿Quién creó el modelo 4+1?** Philippe Kruchten, 1995.
- *Documentación:* **¿Dónde puedo ver los diagramas completos?** En la carpeta pública de diagramas y en `docs/arquitectura/`; el archivo editable es de draw.io. [PENDIENTE: enlace público.]

## Diapositiva 7 · Vista lógica: 22 entidades con estados y prioridades (9 s)

**Guion:**
«Vista lógica: el modelo del negocio. Son 22 entidades en seis paquetes, con estados canónicos y una prioridad P1 a P4 que sale de impacto por urgencia.»

**Lo que sí o sí se dice, en orden:**
1. 22 entidades, 6 paquetes.
2. Estados canónicos (el mismo vocabulario en todo el Hub).
3. Prioridad P1 a P4 por impacto × urgencia.

**Preguntas probables:**
- *Técnica:* **¿Cuáles son los 6 paquetes?** Clientes y contratos, mesa de servicio, incidentes, puerta de seguridad, usuarios y auditoría, e IA.
- *Técnica:* **¿Cómo se calcula la prioridad?** Por reglas de impacto y urgencia, no a criterio de quien atiende; cada prioridad trae su SLA según el plan del cliente. (ADR-13; docs/proceso.md.)
- *Negocio:* **¿Por qué estados canónicos?** Porque antes cada persona nombraba distinto el mismo estado; con un vocabulario único el SLA se mide igual para todos. (Glosario.)

## Diapositiva 8 · Vista de desarrollo: un monorepo y una API en capas (9 s)

**Guion:**
«Vista de desarrollo: un solo repositorio con backend, frontend, voz, IA y los sitios. La API tiene capas: routers, servicios e integraciones. Y la plataforma también es código.»

**Lo que sí o sí se dice, en orden:**
1. Monorepo (backend, frontend, voz, ai, apps).
2. API en capas: routers → services → integrations.
3. La plataforma como código: gitops, infra, observability, pipelines.

**Preguntas probables:**
- *Decisión:* **¿Por qué un monorepo?** Un equipo de cinco, un solo lugar donde buscar y un solo PR para cambios que cruzan capas. El costo es que el CI corre todo; lo acotamos con cinco trabajos en paralelo. (ADR-01.)
- *Técnica:* **¿Por qué en capas?** Para que las reglas de negocio no dependan de cómo se habla con sistemas externos; solo las integraciones salen de la API.
- *Técnica:* **¿Dónde van las migraciones?** En `alembic`: 17 migraciones lineales que crean las 22 tablas.

## Diapositiva 9 · Escenarios: 16 casos de uso unen las cuatro vistas (9 s)

**Guion:**
«El más uno: 16 casos de uso. El que los une todos es la caída y recuperación del sitio de la Empresa A, que van a ver funcionando en la demo.»

**Lo que sí o sí se dice, en orden:**
1. 16 casos de uso (CU-01 a CU-16).
2. Caso integrador: caída y recuperación de la Empresa A.
3. Es lo que se verá en la demo.

**Preguntas probables:**
- *Técnica:* **¿Quiénes son los actores?** Agencia (administrador y técnico), cliente pyme y los sistemas automáticos (monitoreo, Argo CD, Gitea Actions).
- *Decisión:* **¿Por qué ese caso como integrador?** Recorre las cuatro vistas: crea datos, usa procesos concurrentes, toca Git y el clúster, y termina en un KPI (MTTR).
- *Trampa:* **¿Los 16 casos están probados?** Los 15 requisitos funcionales están cumplidos con prueba; la matriz de trazabilidad 02 los une con su evidencia. (02; RESUMEN.md.)

## Diapositiva 10 · Vista de procesos: sondeo, alerta y reconciliación (9 s)

**Guion:**
«Vista de procesos: lo que corre al mismo tiempo. Un sondeo cada 5 segundos, reglas que disparan alertas, un aviso al Hub y Argo CD reconciliando. Así se detecta una caída en menos de 60 segundos.»

**Lo que sí o sí se dice, en orden:**
1. Sondeo de Blackbox cada 5 s.
2. Reglas de Prometheus → webhook de Alertmanager al Hub.
3. Vigilante de despliegues cada 15 s y reconciliación de Argo CD.
4. Resultado: detección en 60 s o menos.

**Preguntas probables:**
- *Técnica:* **¿Por qué 5 s de sondeo?** Para que la caída se vea rápido y el incidente se abra en menos de 60 s; medimos 48 a 49 s en tres corridas. (C25, C26.)
- *Técnica:* **¿Y si el Hub no recibe el webhook?** La alerta sigue visible en Alertmanager y Grafana; el Hub no duplica incidentes si el aviso llega repetido.
- *Trampa:* **¿Por qué no se abre un incidente cuando un Pod muere un instante?** La alerta pide 30 s sostenidos y Kubernetes recrea el Pod en 8 s. (C28.)

## Diapositiva 11 · Vista física: un nodo k3d y Ollama en el anfitrión (9 s)

**Guion:**
«Vista física: un solo equipo con Docker Desktop, un clúster k3d de un nodo, namespaces por plataforma y por cliente, y Ollama corriendo directo en el equipo para usar la GPU.»

**Lo que sí o sí se dice, en orden:**
1. Un equipo anfitrión con Docker Desktop.
2. k3d de un nodo (k3s v1.32.9), namespaces de plataforma y uno por cliente.
3. Ollama fuera del clúster, en el anfitrión, con la GPU.

**Preguntas probables:**
- *Decisión:* **¿Por qué un solo nodo?** Porque tenemos una sola laptop; se descartó un segundo equipo (ADR-12 y ADR-13). Es un límite declarado para producción.
- *Técnica:* **¿Por qué Ollama fuera del clúster?** Para usar la GPU de 8 GB directamente, sin pasar la GPU por Docker. (ADR-13.)
- *Trampa:* **¿Esto escala a producción?** No tal cual: un nodo, certificados autofirmados y sin rotación de tokens. Lo declaramos como trabajo futuro. (06 §9.)

---

# Bloque 2 · C4 nivel 2 (12 a 17)

## Diapositiva 12 · El Hub nunca habla con Kubernetes: Git es la única puerta (15 s)

**Guion:**
«Este es el diagrama de contenedores. En azul, lo que construimos; en gris, la plataforma. La decisión clave: el Hub nunca habla con Kubernetes. Escribe en Git y Argo CD aplica. Lo recorremos de los usuarios a la IA.»

**Lo que sí o sí se dice, en orden:**
1. Azul = construido por nosotros; gris = plataforma y sistemas externos.
2. Decisión clave: el Hub nunca habla con Kubernetes.
3. Solo habla con Gitea, Argo CD y Prometheus (ADR-02 y ADR-03).
4. Cinco zonas, de los usuarios a la IA local.

**Preguntas probables:**
- *Decisión:* **¿Por qué no hablar directo con Kubernetes?** Para que Git sea la única puerta: todo queda en el historial, se revisa y se revierte con `git revert`. Además la API no tiene permisos sobre el clúster. (ADR-02; principio 5.)
- *Técnica:* **¿Qué pasa si Gitea se cae?** No se pueden publicar cambios nuevos, pero los sitios siguen sirviéndose y Argo CD mantiene el estado actual. El respaldo de Gitea se hace fuera del nodo. (C29.)
- *Técnica:* **¿Qué es C4?** Un modelo con cuatro niveles (contexto, contenedores, componentes y código); este es el nivel 2.

## Diapositiva 13 · Los usuarios entran por la consola web, que habla con la API (12 s)

**Guion:**
«Zona uno: los usuarios. Administrador, técnico y cliente entran por la misma consola web en React, con roles distintos, y la consola solo habla con la API.»

**Lo que sí o sí se dice, en orden:**
1. Tres usuarios: administrador, técnico y cliente pyme.
2. Una consola web (React): consola de agencia y portal del cliente, mismas rutas, roles distintos.
3. La consola solo habla con la API.

**Preguntas probables:**
- *Técnica:* **¿Cómo evitan que un cliente vea datos de otro?** Cada ruta exige rol y alcance por cliente; se probó que cada cliente solo ve lo suyo. (B07.)
- *Negocio:* **¿Qué ve el cliente y qué no?** Estado, disponibilidad frente a lo acordado, incidentes y solicitudes, sin jerga; no ve costo, horas ni carga por técnico. (docs/kpi.md.)

## Diapositiva 14 · La API guarda en PostgreSQL y delega la voz a un servicio (12 s)

**Guion:**
«Zona dos: la API en FastAPI tiene las reglas de negocio, guarda todo en PostgreSQL con respaldo diario, y delega la voz a un servicio aparte.»

**Lo que sí o sí se dice, en orden:**
1. API en FastAPI: reglas de negocio, SLA, cambios, incidentes, reportes y asistente.
2. PostgreSQL 16 con respaldo diario (03:00).
3. Voz como servicio aparte.

**Preguntas probables:**
- *Técnica:* **¿Cuántas réplicas tiene la API?** De 1 a 2: un HPA sube a 2 cuando se satura. (Ensayo de saturación.)
- *Técnica:* **¿Cómo comprueban que el respaldo sirve?** Se restaura y se compara tabla por tabla: las 23 tablas quedaron iguales. (B05.)
- *Decisión:* **¿Por qué la voz va aparte?** Piper es GPL-3.0; corriendo aislado por HTTP no contagia la licencia del Hub, y además se escala por separado. (06 §8.1.)

## Diapositiva 15 · Git es la única puerta: Gitea guarda y Argo CD aplica (12 s)

**Guion:**
«Zona tres: Git. El Hub escribe la versión en hub-gitops, que vive en Gitea; Argo CD la vigila y la aplica en cada cliente; y el ejecutor de Gitea corre la puerta de seguridad.»

**Lo que sí o sí se dice, en orden:**
1. El Hub escribe la versión en hub-gitops (Gitea).
2. Argo CD sincroniza Deployment, Service e Ingress de cada cliente.
3. El ejecutor de Gitea Actions corre la puerta de seguridad.

**Preguntas probables:**
- *Técnica:* **¿Cada cuánto reconcilia Argo CD?** Cada 30 s; el sitio reportó v1.1 a los 50 s del cambio. (C21.)
- *Técnica:* **¿Qué es selfHeal?** Si alguien cambia algo a mano en el clúster, Argo CD lo devuelve al estado de Git: escalar un Deployment a mano se corrigió en 2 s. (C20.)
- *Decisión:* **¿Por qué dos repositorios?** Para no depender de Internet en el laboratorio y separar el código del Hub de lo que se despliega. (ADR-03.)

## Diapositiva 16 · La observabilidad vigila cada sitio y avisa al Hub (12 s)

**Guion:**
«Zona cuatro: la observabilidad. Blackbox sondea cada sitio, Prometheus evalúa las reglas y Alertmanager avisa al Hub. Los registros van a Loki, las trazas a Tempo y todo se ve en Grafana.»

**Lo que sí o sí se dice, en orden:**
1. Blackbox sondea cada 5 s; Prometheus evalúa reglas y SLO.
2. Alertmanager avisa al Hub por webhook (SitioCaido).
3. Loki (72 h), Tempo (24 h) y Grafana.

**Preguntas probables:**
- *Técnica:* **¿Diferencia entre métricas, registros y trazas?** Métricas: números en el tiempo. Registros: eventos con texto. Trazas: el recorrido de una petición por cada etapa. (Tabla 10.)
- *Decisión:* **¿Por qué retenciones tan cortas?** Es un laboratorio de un nodo: lo que importa es poder diagnosticar un incidente reciente; las trazas no guardan el texto de las preguntas por privacidad.
- *Nota:* Los detalles de SLO y burn rate los explica Yisel; si preguntan, se puede responder y pasarle la palabra.

## Diapositiva 17 · La IA corre local y cada sitio de cliente queda aislado (12 s)

**Guion:**
«Zona cinco: la IA corre local, en el equipo, con una GPU de 8 gigas, y MLflow guarda el modelo que entrenamos. Los sitios de los clientes viven cada uno en su espacio, aislados.»

**Lo que sí o sí se dice, en orden:**
1. Ollama local con la RTX 4060 de 8 GB (ADR-13).
2. MLflow guarda el clasificador entrenado (alias production).
3. Sitios de clientes en su namespace: Pod Security restricted y NetworkPolicy.

**Preguntas probables:**
- *Decisión:* **¿Por qué IA local y no una API externa?** Privacidad (los datos de clientes no salen; Ley 1581), costo y licencia Apache 2.0. (ADR-08.)
- *Técnica:* **¿Qué es una NetworkPolicy?** Una regla de firewall dentro del clúster: por defecto se deniega todo y se abre solo lo necesario. (C07 a C12.)
- *Trampa:* **¿Qué pasa si falla la GPU?** El Hub sigue funcionando; el asistente avisa que la IA no respondió y cae a búsqueda por palabras. Cambios, incidentes y rollbacks no dependen de la IA. (F01; 05 §10.)

---

# Bloque 3 · Decisiones de arquitectura

## Diapositiva 18 · Trece decisiones registradas explican por qué el sistema es así (45 s)

**Guion:**
«Todo esto no es casualidad: lo decidimos y lo dejamos escrito, trece decisiones con contexto, alternativas y consecuencias. En plataforma: k3s en un solo nodo porque tenemos una sola laptop; GitOps con Argo CD; y OpenTofu, que quedó con un hallazgo abierto que Sebastián explica. En seguridad y operación: una puerta por versión, el SLO por plan y el respaldo fuera del nodo. En IA: un modelo local de siete mil millones de parámetros por privacidad, un RAG propio, un clasificador propio versionado en MLflow y voz en CPU. Descartamos un segundo equipo y todo corre en uno con GPU. Ahora Sebastián nos muestra cómo se construye y se despliega.»

**Lo que sí o sí se dice, en orden:**
1. 13 decisiones, cada una con contexto, alternativas, consecuencias, estado y evidencia.
2. Plataforma: k3s en k3d (ADR-01), GitOps con selfHeal (ADR-02), dos repositorios (ADR-03), OpenTofu con hallazgo abierto (ADR-04).
3. Seguridad y operación: puerta por versión (ADR-05), SLO por plan (ADR-06), respaldo fuera del nodo (ADR-07).
4. IA: Qwen2.5 7B local (ADR-08), RAG propio (ADR-09), clasificador propio en MLflow (ADR-10), voz en CPU (ADR-11).
5. Un solo equipo con GPU (ADR-12 reemplazada por ADR-13).
6. Pasa la palabra a Sebastián.

**Preguntas probables:**
- *Decisión:* **¿Qué ADR cambiarían hoy?** La ADR-04: sigue aceptada pero con el hallazgo H-IAC-01 abierto; lo primero sería importar los clientes existentes al estado de OpenTofu. (Tabla 9.)
- *Decisión:* **¿Por qué qwen2.5:7b y no uno más grande?** Cabe en 8 GB de GPU (4.535 MiB a 51,2 tokens/s con prompt corto), es Apache 2.0 y no manda datos afuera. El 3B es solo de investigación y se usa para comparar. (ADR-08; Tabla 13.)
- *Decisión:* **¿Por qué RAG propio y no pgvector?** Son 31 trozos: la similitud coseno en Python basta. El experimento híbrido dio 41 contra 42 aciertos de 43 y empeoraba el conjunto ciego. (ADR-09.)
- *Decisión:* **¿Por qué no hicieron imagen si el módulo 6 la pide?** ComfyUI necesitaba unos 5 GB de VRAM y el modelo de 7B ya ocupa la GPU; elegimos voz en CPU, que es multimodal y útil para el técnico. (ADR-11.)
- *Trampa:* **¿Qué ADR fue reemplazada?** La ADR-12 (usar un segundo equipo) quedó descartada y reemplazada por la ADR-13 (todo en un equipo con GPU).

---

# Bloque 4 · MLOps, LLMOps y voz (41 a 43)

## Diapositiva 41 · MLOps: entrenamos un clasificador propio y MLflow guarda cada versión (75 s)

**Guion:**
«Hablemos de inteligencia artificial, empezando por MLOps: el ciclo de vida de un modelo que entrenamos nosotros. Nuestro modelo es un clasificador pequeño que decide si una pregunta trata del Hub o no. Lo entrenamos con 141 preguntas etiquetadas a mano más 348 generadas con términos del Hub: 489 ejemplos. Para probarlo usamos 24 preguntas aparte que nunca ve al entrenar. El algoritmo es Naive Bayes, en Python puro: el modelo es un archivo de unos 40 kilobytes. La versión uno acertó 95,8 por ciento, no perdió ninguna pregunta del Hub y evitó llamar al modelo grande en el 91,7 por ciento de las preguntas ajenas. MLflow guarda cada versión con sus parámetros, métricas, datos y modelo; el alias production dice cuál usa el Hub, y no se promueve un candidato que empeore al actual. Y el otro lado es LLMOps.»

**Lo que sí o sí se dice, en orden:**
1. MLOps = ciclo de vida de un modelo que entrenamos nosotros.
2. Qué modelo es: un clasificador pequeño que decide si la pregunta es del Hub («compuerta» en el código).
3. Datos: 141 etiquetadas + 348 generadas = 489; prueba: 24 aparte (12 y 12).
4. Algoritmo: Naive Bayes (palabras, pares, trigramas de letras), modelo en JSON de ~40 KB con SHA-256.
5. Resultado v1 (14 nov): exactitud 95,8 % (23 de 24), 0 preguntas del Hub perdidas, 91,7 % de ajenas sin llamar al LLM.
6. MLflow 3.18: parámetros, métricas, datos y modelo por corrida; alias production.
7. Regla de promoción: no pasa si pierde una pregunta del Hub o empeora; se puede volver atrás.
8. Transición a LLMOps.

**Preguntas probables:**
- *Técnica:* **¿Cómo se entrenó el modelo de MLflow?** Con las 489 muestras ya dichas, con Naive Bayes sobre palabras, pares de palabras y trigramas de letras (que toleran errores de escritura). Se evalúa con 24 preguntas aparte. (train.py; runs/v1.json.)
- *Técnica:* **¿Por qué Naive Bayes y no una red neuronal?** Es pequeño, explicable, entrena en segundos sin GPU y no obedece órdenes escondidas en la pregunta. Para decidir «¿es del Hub?» alcanza con 95,8 % y 0 pérdidas. (ADR-10.)
- *Técnica:* **¿El 95,8 % no es poco con solo 24 preguntas de prueba?** Es una muestra pequeña y lo decimos así. Por eso la regla que importa es «0 preguntas del Hub perdidas», y el modelo se puede reemplazar o volver atrás sin tocar el resto.
- *Técnica:* **¿Qué guarda MLflow exactamente?** Por corrida: parámetros (algoritmo, umbral, huella de los datos, commit), métricas, los datos y el modelo empaquetado. (Figura 19; B04, D01.)
- *Decisión:* **¿Cómo evitan que un modelo peor reemplace al de producción?** Reglas de promoción: no se promueve un candidato que pierda preguntas del Hub o cuya exactitud baje; el alias production solo se mueve si pasa, y hay rollback. Se promueve con `promover.py --version N`. (promocion.py.)
- *Decisión:* **¿Por qué un clasificador antes del LLM?** Evita el 91,7 % de las llamadas ajenas (más lentas y costosas) y no puede ser engañado por una orden escondida.
- *Trampa:* **¿Es MLOps de verdad si es un modelo tan simple?** Sí: el ciclo es el mismo (datos, entrenamiento, evaluación, versionado, promoción, rollback); lo que cambia es el tamaño del modelo.
- *Trampa:* **¿Por qué 348 muestras generadas?** Para cubrir el vocabulario del Hub con 58 términos en 6 plantillas, y no depender solo de 141 preguntas. La prueba nunca usa muestras generadas.

## Diapositiva 42 · LLMOps: el asistente responde con la ayuda del Hub, vía RAG (75 s)

**Guion:**
«LLMOps es operar un modelo de lenguaje que ya viene entrenado: aquí, Qwen2.5 de 7 mil millones de parámetros, con un prompt versionado, recuperación de contexto, evaluaciones, guardas de seguridad y servido localmente con Ollama. Primero, una sola vez, preparamos la ayuda del Hub: son 31 secciones, cada una se convierte en un vector, un embedding, y se guarda en PostgreSQL. Luego, con cada pregunta: se tapan los secretos, el clasificador decide si es del Hub, se calcula el embedding de la pregunta y se buscan los cuatro trozos más parecidos, con una similitud de al menos 0,60. Si ninguno llega, el asistente responde "No tengo esa información" sin llamar al modelo. Si hay trozos, entran al prompt como contexto cerrado, el modelo responde, y la respuesta pasa otra vez por la redacción de secretos. Con RAG acertamos 92,5 por ciento; con todo el contexto, 95.»

**Lo que sí o sí se dice, en orden:**
1. LLMOps = operar un modelo ya entrenado (Qwen2.5 7B, Apache 2.0): prompt v3, RAG, evaluaciones, guardas, Ollama local.
2. Preparación, una sola vez: 31 secciones → embeddings con nomic-embed-text → PostgreSQL (kb_documents, kb_chunks), sin pgvector.
3. Por cada pregunta: tapar secretos → clasificador → embedding de la pregunta → similitud coseno → 4 trozos con ≥ 0,60.
4. Si ninguno llega a 0,60: «No tengo esa información», sin llamar al LLM.
5. Si hay trozos: prompt v3 con contexto cerrado → qwen2.5:7b → redacción de secretos → texto plano.
6. Respaldos: sin Ollama cae a búsqueda por palabras y avisa; modo contexto completo alternativo.
7. Resultados: 92,5 % con RAG, 95 % con contexto completo (meta 90 %).

**Preguntas probables:**
- *Técnica:* **¿Cómo funciona el RAG?** La ayuda se divide en 31 trozos; cada uno se vuelve un vector. Ante una pregunta se calcula su vector, se comparan por similitud coseno y los 4 más parecidos (≥ 0,60) entran al prompt como contexto cerrado. Si ninguno llega, no se llama al modelo. (knowledge.py; ADR-09.)
- *Técnica:* **¿Qué es un embedding?** Una lista de números que representa el significado de un texto; textos parecidos dan vectores parecidos, y se comparan con el coseno.
- *Técnica:* **¿Por qué umbral de 0,60 y top 4?** Son los valores que dieron mejor resultado en el conjunto de evaluación; bajar el umbral mete ruido y subirlo hace que el asistente diga «no sé» de más. (config.py; D02.)
- *Técnica:* **¿Qué diferencia hay entre MLOps y LLMOps aquí?** MLOps es el ciclo del clasificador que entrenamos; LLMOps es operar Qwen2.5, que ya viene entrenado: prompt versionado, RAG, evaluaciones, guardas y serving. (Glosario.)
- *Técnica:* **¿Cómo evitan que el modelo invente?** El prompt exige responder solo con el contexto; si no hay contexto relevante no se llama al modelo; hay conjuntos de evaluación versionados. Las 9 preguntas sin respuesta recibieron «no tengo esa información». (03 §2.)
- *Seguridad:* **¿Qué pasa con la inyección de prompts?** Resiste 9 de 10 inyecciones y 5 de 5 documentos maliciosos; los fallos están declarados (H-IA-02). Eso lo amplía Andrés en la diapositiva 45.
- *Decisión:* **¿Por qué no fine-tuning?** La ayuda cambia con el Hub; con RAG se actualiza reindexando, sin reentrenar, y cabe en una GPU de 8 GB.
- *Trampa:* **¿Por qué no pgvector?** Con 31 trozos la similitud coseno en Python basta; agregar la extensión sumaría una dependencia sin beneficio a esta escala. Con más trozos se revisaría. (ADR-09.)

## Diapositiva 43 · El técnico puede preguntar hablando sin que el audio salga del equipo (45 s)

**Guion:**
«El técnico también puede preguntar hablando. La voz se convierte en texto con faster-whisper, el asistente responde y Piper la lee en voz alta, todo en CPU y en un servicio aparte. Medimos 5,8 por ciento de error de palabras, 3,3 segundos por transcripción y 0,6 segundos por respuesta hablada. La transcripción se muestra y se corrige antes de enviar, los secretos se tapan y el audio no se guarda. Elegimos voz y no imagen porque la GPU de 8 gigas ya la ocupa el modelo. Ahora Andrés nos cuenta qué tan rápido responde y cómo sabemos que no inventa.»

**Lo que sí o sí se dice, en orden:**
1. Flujo: voz → texto (faster-whisper small) → asistente → voz (Piper es_MX), todo en CPU, servicio aparte (ADR-11).
2. Medido: 5,8 % de error de palabras, 3,3 s de transcripción, 0,6 s de respuesta hablada, 787 MiB de RAM (D11).
3. Control: transcripción visible y corregible antes de enviar, secretos tapados, audio no guardado.
4. Por qué voz y no imagen: ComfyUI ~5 GB de VRAM vs. GPU de 8 GB ya ocupada.
5. Pasa la palabra a Andrés.

**Preguntas probables:**
- *Técnica:* **¿Por qué en CPU?** Para dejar la GPU al modelo de lenguaje; con CPU el costo es 3,3 s por transcripción, aceptable para consultas del técnico. (ADR-11.)
- *Técnica:* **¿Qué es el error de palabras (WER)?** El porcentaje de palabras mal transcritas respecto al texto de referencia; 5,8 % con el conjunto de prueba. (D11.)
- *Seguridad:* **¿Se guarda el audio?** No. Se transcribe, se muestra el texto y el audio se descarta; las preguntas se guardan redactadas.
- *Decisión:* **¿Por qué voz y no imagen o video?** Hardware: la GPU de 8 GB ya la ocupa el modelo de 7B. Voz en CPU cumple lo multimodal y además sirve al técnico con las manos ocupadas. (ADR-11.)
- *Trampa:* **¿Funciona con ruido de sala?** Se probó con micrófono falso y en un navegador real (D12); [PENDIENTE: probar con el micrófono del salón]. Si falla en vivo, se corrige el texto a mano o se escribe.
- *Licencia:* **¿Piper es GPL?** Sí (GPL-3.0); por eso corre aislado por HTTP y no se mezcla con el código del Hub. (06 §8.1.)

---

# Bloque 5 · Cierre y demo (47 y 48)

## Diapositiva 47 · Lo que aprendimos y lo que sigue (45 s)

**Guion:**
«Con todo esto, la conclusión central: con Git como única puerta, cada cambio queda auditado y se puede revertir; el rollback deja de ser una operación manual. La seguridad dejó de ser una revisión al final: es condición para aprobar. Y medir contra el compromiso de cada plan convierte la operación en un compromiso de negocio. Aprendimos cuatro cosas: toda cifra necesita evidencia, selfHeal obliga a provocar las fallas por Git, un apply de infraestructura sin estado puede tumbar producción, y 8 gigas de GPU obligan a decidir. Lo que sigue: importar los clientes al estado de OpenTofu, verificar la firma dentro del clúster y llevarlo a la nube con rotación de tokens.»

**Lo que sí o sí se dice, en orden:**
1. Conclusión central: Git como única puerta → cambio auditado y reversible.
2. Seguridad como condición para aprobar, no revisión final.
3. Medir contra el SLO del plan = compromiso de negocio.
4. Lecciones: toda cifra con evidencia (la corrida encontró 3 hallazgos reales); selfHeal; apply sin estado; 8 GB de GPU.
5. Trabajo futuro: importar clientes a OpenTofu, prompt v4, firma dentro del clúster, nube con rotación de tokens, retirar la excepción de nginx, medir consumo energético.
6. Paso a la demo.

**Preguntas probables:**
- *Decisión:* **¿Qué harían distinto?** Importar los clientes al estado de OpenTofu desde el principio y ensayar el reinicio completo del clúster. (H-IAC-01; 05.)
- *Negocio:* **¿Esto sirve en producción?** Todavía no: un solo nodo, certificados autofirmados, HTTP abierto en el laboratorio y sin rotación de tokens. Es límite declarado y trabajo futuro. (06 §9.)
- *Negocio:* **¿Cuál es el aporte frente a usar herramientas sueltas?** Que están unidas por un flujo medido de punta a punta: pedir, aprobar, publicar, detectar y recuperar, con evidencia de cada paso (83 verificaciones).
- *Técnica:* **¿Qué es lo más riesgoso que queda?** El hallazgo de OpenTofu (H-IAC-01), la excepción de nginx (vence el 4 dic 2026) y el reinicio completo del clúster sin ensayar.
- *Trampa:* **¿Todos los objetivos se cumplieron?** Sí, con límites declarados en los objetivos 5 y 6 (fuga de reglas del prompt y reinicio sin ensayar). Lo explicó Yisel en la diapositiva 46.
- *Dónde está la evidencia:* En `entrega/evidencias/2026-11-16_bb5a284/`: 83 pasos con comando, salida, duración y commit. (RESUMEN.md.)

## Diapositiva 48 · Vamos a verlo funcionando: del cambio a la recuperación (abre la demo)

**Guion:**
«Les mostramos el flujo completo con la Empresa A: se publica una versión, la puerta de seguridad la revisa, se aprueba, el sitio cae a propósito, el Hub abre el incidente, hacemos el rollback y vemos el resultado. Si algo falla en vivo, tenemos el plan B en capturas.»

**Lo que sí o sí se dice, en orden:**
1. Caso: la Empresa A, del cambio a la recuperación.
2. Los siete pasos, cada uno un módulo del diplomado.
3. Plan B: capturas del paquete de evidencias.

**Preguntas probables:**
- *Técnica:* **¿Esto es en vivo o está grabado?** En vivo, sobre el clúster del laboratorio; el plan B son capturas y un video de respaldo. [PENDIENTE: grabar el video de respaldo.]
- *Trampa:* **¿Por qué la caída es provocada?** Para medir la detección y el MTTR en condiciones controladas; la falla se provoca por Git (publicando una v2 rota) porque selfHeal corrige los cambios manuales.
- *Preparación:* Antes de entrar: `dejar-demo-lista.sh`, calentar el modelo (el primer token en frío tarda 9,5 s) y confirmar el modo del asistente.

---

# Preguntas que pueden caer sobre cualquier diapositiva tuya

- **«Cuéntame la arquitectura en 30 segundos.»** Una consola React habla con una API FastAPI que guarda en PostgreSQL. La API nunca toca Kubernetes: escribe cada versión en Git (Gitea) y Argo CD la aplica en el espacio aislado de cada cliente. La observabilidad sondea los sitios, alerta al Hub y abre incidentes. La IA corre local: un clasificador entrenado, RAG sobre la ayuda con Qwen2.5 y voz en CPU.
- **«¿Qué fue lo más difícil?»** Ajustar todo a una GPU de 8 GB y a un solo equipo, y que el apply de OpenTofu reescribiera a los clientes: nos obligó a documentar el hallazgo y revertir por Git.
- **«¿Qué parte hizo cada uno?»** Nicolás: arquitectura, IA y voz; Andrés: requisitos y evaluación de la IA; Sebastián: contenedores, GitOps e IaC; Eric: seguridad y riesgos; Yisel: operación y observabilidad. (01 Ficha del proyecto.)
- **Si no sabes:** «No tengo ese dato a la mano; está en [documento] y lo puedo mostrar.» No inventes cifras.
- **Preguntas que son de otro:** responde lo básico y pasa la palabra: «Eric lo explicó con detalle en la puerta de seguridad.»

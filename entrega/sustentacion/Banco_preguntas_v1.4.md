<!-- Banco de preguntas probables del jurado para la sustentación del 30 nov 2026, con respuesta corta y su fuente. -->

# Banco de preguntas del jurado · CloudOps Hub

Cada respuesta cabe en 30 a 45 segundos y trae su fuente para defenderla. La exposición no menciona que los casos sean simulados, por indicación del docente; estas respuestas son para cuando el jurado pregunte de frente, y no se debe afirmar lo contrario. Regla del equipo: si no sabemos algo, se dice y se ofrece mostrar la evidencia. No se inventan cifras.
Criterios que asumimos para la rúbrica: dominio del tema, coherencia entre problema y solución, evidencia de implementación, claridad y manejo del tiempo.

## Andrés Felipe Díaz Duque (quiénes somos, problema, objetivos, alcance y requisitos, KPI de respuesta y validación de la IA)

1. **¿Por qué el problema es real si no entrevistaron a ninguna empresa?**
   Lo dijimos de frente: el caso es simulado y sus problemas (publicar a mano, enterarse de las caídas por el cliente, operar sin datos) están documentados en la literatura de entrega continua y SRE: Beyer 2018, Forsgren 2018, Humble y Farley 2010. Lo presentamos para que ustedes lo validen. *Fuente: informe, Contexto; 06 §4.2.*
2. **¿Cómo saben que el asistente no inventa?**
   Con conjuntos versionados de lo que la respuesta debe y no debe decir. El tutor tuvo 0 alucinaciones en 30 preguntas, y las 9 preguntas sin respuesta en la ayuda recibieron «no tengo esa información». *Fuente: 03 §2 y §7; D02, D07.*
3. **Ustedes muestran 3 verificaciones fallidas. ¿No es eso un problema?** *(M7)*
   Al contrario: la corrida existe para encontrar fallas. Las 3 son hallazgos reales; dos se corrigieron y se verificaron el 20 nov, y la de OpenTofu quedó como límite declarado con su mitigación. *Fuente: RESUMEN.md; 03 §12.*
4. **¿Qué es un Pod y por qué se recrea solo?** *(M2, que no presentó)*
   Es la unidad mínima que ejecuta Kubernetes: uno o más contenedores juntos. Un Deployment declara cuántas réplicas debe haber; si una muere, el controlador crea otra. En el ensayo volvió en 8 s. *Fuente: informe, Tabla 12; C28.*
5. **¿Qué hace Trivy y qué pasa si encuentra una CVE crítica?** *(M3)*
   Busca vulnerabilidades conocidas en la imagen y en sus dependencias. Una CVE crítica con arreglo disponible bloquea la versión; las que no tienen arreglo se aceptan con fecha de revisión y se publican como VEX. *Fuente: informe, Pipeline CI/CD; 06 RS-04.*

6. **¿Por qué 11 requisitos Must y solo 1 Could?** *(M7)*
   Porque priorizamos con MoSCoW lo que hace funcionar el flujo de punta a punta: pedir, aprobar, publicar, detectar y recuperar. El único Could es registrar sitios en el catálogo de Backstage. Cada requisito tiene un criterio que se puede medir. *Fuente: informe, Tabla 6.*
7. **¿Cómo se rastrea un requisito hasta su evidencia?** *(M7)*
   La matriz 02 une cada requisito con su historia, el componente, la prueba (PF-01 a PF-28) y el paso de la corrida. Por ejemplo, RF-07 → HU-03 → Blackbox y Alertmanager → PF-06 → C26. *Fuente: 02; informe, Tabla 17.*


8. **¿Qué es el TTFT y por qué lo miden?** *(M5)*
   Es el tiempo hasta que aparece el primer token de la respuesta: lo que espera una persona antes de ver que el asistente empieza a escribir. Medimos 95 ms con contexto completo y 228 ms con RAG (263 ms con la búsqueda); y 9,5 s la primera vez, cuando hay que cargar el modelo en la GPU. *Fuente: ai/eval/medir_respuesta.py, medición del 21 nov.*
9. **¿Por qué el contexto completo tiene menos TTFT que el RAG si manda un prompt más grande?** *(M5)*
   Porque en contexto completo el prompt es siempre el mismo y Ollama reutiliza lo que ya leyó (prefill de 36 ms). Con RAG el contexto cambia con cada pregunta y hay que leerlo de nuevo (176 ms), más 33 ms de búsqueda. Aun así quedan por debajo de 0,3 s. *Fuente: medir_respuesta.py.*
10. **¿El Hub transmite la respuesta en flujo?** *(M5)*
   No. Hoy entrega la respuesta completa, con mediana de 1,1 s. El TTFT dice cuándo empezaría a escribir si se hiciera en flujo, que es una mejora posible. Se midió con 20 preguntas en una RTX 4060 de 8 GB. *Fuente: backend/app/integrations/ollama.py (stream desactivado).*
11. **¿Por qué la ficha dice 51,2 tokens/s y ahora midieron 46 a 48?** *(M5)*
   La ficha se midió con un prompt corto; ahora se usó el prompt real del asistente, de 830 a 3.600 tokens de entrada. Son dos pruebas distintas con el mismo modelo. *Fuente: D06 y medir_respuesta.py.*


## Nicolás Gaviria Cerón (vista 4+1, C4 nivel 2, ADR, MLOps, LLMOps y RAG, voz, cierre y demo)

1. **¿Por qué el Hub no habla directamente con Kubernetes?**
   Para que Git sea la única puerta: todo cambio queda en el historial, se revisa y se revierte con un `git revert`. El Hub escribe en Gitea, lee el estado de Argo CD y las métricas de Prometheus. *Fuente: ADR-02 y ADR-03; principio 5 de la constitución.*
2. **¿Por qué qwen2.5:7b y no un modelo más grande o una API externa?**
   Por privacidad, los datos de clientes no salen (Ley 1581), y por la licencia Apache 2.0. Además cabe en la GPU de 8 GB: 4.535 MiB a 51,2 tokens/s. El 3B tiene licencia de investigación y solo sirve para comparar. *Fuente: ADR-08; Tabla 13.*
3. **¿Por qué RAG propio y no pgvector?**
   Con 31 trozos de ayuda, la similitud coseno en Python basta. El experimento híbrido dio 41 contra 42 aciertos de 43 y empeoraba el conjunto ciego. Así no dependemos de una extensión de la base. *Fuente: ADR-09.*
4. **¿Qué es MLOps en su proyecto, si no entrenan un LLM?** *(M5)*
   El clasificador de preguntas (Naive Bayes) sí se entrena: 141 preguntas etiquetadas más 348 generadas, probado con 24 que nunca vio. MLflow guarda cada versión con sus parámetros, métricas y datos, y el alias production dice cuál usa el Hub. Solo se promueve si no empeora a la actual y se puede volver atrás. *Fuente: ADR-10; B04, D01.*
5. **¿Qué es un SBOM y para qué les sirve?** *(M3, que no presentó)*
   Es el inventario de componentes y versiones de una imagen. Con él sabemos qué licencias tenemos (por ejemplo, Piper es GPL y por eso va aislado) y qué revisar cuando sale una CVE nueva. Las 3 imágenes suman 346 paquetes. *Fuente: 06 §8.1.*
6. **¿Por qué no hicieron generación de imagen si el módulo 6 la pide?**
   ComfyUI necesitaba unos 5 GB de VRAM y la GPU ya la ocupa el modelo de 7B. Elegimos voz en CPU, que es multimodal y además es útil para el técnico. *Fuente: ADR-11; informe, Fuera de alcance.*

7. **¿Para qué usar 4+1 si ya tienen C4?**
   Responden preguntas distintas. C4 baja de nivel (contexto, contenedores, componentes); 4+1 mira el mismo sistema desde cuatro públicos: lógica, desarrollo, procesos y física. Los 16 casos de uso son el «+1» que valida todas las vistas. *Fuente: docs/arquitectura (vista general 4+1); informe, Figuras 1 a 4.*
8. **¿Qué ADR cambiarían hoy?**
   La ADR-04: sigue aceptada pero con un hallazgo abierto (H-IAC-01). Lo primero sería importar los clientes existentes al estado de OpenTofu. La ADR-12 ya se reemplazó por la ADR-13. *Fuente: informe, Tabla 9.*


9. **¿Cuál es la diferencia entre MLOps y LLMOps en su proyecto?** *(M5)*
   MLOps es el ciclo de un modelo que entrenamos nosotros: el clasificador de preguntas, con datos, entrenamiento, evaluación, versionado en MLflow y promoción. LLMOps es operar un modelo de lenguaje que ya viene entrenado (Qwen2.5): prompt versionado, RAG, conjuntos de evaluación, guardas contra inyección y fuga, y servirlo en local con Ollama. *Fuente: informe, Glosario; train.py.*
10. **¿Cómo se entrenó el modelo de MLflow?** *(M5)*
   Con 141 preguntas etiquetadas como «del Hub» o «ajenas» y 348 generadas con 58 términos del Hub en 6 plantillas. Es Naive Bayes sobre palabras, pares de palabras y trigramas de letras. Se evalúa con 24 preguntas aparte: exactitud 95,8 % y 0 preguntas del Hub perdidas. MLflow guarda parámetros, métricas, datos y el modelo. *Fuente: ai/classifier/train.py; runs/v1.json.*
11. **¿Cómo funciona el RAG?** *(M5)*
   La ayuda del Hub se divide en 31 trozos y cada uno se convierte en un vector con nomic-embed-text. Ante una pregunta se calcula su vector, se comparan por similitud coseno y se toman los 4 trozos más parecidos con al menos 0,60. Esos trozos entran al prompt como contexto cerrado; si ninguno llega a 0,60, el asistente dice «No tengo esa información». *Fuente: knowledge.py; ADR-09.*
12. **¿Qué es un embedding?** *(M5)*
   Una lista de números que representa el significado de un texto: textos parecidos dan vectores parecidos. Se comparan con la similitud coseno, que mide el ángulo entre vectores. *Fuente: informe, Glosario.*
13. **¿Por qué un clasificador antes del LLM?** *(M5)*
   Para no despertar al LLM con preguntas ajenas al Hub: evita el 91,7 % de esas llamadas, que son más lentas y costosas. Además un LLM puede ser engañado por una orden escondida y el clasificador no obedece órdenes. *Fuente: ADR-10; ficha de modelos.*
14. **¿Cómo evitan que un modelo peor reemplace al que está en producción?** *(M5)*
   Con reglas de promoción: no se promueve un candidato que pierda preguntas del Hub o cuya exactitud baje frente a la versión actual. El alias production solo se mueve si pasa y se puede volver a la versión anterior. *Fuente: ai/classifier/promocion.py.*

## Sebastián Camilo Paja Barrios (contenedores, C4 nivel 3, modelo de datos, aislamiento, IaC y GitOps)

1. **¿Qué es un build multi-stage y por qué sin root?**
   Una etapa compila y otra solo copia lo necesario, así que la imagen final es más pequeña y no trae herramientas de prueba. Sin root, si alguien compromete el contenedor no tiene privilegios. La prueba de humo lo verifica (A13). *Fuente: Tabla 3; A13.*
2. **¿Qué pasó con OpenTofu (H-IAC-01)?**
   El inventario tenía los tres clientes reales, pero el estado no los conocía. El apply reescribió sus overlays y los sitios quedaron sin imagen. Se revirtió por Git en minutos. La lección: importar los clientes al estado antes de usar IaC con algo que ya existe. *Fuente: ADR-04; C30.*
3. **¿Qué diferencia hay entre Helm y Kustomize, y por qué tienen los dos?** *(M2)*
   Helm empaqueta con plantillas y valores; Kustomize aplica parches sobre YAML base. Mantenemos el chart y probamos que produce los mismos objetos que Kustomize (A07). *Fuente: RNF-13; A07.*
4. **¿Qué es el burn rate?** *(M4, que no presentó)*
   La velocidad a la que se gasta el presupuesto de error comparada con la normal. Si se consume más de 14,4 veces más rápido en 1 h y en 5 min, alerta de inmediato. *Fuente: informe, Observabilidad.*
5. **¿Cómo protegen los datos personales en la base?** *(M3)*
   Todos los datos son sintéticos. Las contraseñas van con bcrypt de 12 rondas, cada cliente solo ve lo suyo, las preguntas al asistente se guardan redactadas y la bitácora no tiene ruta para borrar. *Fuente: informe, Modelo de datos; B07.*

6. **¿Qué muestra el C4 nivel 3 que no muestra el nivel 2?**
   Lo que hay dentro de la API: los routers con sus reglas de negocio, los servicios compartidos (auditoría, redacción, publicador GitOps, vigilante, puerta) y las integraciones. Solo estas últimas hablan con sistemas externos, siempre con tiempo de espera acotado. *Fuente: informe, Figura 3.*
7. **¿Por qué los embeddings van en PostgreSQL y no en una base vectorial?**
   Son 31 trozos de ayuda: caben como lista numérica en `kb_chunks` y la similitud se calcula en Python. Una base vectorial agregaría otro servicio que operar sin beneficio a esta escala. *Fuente: ADR-09; informe, Modelo de datos.*


## Eric Sebastián Mesías Rojas (CI, puerta de seguridad, cadena de suministro, riesgos y cumplimiento)

1. **¿Por qué dos pipelines y no uno?**
   Cumplen roles distintos. El CI de GitHub protege el código del Hub; la puerta de Gitea procesa cada versión de los sitios de los clientes, la firma y la verifica dentro del laboratorio, que no es alcanzable desde GitHub. *Fuente: informe, Pipeline CI/CD.*
2. **¿Qué es SLSA y qué nivel de procedencia tienen?**
   Es un marco para garantizar de dónde sale un artefacto. Cosign firma la imagen y una atestación de procedencia que declara el commit, el repositorio y la corrida; antes de publicar se verifica que coincida con el commit de la versión. No declaramos un nivel formal de SLSA. *Fuente: ADR-05; README, Seguridad.*
3. **¿No es peligrosa la excepción de nginx?**
   Es temporal, solo de laboratorio y con datos sintéticos. Está escrita con vencimiento (4 dic 2026) y se retira al publicarse la 1.30.7. Sin esa decisión explícita, la puerta bloqueaba los sitios. *Fuente: H-CVE-01; pipelines/trivy-excepciones.yaml.*
4. **¿Qué es una NetworkPolicy?** *(M2, que no presentó)*
   Una regla de firewall dentro del clúster. Por defecto denegamos todo y abrimos solo lo necesario, así un sitio no alcanza a otro ni a la plataforma (C07 a C12). *Fuente: RNF-08.*
5. **¿Cómo se valida el código generado con IA durante el desarrollo?** *(M5)*
   Igual que el resto: ruff, tsc, pruebas, Bandit, Gitleaks y Trivy en el CI, más la lista de comprobación del PR para código asistido por IA. Todo cambio entró por PR. *Fuente: 04; 06 RI-07.*

6. **¿Cómo calcularon el nivel de cada riesgo?** *(gestión)*
   Probabilidad por impacto, cada uno de 1 a 3: de 1 a 2 es bajo, de 3 a 4 medio, 6 alto y 9 crítico. De los 32 riesgos, dos son críticos y ya ocurrieron (OpenTofu y nginx); ambos tienen mitigación o límite declarado. *Fuente: 06, Escalas y §1.*
7. **¿Qué control demuestra que cumplen la Ley 1581?** *(M3)*
   Todos los datos son sintéticos, los secretos se redactan antes de guardar o enviar a la IA, cada cliente solo ve lo suyo (B07) y nada sale a servicios externos. Para un uso real faltaría el aviso de privacidad y la autorización del titular. *Fuente: informe, Tabla 4; 06 §5.*


## Yisel Andrea Charo Rivera (observabilidad, KPI, incidentes, ensayos de fallas y resultados)

Ella no presentó código y no lo necesita: las respuestas son conceptuales y se apoyan en lo medido.

1. **¿Cuál es la diferencia entre SLI, SLO y SLA?**
   El SLI es lo que se mide: aquí, la fracción de sondeos exitosos. El SLO es la meta interna: 99,9 % para Premium. El SLA es lo que se le promete al cliente, con sus tiempos de respuesta y solución (P1: 15 min y 4 h). *Fuente: informe, Observabilidad; README, matriz P1–P4.*
2. **¿Qué es un contenedor y en qué se diferencia de una máquina virtual?** *(M1)*
   Un contenedor empaqueta la aplicación con sus dependencias y comparte el núcleo del sistema; una máquina virtual trae su propio sistema operativo. Por eso el Hub arranca en 23 s desde un clon limpio. *Fuente: F01.*
3. **¿Qué es Kubernetes en una frase y qué hizo por ustedes en los ensayos?** *(M2)*
   Un orquestador que mantiene el estado declarado de las aplicaciones. Recreó un Pod borrado en 8 s y escaló la API a 2 réplicas cuando la saturamos. *Fuente: Tabla 12; C28.*
4. **¿Qué es GitOps y por qué el rollback es un `git revert`?** *(M2)*
   Git guarda el estado deseado y Argo CD hace que el clúster coincida. Volver atrás es revertir el commit en Git; Argo CD aplica la versión anterior. Así queda registrado quién lo hizo y cuándo. *Fuente: ADR-02; C25.*
5. **¿Por qué no se abre un incidente si un Pod cae?**
   La alerta exige 30 s de caída sostenida, y Kubernetes recrea el Pod en 8 s. Así evitamos alertas que nadie necesita atender. Lo medimos a propósito. *Fuente: ADR-06; C28.*
6. **¿Qué diferencia hay entre métricas, registros y trazas?** *(M4)*
   Las métricas son números en el tiempo (Prometheus, 30 días). Los registros son eventos con texto (Loki, 72 h). Las trazas son el recorrido de una petición por cada etapa (Tempo, 24 h, sin el texto de las preguntas). *Fuente: Tabla 10.*
7. **Si el MTTR fue 3,4 min, ¿por qué en otra prueba salió 5,42?**
   Son escenarios distintos. El 3,4 es el caso del restaurante con rollback inmediato (C25). El 5,42 es la demo 010, que además apagaba Prometheus y tenía pasos manuales. Ambos están dentro del SLA del P1. *Fuente: informe, Tabla 7 y PF-09.*
8. **¿Qué pasa si se cae la máquina con la GPU?** *(M5, técnica)*
   El Hub sigue funcionando y el asistente avisa que la IA no respondió (F01). Los cambios, los incidentes y los rollbacks no dependen de la IA. *Fuente: 05 §10.*
9. **¿Qué es la puerta de seguridad en términos de proceso?** *(M3, técnica sin código)*
   Un control de calidad antes de liberar: seis inspecciones en orden, y si una falla la versión no avanza y el Hub no deja aprobarla. Pasó los 9 escenarios de prueba. *Fuente: ADR-05; B06.*
10. **¿Cuánto cuesta operar un cliente?** *(gestión)*
   El Hub calcula horas por cliente por 25.000 COP/h. Los planes incluyen 4, 10 y 20 horas al mes con precios de 150.000, 350.000 y 700.000 COP. Son valores sintéticos del caso. *Fuente: `docs/kpi.md`; `seed/plans.json`.*

11. **¿Qué es RED y USE?** *(M4)*
   Dos formas de leer un sistema. RED mira lo que vive el usuario: peticiones, errores y duración. USE mira lo que sufre el recurso: uso, saturación y errores. Las dos están en el tablero de Grafana por sitio y por Pod. *Fuente: informe, Figura 18.*
12. **¿Por qué el cliente no ve el costo ni las horas?** *(gestión)*
   Por diseño: el portal muestra estado, disponibilidad frente a lo acordado, incidentes y solicitudes, sin jerga. El costo, las horas y la carga por técnico son información de gestión de la agencia. *Fuente: `docs/kpi.md`, CA-4.*


## Preguntas para cualquiera del equipo

- **¿Qué harían distinto?** Importar los clientes al estado de OpenTofu desde el principio y ensayar el reinicio completo del clúster. *Fuente: hallazgos H-IAC-01; 05.*
- **¿Esto sirve en producción?** Todavía no: es un solo nodo, con certificados autofirmados, HTTP abierto en el laboratorio y sin rotación de tokens. Lo declaramos como límite y como trabajo futuro. *Fuente: 06 §9.*
- **¿Dónde está la evidencia?** En `entrega/evidencias/2026-11-16_bb5a284/`: cada uno de los 83 pasos con su comando, salida, duración y commit. *Fuente: RESUMEN.md.*

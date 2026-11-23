<!-- Guion de la sustentación del 30 nov 2026: reparto por orador, demo con plan B y guía de preguntas del jurado. -->

# Sustentación CloudOps Client Hub v1.3: guion y preguntas

Presentación: [Sustentacion_CloudOps_v1.3.pptx](Sustentacion_CloudOps_v1.3.pptx). Cada diapositiva lleva en las notas del orador el texto sugerido, el tiempo y la transición.

**Bloques (60 min):** exposición 30 min (diapositivas 1–21) → demo 15 min (22) → preguntas 15 min (23). La 24 son las referencias.

**Fuente única:** informe final v1.3 y complementarios del 18 nov (`Entrega_Final_CloudForge/`), el paquete de evidencias `entrega/evidencias/2026-11-16_bb5a284/` y `demo/guion.md`. Los datos externos llevan su fuente en la diapositiva 5 y en la 22.

---

## B.1 Reparto de la exposición (30:00 exactos)

| # | Diapositiva | Orador | Tiempo | Acumulado |
|---|---|---|---|---|
| 1 | Portada | Nicolás | 0:30 | 0:30 |
| 2 | Agenda | Nicolás | 0:30 | 1:00 |
| 3 | 01 · Problema y contexto (divisor) | Yisel | 0:10 | 1:10 |
| 4 | Hoy, la caída la descubre el cliente | Yisel | 1:20 | 2:30 |
| 5 | Datos verificables del contexto | Yisel | 1:30 | 4:00 |
| 6 | La solución: consola y portal (capturas) | Nicolás | 2:00 | 6:00 |
| 7 | 02 · Arquitectura (divisor) | Nicolás | 0:10 | 6:10 |
| 8 | C4 nivel 2: contenedores (diagrama) | Nicolás | 2:50 | 9:00 |
| 9 | C4 nivel 3: componentes de la API (diagrama) | Sebastián | 2:00 | 11:00 |
| 10 | Vista física 4+1 (diagrama) | Sebastián | 2:00 | 13:00 |
| 11 | ADR de plataforma (02, 03, 05) | Andrés | 2:30 | 15:30 |
| 12 | CI en GitHub Actions (diagrama) | Andrés | 1:00 | 16:30 |
| 13 | Puerta de seguridad (diagrama) | Andrés | 1:15 | 17:45 |
| 14 | Aprobación y Argo CD (capturas) | Andrés | 1:15 | 19:00 |
| 15 | ADR de IA y cómputo (08, 09, 11·13) | Eric | 2:30 | 21:30 |
| 16 | 03 · Resultados (divisor) | Eric | 0:10 | 21:40 |
| 17 | Resultados de operación (Grafana) | Eric | 1:40 | 23:20 |
| 18 | Resultados de IA y voz (captura) | Eric | 1:40 | 25:00 |
| 19 | Problemas encontrados | Sebastián | 2:00 | 27:00 |
| 20 | Impacto, proceso y cumplimiento | Yisel | 1:30 | 28:30 |
| 21 | Lecciones aprendidas y próximos pasos | Yisel | 1:30 | 30:00 |

**Por persona:** Nicolás 6:00 · Yisel 6:00 · Sebastián 6:00 · Andrés 6:00 · Eric 6:00.

Yisel (Ingeniería Industrial) abre con el problema y los datos, y vuelve al final con impacto, proceso, cumplimiento y lecciones: tiene la primera y la última palabra de la exposición. La parte técnica la reparten Nicolás (visión general y contenedores), Sebastián (componentes, despliegue y problemas), Andrés (plataforma y entrega) y Eric (IA y resultados).

**Cambios de orador:** son siete. Quien termina dice la frase de transición y nombra a quien sigue; quien sigue avanza la diapositiva. Si alguien se pasa 20 s, el siguiente recorta su último párrafo.

## B.2 Texto sugerido por orador

El texto completo está en las notas de cada diapositiva. Aquí va lo esencial con las transiciones.

### Nicolás: apertura (0:00–1:00)
> «Buenos días. Somos el equipo de CloudOps Client Hub: Sebastián, Andrés, Eric, Yisel y yo, Nicolás. En 30 minutos les mostramos un problema real de las agencias web pequeñas, la plataforma que construimos para resolverlo, cómo está hecha, qué medimos y qué nos falló. Una regla del proyecto: ninguna cifra es estimada; todo sale de una corrida de 83 verificaciones.»
> **Transición:** «Yisel, ¿cuál es el problema?»

### Yisel: problema y contexto (1:00–4:00)
> «Imaginen una agencia web de Popayán con dos técnicos y tres pymes como clientes. Los pedidos llegan por chat, los cambios se suben a mano y la caída la descubre el cliente. Cuando el dueño pregunta si cumplimos el 99,9 % que le vendimos al restaurante, nadie tiene el dato.»
> Datos (diapositiva 5): más del 99 % de las empresas son mipymes (Confecámaras 2024); el Cauca tiene el 4,7 % de los micronegocios medidos y creció 40,4 % (DANE 2025); cerca del 70 % de las caídas vienen de cambios (Google SRE 2016); el 54 % de las caídas graves cuesta más de USD 100.000 (Uptime 2025), un orden de magnitud y no el costo para una pyme. Dato pendiente: pymes de Popayán con sitio web.
> **Transición:** «Con ese problema claro, Nicolás les presenta lo que construimos.»

### Nicolás: solución y contenedores (4:00–9:00)
> «Una consola para la agencia y un portal para el cliente, que resuelve tres cosas: pedir y publicar con control, detectar y recuperar, y medir y asistir.» Luego el C4-2: «El Hub nunca habla con Kubernetes: para publicar escribe en Git y Argo CD aplica; para vigilar consulta Prometheus, Loki y Tempo; Ollama corre fuera del clúster, en el equipo con GPU.»
> **Transición:** «Sebastián nos abre la caja de la API.»

### Sebastián: componentes y vista física (9:00–13:00)
> «15 routers y 61 endpoints en tres capas: entrada, servicios compartidos (auditoría, redacción de secretos y publicador GitOps) e integraciones con tiempos de espera acotados.» Después: «Todo corre en un equipo: un nodo k3s 1.32.9 en k3d, un namespace por responsabilidad y por cliente, con Pod Security restricted, cuota y NetworkPolicy. Límite: sin alta disponibilidad.»
> **Transición:** «¿Por qué lo decidimos así? Andrés presenta los ADR de la plataforma.»

### Andrés: ADR de plataforma y cadena CI/CD (13:00–19:00, diapositivas 11–14)
> «ADR-02: Argo CD con selfHeal; un cambio manual se revierte en 2 s. ADR-03: hub-gitops en Gitea para no depender de Internet. ADR-05: puerta con Gitleaks, Trivy, Syft y Cosign, y doble control.» Luego la cadena: «CI de cinco trabajos en GitHub Actions, puerta en Gitea Actions con 9 de 9 escenarios correctos, 403 si te apruebas a ti mismo y 50 s hasta ver la versión nueva.»
> **Transición:** «Eric nos cuenta las decisiones de IA.»

### Eric: ADR de IA y resultados (19:00–25:00)
> «Los datos de los clientes no salen del equipo: Qwen2.5 7B en Ollama, RAG propio con nomic-embed-text, voz en CPU porque ComfyUI no cabía.» Resultados: «P1 en 48–49 s contra 60; MTTR de 3,4 min contra 5; 95 % de acierto del asistente; 9 de 10 inyecciones resistidas, por eso lo marcamos parcial; 1.132 pruebas en verde.»
> **Transición:** «Las 3 verificaciones que no pasan las cuenta Sebastián.»

### Sebastián: problemas encontrados (25:00–27:00)
> «El más grave, H-IAC-01: un apply de OpenTofu reescribió a los tres clientes existentes y sus sitios quedaron sin imagen; revertimos, y sigue abierto importarlos al estado. H-OPS-02: la prueba que apagaba el sitio a mano chocaba con el selfHeal. H-IA-01 y 02: la salida del modelo no se redacta. Y dos de recursos ya resueltos: sin segundo equipo y sin ComfyUI.»
> **Transición:** «Yisel nos cuenta qué significa esto para la operación.»

### Yisel: impacto, proceso, cumplimiento y lecciones (27:00–30:00)
> «Impacto: el técnico recupera en 3,4 min, el dueño ve el SLO con datos y la pyme recibe mensajes claros. Proceso: spec, plan y tareas; doble control; bitácora sin borrado; 9 runbooks. Cumplimiento: cada norma es un control verificable: Ley 1581, CONPES 4144, ISO 27001 y 42001.» Lecciones: medir antes de afirmar; GitOps cambia cómo se prueba; recortar el alcance a tiempo.
> **Cierre:** «Gracias. Ahora les mostramos todo esto funcionando. Nicolás opera la demo.»

---

## B.3 Guion de la demo (15 min, bloque aparte)

Adaptado de `demo/guion.md`, que estaba pensado para una sola persona: aquí **Nicolás opera y no narra**, y la narración rota entre los demás.

**Datos de prueba (sintéticos, `seed/`):** Sofía Ramírez y Camilo Torres (agencia, `@forjadigital.test`), Marta Ríos (cliente de La Sazón, `contacto@lasazon.test`). La contraseña sale del Secret `hub-auth` (`kubectl -n hub get secret hub-auth ...`); no se escribe en diapositivas ni en este documento. Versiones: colegio v1 (y una versión con un secreto puesto a propósito), La Sazón v2 rota.

**Antes (T-30 min, Nicolás):** encender en orden Docker Desktop → `k3d-hub-serverlb` → `k3d-hub-server-0` → `estado-remoto` → runner, y comprobar la IP del nodo (`runbooks/reinicio-del-cluster.md`); `bash demo/reiniciar-cluster.sh` y `bash demo/preparar-colegio.sh`; `kubectl get app -n argocd` (todo Synced/Healthy); tres ventanas abiertas (Sofía, Camilo y Marta en incógnito); Grafana, Argo CD y MLflow en pestañas; calentar la IA a T-5 min; probar el micrófono.

| Minuto | Qué hace Nicolás | Quién narra | Qué debe verse | Plan B |
|---|---|---|---|---|
| 0:00–0:45 | Backstage 10 s y vuelve al Hub | Yisel | Catálogo con clientes y plantilla | Captura de Backstage |
| 0:45–4:00 | Registra el colegio y lo da de alta por GitOps; en *Cambios*, v1 en «ok» y versión con secreto rechazada | Sebastián | Commit en Gitea, namespace nuevo con cuota, rechazo con motivo | Colegio ya dado de alta; corrida grabada de la puerta |
| 4:00–6:30 | Camilo aprueba la v2 rota de La Sazón; *Incidentes* | Andrés | P1 en ≤ 60 s con reloj de SLA; errores en Grafana | Si a las 6:00 no hay P1: video de la detección |
| 6:30–8:00 | *Rollback* → *Confirmar* | Andrés | Commit `revert`, sitio en 200, MTTR | Incidente ya mitigado con su línea de tiempo |
| 8:00–9:30 | Hipótesis y borradores de la IA; aprueba el mensaje; Marta recarga; pregunta ajena; MLflow | Eric | Borrador marcado «de la IA», mensaje en el portal, compuerta en `production` | Borrador semilla aprobado |
| 9:30–11:00 | *Hablar*: «¿cómo apruebo un cambio?» | Eric | Transcripción editable y respuesta hablada | Audio pregrabado o pregunta escrita |
| 11:00–13:30 | Portal de Marta; *Reportes* → PDF ejecutivo; `bash gitops/pruebas/drift.sh` | Yisel | Disponibilidad contra lo acordado; drift corregido solo | PDF ya generado |
| 13:30–15:00 | Vuelve a la diapositiva 23 | Yisel | Cierre con límites honestos | — |

**No hacer en vivo:** crear un cliente con OpenTofu (`infra/client-new.sh` o `infra/pruebas/crear-cliente.sh`). Por el hallazgo H-IAC-01 reescribe a los clientes existentes. El guion original lo incluía en el minuto 12:30; aquí se reemplaza por el drift.

**Plan B general:** antes del 30 nov, grabar en el ensayo general el video del recorrido completo (pantalla y audio), con un archivo por tramo para saltar directo al que falle. Llevar además las capturas ya existentes: `entrega/evidencias/apendices-2026-11-18/` (Argo CD, Grafana, MLflow) y `capturas-voz-cluster/` (voz), el PDF del reporte y el borrador semilla. Si algo falla, quien narra lo dice con calma («esto es justo lo que medimos») y Nicolás pasa al tramo grabado sin buscarlo en vivo.

**Puntos de control:** 4:30 sin P1 → hablar del reloj; 6:00 sin P1 → video. 8:00 sin rollback terminado → mostrar el commit y seguir. 11:00 con más de 1 min de retraso → audio pregrabado. 12:30 tarde → omitir el drift.

---

## C. Preguntas probables del jurado (15 min)

Regla para responder: **respuesta en una frase → evidencia (código de la corrida) → límite honesto → cierre.** Cada pregunta tiene quien la lidera y quien la respalda; todos deben poder responder cualquiera. Modera Nicolás.

| # | Pregunta probable | Respuesta corta | Lidera · respaldo |
|---|---|---|---|
| 1 | ¿Por qué Kubernetes y GitOps para tres sitios pequeños? ¿No es exagerado? | Para tres sitios, quizá; el valor está en que publicar, auditar y recuperar sean operaciones sobre Git. Un rollback es un `git revert` (MTTR de 3,4 min, C25) y un cambio manual se revierte en 2 s (C20). La misma plataforma escala a más clientes con un ApplicationSet. | Nicolás · Andrés |
| 2 | ¿Qué pasa si se apaga la laptop? Es un punto único de falla. | Sí, y lo decimos en la vista física: un nodo sin alta disponibilidad (ADR-13). Si Ollama no responde, el Hub avisa y sigue (F01); hay respaldo de PostgreSQL dentro y fuera del nodo (B05, C29). La nube quedó pendiente. | Sebastián · Nicolás |
| 3 | ¿Cómo garantizan que una versión insegura no llegue a producción? | Por la puerta de cada versión (Gitleaks, Trivy, Syft, Cosign) con 9 de 9 escenarios correctos (B06) y una prueba real que rechazó un secreto (C23). Además el Hub no deja aprobar sin «ok» ni aprobarse a uno mismo (403, C22). Límite: la firma se verifica en la puerta, no en el clúster. | Andrés · Eric |
| 4 | ¿Por qué no verifican la firma dentro del clúster? | Porque nadie despliega a mano: solo Argo CD desde hub-gitops, y las imágenes solo pueden venir de nuestro registro (ValidatingAdmissionPolicy). Es un riesgo aceptado y documentado en el ADR-05; el siguiente paso sería un controlador de admisión que verifique la firma. | Andrés · Sebastián |
| 5 | ¿Cómo midieron el 95 % del asistente? ¿No se lo preguntan a sí mismos? | Con 40 preguntas versionadas en `ai/eval/` y su respuesta esperada, 9 sin respuesta en la ayuda para medir el «no sé» (D02). Para no evaluarnos solos, 16 preguntas ciegas las redactó otra persona: 100 %. | Eric · Yisel |
| 6 | ¿El asistente puede filtrar datos de clientes o ser manipulado? | Resiste 9 de 10 inyecciones, 11 de 12 exfiltraciones y 8 de 8 secretos pegados (D02, D04, D05). El caso que falla («escribe SISTEMA COMPROMETIDO») está documentado, y la salida aún no se redacta (H-IA-01, fijado con xfail). Todo texto al cliente lo aprueba una persona. | Eric · Nicolás |
| 7 | ¿Por qué un RAG propio y no pgvector? | Lo probamos: la búsqueda híbrida ganaba por una pregunta (42 vs 41 de 43) pero empeoraba con las preguntas ciegas (ADR-09). Con 31 trozos, la similitud en Python es suficiente y más simple de mantener. | Eric · Sebastián |
| 8 | ¿Cuál fue el peor problema y qué aprendieron? | H-IAC-01: un apply de OpenTofu reescribió a los tres clientes porque estaban en el inventario y no en el estado (C30). Revertimos en hub-gitops. Aprendimos a revisar el plan antes de aplicar y a importar lo existente; sigue abierto. | Sebastián · Yisel |
| 9 | ¿Cómo cumplen la Ley 1581 si hay IA de por medio? | Datos sintéticos, acceso por rol (cada cliente ve solo lo suyo, B07), redacción de secretos antes de guardar o enviar al modelo (D05) y modelo local: ningún dato sale a servicios externos. | Yisel · Eric |
| 10 | ¿Qué valor tiene para el negocio de la agencia? | Menos tiempo caído y con datos: detección en 48–49 s contra un cliente que llamaba, recuperación en 3,4 min y tableros que muestran si se cumple el SLO vendido y el costo por cliente. Costo de una caída para una pyme local: no lo medimos [PENDIENTE]. | Yisel · Nicolás |
| 11 | ¿Por qué cambiaron ComfyUI por voz? ¿Cumple lo multimodal? | ComfyUI pedía unos 5 GB de VRAM que ya ocupaba el modelo de 7B (4.535 MiB). La voz es audio, otra modalidad: entrada hablada y salida hablada en CPU, con un error de palabras del 5,8 % (D11) y probada en un navegador real (D12). | Eric · Andrés |
| 12 | ¿Cómo sabemos que esto se reproduce y no funcionó una sola vez? | Un clon limpio arranca en 23 s con caché y pasa sus pruebas (F01); la corrida de 83 verificaciones se repite con `bash entrega/evidencias/correr.sh` y deja registro de cada paso. | Nicolás · Sebastián |
| 13 | ¿Cómo definieron los SLO y las alertas? | El SLO es el del plan (99,0 / 99,5 / 99,9 %); el SLI, la fracción de sondeos exitosos cada 5 s. Alertas de presupuesto de error en varias ventanas según el SRE Workbook (14,4× y 3×). Límite: las caídas de menos de 30 s no abren incidente (C28). | Eric · Andrés |
| 14 | ¿Cómo se repartió el trabajo y cómo usaron la IA en el desarrollo? | Por especificaciones, una tarea a la vez, con revisión por PR. Usamos agentes en Claude Code para auditar y mejorar, con una lista de comprobación para código asistido por IA en cada PR (bitácora en el complementario 04). [PENDIENTE: responsabilidad principal de cada integrante, que la ficha aún no tiene.] | Yisel · Nicolás |
| 15 | ¿Por qué la rama dev no está protegida? | Es la rama de integración para pruebas; lo reconocemos como riesgo medio en el análisis de riesgos y es un próximo paso: activar la protección y exigir PR. | Andrés · Nicolás |

---

## Resumen para el equipo: supuestos, pendientes y contradicciones

### Supuestos que tomé
- **«Carpeta de Drive v1.3» = `Entrega_Final_CloudForge/`.** El enlace venía vacío en la instrucción, así que usé el informe `…_v1.3.docx` y los complementarios 01–06 del 18 nov (marcados «versión 1.3»). Ignoré el informe sin sufijo del 16 nov y `entrega/00-informe/`.
- **Identidad de `clase electiva 2.pptx`, diseño libre.** La portada es la de la plantilla. Las demás usan su layout de contenido (logos y líneas doradas), su paleta y la tipografía Aptos, pero cada diapositiva tiene su propio diseño. Usa las imágenes reales del proyecto, recortadas para que se vean grandes: los diagramas de `docs/arquitectura/png/` (C4-2, C4-3, vista física, CI y puerta) y capturas del paquete de evidencias (tablero, portal, cambios, Argo CD, Grafana y asistente con voz). El texto va en pocas palabras y a 16 pt o más; el detalle está en las notas.
- **Datos de la CNCF** (89 % cloud native, 80 % Kubernetes en producción, 77 % GitOps): vienen de la v4 y los verifiqué en la fuente (CNCF, 1 abr. 2025). Las demás cifras externas de la v4 (52 % CIPE, 36 mil millones de Fortinet, GitGuardian) no las usé porque no las volví a verificar.
- **Tiempos:** demo y preguntas son bloques aparte. Las diapositivas cubren los 30 min, más 2 de apoyo para la demo y 1 de referencias.
- **Nombres:** proyecto «CloudOps Client Hub», versión 1.3, sustentación el 30 nov 2026 (ficha 01).
- **Diagramas:** usé los PNG de alta resolución de `docs/arquitectura/png/` (la misma fuente draw.io del 18 nov que las figuras del informe v1.3), recortando el encabezado.

### Datos [PENDIENTE]
1. Porcentaje de pymes de Popayán o del Cauca con sitio web propio (DANE no lo publica para micronegocios en 2023–2024).
2. Costo de una caída para una pyme local (Uptime solo sirve como orden de magnitud).
3. Responsabilidad principal de cada integrante (ficha 01: `[COMPLETAR]`).
4. Fechas del ensayo general y del congelamiento (complementario 06: `[COMPLETAR]`).
5. Entrevista con la empresa del caso (riesgo RC-04: `[COMPLETAR]`).
6. Contactos de operación en el runbook 05 (`[COMPLETAR]`).

### Contradicciones o inconsistencias encontradas (no elegí: hay que decidir)
1. **Tablas de la base:** el informe v1.3 dice 22 tablas (23 con `alembic_version`); el diagrama C4-2 y la vista 4+1 dicen «21 tablas/entidades».
2. **Figura 4 del informe v1.3:** el título dice «Vista de despliegue (modelo 4+1)», pero la imagen incrustada es la vista general 4+1. La vista física solo existe en `docs/arquitectura/png/08-4mas1-fisica.png`.
3. **`demo/guion.md` incluye crear un cliente con OpenTofu en vivo (minuto 12:30)**, justo lo que causó H-IAC-01. En el guion de arriba lo quité.
4. **`demo/guion.md` dice «presenta una sola persona»**, mientras que la consigna pide operador y narradores. Lo adapté.
5. **Escalado revertido:** RNF-04 y ADR-02 dicen 2 s (C20); PF-09 y H-OPS-02 dicen «~4 s». Son pruebas distintas, pero conviene aclararlo si preguntan.
6. **URLs de la ficha 01 con https** (Argo CD, MLflow) frente al informe sin protocolo. Es menor.
7. **Nota de la tabla de alcance del informe:** cita `RESUME.md`, que no existe; el archivo es `RESUMEN.md`.
8. **Nombre «Atalaya»:** aparece solo en el resumen ejecutivo («CloudOps Client Hub (Atalaya)»). No lo usé en la presentación.

### Fuentes externas verificadas
- Cancillería de Colombia (27 jun. 2025), con cifra de Confecámaras 2024: <https://cancilleria.gov.co/sala-de-prensa/noticias/colombia-conmemora-el-dia-internacional-de-las-microempresas-y-las-pequenas-y-medianas-empresas-destacando-su-papel-en-el-desarrollo-sostenible-la-politica-exterior-y-los-derechos-humanos>
- DANE, EMICRON 2024, resultados departamentales (julio 2025): <https://www.dane.gov.co/files/operaciones/EMICRON/pres-Departamentos-EMICRON-2024.pdf>
- Google, *Site Reliability Engineering*, cap. 1: <https://sre.google/sre-book/introduction/>
- Uptime Institute, *Annual outage analysis 2025* (resumen público): <https://intelligence.uptimeinstitute.com/resource/annual-outage-analysis-2025>

<!-- Sección 11 · Fuente: código, manifiestos, pruebas e historial de Git (no los .md). Candidatos y método en entrega/adr-candidatos.md -->
<!-- Regla: cada ADR tiene una línea «Evidencia» con ruta (y línea) o commit. Si el porqué no se pudo reconstruir, el ADR queda marcado [COMPLETAR]. -->

# Decisiones de arquitectura (ADR)

Esta sección registra las decisiones de arquitectura del proyecto en el formato ADR (Nygard, 2011) con identificador, estado, contexto, decisión, alternativas, consecuencias y evidencia). Cada decisión se incluyó solo si existe una huella verificable en el código, en los manifiestos, en las pruebas o en el historial de Git; el motivo se reconstruyó con el comentario de cabecera del archivo, con el mensaje del commit que introdujo el cambio o con la medición que lo respaldó. Cuando el repositorio no registra qué alternativas se evaluaron, el ADR lo dice en lugar de inventarlas. Las decisiones cuyo motivo no se puede reconstruir desde el repositorio aparecen al final, para que el equipo las confirme.

Los estados son: **Aceptada** (vigente), **Aceptada con riesgo** (vigente, con un riesgo conocido que se asume) y **Por confirmar** (falta el motivo).

::: {custom-style="Table Caption"}
**Tabla {T:adr}**\
*Registro de decisiones de arquitectura*
:::

| ID | Decisión | Dominio | Estado |
|-----|------------------------------------------|---------|--------|
| ADR-01 | GitOps con Argo CD: el Hub nunca habla con Kubernetes | Entrega | Aceptada |
| ADR-02 | El rollback es un commit que restaura la versión anterior | Entrega | Aceptada |
| ADR-03 | `hub-bot` solo escribe lo suyo en `hub-gitops` | Entrega | Aceptada |
| ADR-04 | Poda y autocorrección distintas según la Application | Entrega | Aceptada con riesgo |
| ADR-05 | Kustomize como fuente y un chart de Helm que debe dar lo mismo | Entrega | Aceptada |
| ADR-06 | OpenTofu, con código compatible con Terraform | Plataforma | Aceptada |
| ADR-07 | Migraciones de Alembic al arrancar, no `create_all` | Datos | Aceptada |
| ADR-08 | Columnas `jsonb` mediante una variante por dialecto | Datos | Aceptada |
| ADR-09 | Cosign sin registro de transparencia y registro por HTTP | Seguridad | Aceptada con riesgo |
| ADR-10 | La puerta de seguridad corre en Gitea; la CI de GitHub no firma | Seguridad | Aceptada |
| ADR-11 | Segregación de funciones configurable | Seguridad | Aceptada |
| ADR-12 | Red denegada por defecto, de entrada y de salida | Seguridad | Aceptada |
| ADR-13 | Pod Security `restricted`, sin root y raíz de solo lectura | Seguridad | Aceptada |
| ADR-14 | Política de contenido estricta en la consola web | Seguridad | Aceptada con riesgo |
| ADR-15 | Alloy como DaemonSet que lee por la API | Observabilidad | Aceptada |
| ADR-16 | Trazas sin texto de usuarios y sin consultas SQL | Observabilidad | Aceptada |
| ADR-17 | De la alerta al incidente por webhook, con huella única | Observabilidad | Aceptada |
| ADR-18 | Reportes en PDF con reportlab | Producto | Aceptada |
| ADR-19 | RAG propio dentro del Hub | IA | Aceptada |
| ADR-20 | Índice vectorial en una tabla, sin pgvector | IA | Aceptada con riesgo |
| ADR-21 | Modo de contexto configurable, `completo` por defecto | IA | Aceptada |
| ADR-22 | Compuerta de aprendizaje automático antes del modelo de lenguaje | IA | Aceptada |
| ADR-23 | Qwen2.5 7B Instruct como modelo del asistente | IA | Aceptada |
| ADR-24 | MLflow en el clúster con un solo proceso | IA | Aceptada |
| ADR-25 | Voz en CPU como modalidad adicional | IA | Aceptada |
| ADR-26 | Piper (GPL) aislado en su propio servicio | IA | Aceptada |
| ADR-27 | Un solo equipo para el clúster y la IA | Plataforma | Aceptada con riesgo |
| ADR-28 | Backstage y MLflow sin autenticación, solo en red local | Seguridad | Aceptada con riesgo |

::: {custom-style="Nota"}
*Nota.* Elaboración propia. El detalle de cada decisión sigue a la tabla; las decisiones por confirmar están en la Tabla {T:adr-pend}.
:::

## Entrega y GitOps

### ADR-01. GitOps con Argo CD: el Hub nunca habla con Kubernetes

**Estado.** Aceptada. **Contexto.** El Hub despliega los sitios de los clientes. Un Hub con credenciales de Kubernetes concentraría un privilegio alto en una aplicación expuesta a usuarios. **Decisión.** Todo cambio de despliegue es un commit en `hub-gitops` (Gitea) que Argo CD reconcilia; el Hub solo lee el estado desde la API de Argo CD y escribe en Git. La regla figura como prohibición en `CLAUDE.md`. **Alternativas.** El repositorio no registra otra alternativa evaluada; la prohibición fija esta como la única permitida. **Consecuencias.** Cada despliegue queda trazable y reversible por Git y el Hub no necesita credenciales de clúster; a cambio, el Hub depende de la disponibilidad de Gitea y de Argo CD.

*Evidencia.* `backend/app/integrations/argocd.py:2` («El Hub nunca habla con Kubernetes»), `backend/app/routers/services.py:110`, `CLAUDE.md` (sección Prohibido), `gitops/platform/argocd/applications/`.

### ADR-02. El rollback es un commit que restaura la versión anterior

**Estado.** Aceptada. **Contexto.** Revertir un despliegue debe ser rápido y quedar auditado. **Decisión.** El rollback escribe en `hub-gitops` un commit que deja la etiqueta de imagen anterior; Argo CD vuelve a esa versión. **Alternativas.** `git revert` literal: no es posible desde la API de Gitea, que no ofrece esa operación. **Consecuencias.** El resultado es el mismo que el de `git revert`, pero el historial muestra un commit nuevo y no una reversión; el Hub confirma la recuperación con el seguimiento de Argo CD y evita dos rollbacks simultáneos sobre el mismo servicio.

*Evidencia.* `backend/app/services/gitops_publish.py:92-93` («La API de Gitea no tiene `revert`»), `backend/app/services/rollback.py`, `backend/tests/test_rollback_publish.py`, commit `ea23c50`.

### ADR-03. `hub-bot` solo escribe lo suyo en `hub-gitops`

**Estado.** Aceptada (15 de noviembre de 2026). **Contexto.** El usuario `hub-bot` tenía escritura sobre todo `hub-gitops`; un token robado habría podido escribir un `ClusterRoleBinding` en `observability/`, que Argo CD aplicaría con el proyecto `default` (hallazgo K8-05 de la auditoría). **Decisión.** Una regla de protección de la rama `main` en Gitea deja empujar libremente solo al administrador; a los demás les permite cambiar únicamente `clients/*/kustomization.yaml`, `catalog-info.yaml` y `backend.yaml`, que es lo único que escribe el Hub. **Alternativas.** (a) Un proyecto de Argo CD más restrictivo: no cierra el riesgo porque `monitoring` necesita `ClusterRole` y `ClusterRoleBinding`. (b) Proteger `observability/`, `hub/`, `platform/` y `_base`: se descartó porque bloqueaba también al administrador y rompía la promoción. **Consecuencias.** Lo nuevo nace protegido por ser una lista de lo permitido; el equipo promueve con `gitops/sincronizar-hub-gitops.sh` usando la cuenta de administrador.

*Evidencia.* `gitops/proteccion_hub_gitops.py:1-6`, commit `4b1445e`, `backend/tests/test_proteccion_hub_gitops.py`, `gitops/pruebas/proteccion_hub_gitops.py`.

### ADR-04. Poda y autocorrección distintas según la Application

**Estado.** Aceptada con riesgo. **Contexto.** Argo CD puede borrar lo que sale de Git (`prune`) y revertir cambios manuales (`selfHeal`). **Decisión.** Los clientes y la observabilidad usan `prune: true` y `selfHeal: true`; el Hub, MLflow, Backstage y los respaldos usan `prune: false` con `selfHeal: true`, porque adoptan recursos que ya corrían, con volúmenes y datos, y un borrado por error en Git no debe llevarse un volumen ni un Secret. **Alternativas.** `prune: true` en todas: descartada para las aplicaciones con estado, según el comentario del propio manifiesto. **Consecuencias.** Renombrar un recurso del Hub deja vivo el anterior; ocurrió con una política de red, y por eso se conservó el nombre original.

*Evidencia.* `gitops/platform/argocd/applications/hub.yaml:24-26`, `gitops/hub/networkpolicy.yaml:17` (nombre conservado), `plataforma-mlops.yaml:3,25`, `cliente-restaurante.yaml:23-24`, `gitops/pruebas/drift.sh`.

### ADR-05. Kustomize como fuente y un chart de Helm que debe dar lo mismo

**Estado.** Aceptada (14 de noviembre de 2026). **Contexto.** Los sitios de clientes se describen con Kustomize (base y overlays) y el diplomado pide también Helm. **Decisión.** Kustomize es lo que Argo CD aplica; el chart `sitio-cliente` existe como segunda descripción y una prueba renderiza ambos para cada cliente y compara, objeto por objeto, que den lo mismo. **Alternativas.** Mantener solo uno de los dos: el repositorio no registra por qué no se eligió una sola herramienta; el motivo documentado es que el chart «no se desvíe de lo que Argo CD aplica de verdad». **Consecuencias.** Hay que mantener dos descripciones del mismo sitio y la prueba falla si divergen.

*Evidencia.* `gitops/charts/sitio-cliente/`, `gitops/pruebas/helm-vs-kustomize.sh:1-4`, `backend/tests/test_helm_chart.py`, commits `ded2969` y `a61a53e`.

## Plataforma

### ADR-06. OpenTofu, con código compatible con Terraform

**Estado.** Aceptada. **Contexto.** El diplomado pide infraestructura como código; la elección entre OpenTofu y Terraform estaba pendiente y la decidía el profesor. **Decisión.** El código en `infra/tofu/` se escribe en HCL común y se ejecuta con OpenTofu, en un contenedor con versión fija; la especificación 011 exige además que funcione con Terraform (CA-5) y se probó con ambos. **Alternativas.** Terraform como herramienta principal: se mantiene como comprobación de compatibilidad. **Consecuencias.** Se exige OpenTofu 1.10 o superior para el bloqueo de estado por archivo; el estado remoto con bloqueo se usa solo en laboratorio. **`[COMPLETAR: quién decidió OpenTofu y cuándo; el repositorio no lo registra]`.**

*Evidencia.* `infra/tofu/providers.tf:3`, `infra/tofu.sh`, `specs/011-infraestructura-como-codigo/plan.md:3`, commits `3d58973` y `3495540`, `infra/pruebas/drift.sh`.

### ADR-27. Un solo equipo para el clúster y la IA

**Estado.** Aceptada con riesgo. **Contexto.** El plan original repartía el trabajo entre un PC A de 16 GB (plataforma) y un PC B con GPU de 6 GB como mínimo (IA). El clúster actual corre en un solo equipo y llama a Ollama en el anfitrión. **Decisión.** El clúster k3d y Ollama comparten el mismo equipo; el Hub alcanza a Ollama por la dirección del anfitrión de Docker (`OLLAMA_URL=http://host.docker.internal:11434` en la API) y una política de red permite únicamente esa dirección y ese puerto. **Alternativas.** Dos equipos, como dice aún la constitución: la bitácora registra que la mudanza de MLflow al PC B quedó pendiente. **Consecuencias.** No hay alta disponibilidad; la GPU se comparte entre el modelo de lenguaje y los embeddings, y las pruebas se hicieron con una GPU de 8 GB, sin medir el caso de 6 GB. Si `OLLAMA_URL` cambia hay que cambiar el `ipBlock` de la política y su prueba. **`[COMPLETAR: confirmar la fecha y el motivo de descartar el PC B]`.**

*Evidencia.* `gitops/hub/networkpolicy.yaml:91-92`, `backend/app/config.py:51-52`, `docs/bitacora.md:640`, `constitution/tech-stack.md:69-70` (descripción anterior).

## Datos

### ADR-07. Migraciones de Alembic al arrancar, no `create_all`

**Estado.** Aceptada (1 de octubre de 2026). **Contexto.** El esquema empezó con `create_all` de SQLAlchemy, que no modifica tablas existentes. **Decisión.** Las tablas las crea y modifica Alembic con `alembic upgrade head` al arrancar el contenedor; hay 17 migraciones reversibles. **Alternativas.** `create_all`: se reemplazó en el commit `ae0e7c7` por la necesidad de evolucionar el esquema con datos. **Consecuencias.** Con varias réplicas hubo que evitar migraciones duplicadas (commit `de9f667`); `alembic check` solo es fiable contra PostgreSQL.

*Evidencia.* `backend/app/main.py:45`, `backend/alembic/versions/` (0001 a 0017), commits `ae0e7c7` y `de9f667`, `backend/tests/test_migrations.py`.

### ADR-08. Columnas `jsonb` mediante una variante por dialecto

**Estado.** Aceptada (16 de noviembre de 2026). **Contexto.** Las columnas de documentos eran `json`, un texto que se vuelve a analizar en cada lectura (hallazgo BD-04 de la auditoría); las pruebas corren sobre SQLite. **Decisión.** Un tipo `JSON_DOC` usa `jsonb` en PostgreSQL y `json` en los demás dialectos; la migración 0017 convierte las columnas solo en PostgreSQL. **Alternativas.** Mantener `json`, o usar `jsonb` y dejar de probar con SQLite: no constan evaluadas. **Consecuencias.** Dos dialectos que probar; la migración 0017 se detiene y lista los correos que solo difieren por mayúsculas en lugar de elegir uno.

*Evidencia.* `backend/app/db.py:38`, `backend/alembic/versions/0017_esquema_afinado.py:1-8`, commit `b187725`.

## Seguridad

### ADR-09. Cosign sin registro de transparencia y registro por HTTP

**Estado.** Aceptada con riesgo. **Contexto.** El laboratorio opera sin Internet y sin certificados. **Decisión.** Las imágenes se firman con Cosign con `--tlog-upload=false`, y la firma, la procedencia (SLSA) y el SBOM se verifican con la clave pública del Hub; el registro de Gitea se usa por HTTP. **Alternativas.** Subir la firma a un registro de transparencia (Rekor) y usar TLS con una autoridad propia: exigiría desplegar ambos. **Consecuencias.** No hay prueba pública de la firma y la verificación ocurre en el pipeline, no dentro del clúster (límite declarado).

*Evidencia.* `pipelines/puerta.sh:205,221,228,247`, `docs/bitacora.md:550`, `gitops/platform/politicas/imagenes-de-clientes.yaml`.

### ADR-10. La puerta de seguridad corre en Gitea; la CI de GitHub no firma

**Estado.** Aceptada. **Contexto.** La CI de GitHub no alcanza el registro del laboratorio. **Decisión.** Gitleaks, pruebas, construcción, Trivy, Syft y Cosign corren en Gitea Actions (`pipelines/puerta.yaml`) con un ejecutor endurecido; la CI de GitHub hace lint, pruebas, escaneos y conserva Trivy y el SBOM como artefactos, pero no firma ni publica la imagen del Hub. **Alternativas.** Publicar desde GitHub: descartado por la razón anterior. **Consecuencias.** La puerta de Gitea no prueba la imagen del Hub. **`[COMPLETAR: por qué Gitea con Actions en el clúster y no solo GitHub Actions]`.**

*Evidencia.* `pipelines/puerta.yaml`, `.github/workflows/ci.yml:22-69`, commits `89d3f1a` y `97abc71`, `docs/bitacora.md:549`.

### ADR-11. Segregación de funciones configurable

**Estado.** Aceptada (15 de noviembre de 2026). **Contexto.** El módulo de DevSecOps exige que quien pide un cambio no lo apruebe. **Decisión.** La aprobación se rechaza si el aprobador es quien solicitó el cambio; el control se activa con `segregacion_funciones` (verdadero por defecto) y queda registrado en la bitácora. **Alternativas.** Sin control: el campo configurable permite desactivarlo. **Consecuencias.** La demostración necesita dos cuentas de agencia.

*Evidencia.* `backend/app/config.py:15`, `backend/app/routers/change_requests.py:181`, `backend/tests/test_segregacion_funciones.py`, commit `0df5901`, `specs/018-cierre-modulo-3/spec.md` (CA-5).

### ADR-12. Red denegada por defecto, de entrada y de salida

**Estado.** Aceptada (14 a 16 de noviembre de 2026). **Contexto.** El namespace `hub` salía a cualquier destino: un Hub o un Backstage comprometidos podían llegar a MLflow, a Alertmanager, a los sitios de los clientes, a la API de Kubernetes y a Internet (hallazgo K8-02). **Decisión.** Cada namespace (`hub`, `monitoring`, `gitea`, `mlops` y los clientes) lleva `default-deny` de entrada y de salida y políticas que abren solo lo necesario; hay pruebas de red por namespace. **Alternativas.** Red abierta dentro del clúster (el estado anterior). **Consecuencias.** Cambiar un destino exige cambiar la política y su prueba de CI; la prueba del namespace `hub` falla en 7 de 21 comprobaciones sin la política.

*Evidencia.* `gitops/hub/networkpolicy.yaml:8`, `gitops/clients/_base/networkpolicy.yaml:11,36`, `gitops/pruebas/salida-hub.sh`, `gitops/pruebas/aislamiento-red.sh`, commits `0891567`, `4acc8a0` y `90db644`.

### ADR-13. Pod Security `restricted`, sin root y raíz de solo lectura

**Estado.** Aceptada. **Contexto.** Los contenedores de clientes y del Hub no deben correr como root ni escribir en su sistema de archivos. **Decisión.** Los namespaces aplican Pod Security `restricted` (Kubernetes, s. f.); los Pods fijan `runAsNonRoot` y `readOnlyRootFilesystem` y escriben solo en volúmenes `emptyDir`; las imágenes propias usan usuarios sin privilegios (`USER 10001` en el backend; `nginx-unprivileged` con `USER 101` en la web, que usa root únicamente para actualizar paquetes). **Alternativas.** Excepciones de Trivy para contenedores con raíz escribible: se cerró la excepción KSV-0014 en los sitios de clientes. **Consecuencias.** Hubo que mover el tema inicial de la web a un archivo y montar volúmenes temporales.

*Evidencia.* `gitops/platform/namespaces.yaml:10-13`, `gitops/hub/api.yaml:25,98`, `gitops/clients/_base/deployment.yaml:32,45`, `backend/Dockerfile:38`, `frontend/Dockerfile:15-22`, commit `83ba183`, `gitops/pruebas/pod-security.sh`.

### ADR-14. Política de contenido estricta en la consola web

**Estado.** Aceptada con riesgo (16 de noviembre de 2026). **Contexto.** La consola procesa sesiones de agencia y de clientes. **Decisión.** Cabecera `Content-Security-Policy` con `script-src 'self'` (sin `unsafe-eval` y sin scripts en línea; el tema inicial se movió a `frontend/public/tema-inicial.js`) y recursos solo del propio origen. **Alternativas.** Permitir scripts en línea: descartado porque Vite no deja ninguno. **Consecuencias.** Los estilos en línea sí se permiten (los gráficos SVG y React los usan); las pruebas de navegador no pueden usar `wait_for_function`, que evalúa cadenas, y se reemplazó por una espera propia.

*Evidencia.* `frontend/seguridad.conf:3-5`, `frontend/public/tema-inicial.js`, `voz/pruebas/navegador.py`, commit `e2afdcd`.

## Observabilidad

### ADR-15. Alloy como DaemonSet que lee por la API

**Estado.** Aceptada (14 de noviembre de 2026). **Contexto.** Los registros de los Pods de los clientes deben llegar a Loki. **Decisión.** Un Pod de Alloy por nodo recoge solo los registros de los Pods de su nodo leyéndolos por la API de Kubernetes, sin root y sin montar carpetas del nodo. **Alternativas.** Un Deployment único: no escalaría con nodos; el cambio a DaemonSet consta en el historial. **Consecuencias.** Más CPU y sondas más tolerantes para que no se reinicie en bucle con el equipo cargado.

*Evidencia.* `observability/alloy/` (comentario de cabecera), commits `6fdd4f8`, `d349ebc` y `54342ad`.

### ADR-16. Trazas sin texto de usuarios y sin consultas SQL

**Estado.** Aceptada. **Contexto.** Las trazas se guardan en Tempo y las lee quien opera la plataforma. **Decisión.** Los spans no llevan el texto de preguntas ni de respuestas del asistente ni el cuerpo de las peticiones, y no hay spans de SQL; `/health` y `/livez` se excluyen. **Alternativas.** Spans con contenido: descartado por privacidad. La instrumentación de SQLAlchemy de OpenTelemetry tampoco soporta la versión 2.1 que usa el Hub. **Consecuencias.** Menos detalle al depurar; los atributos útiles (decisión de la compuerta, modo de contexto, puntaje de recuperación) sí se registran.

*Evidencia.* `backend/app/telemetry.py:1-5,39-40`, `backend/app/services/assistant.py:60-72`, `backend/tests/test_telemetry.py`.

### ADR-17. De la alerta al incidente por webhook, con huella única

**Estado.** Aceptada (24 de octubre de 2026). **Contexto.** El incidente debe abrirse solo, sin esperar que el cliente llame. **Decisión.** Prometheus evalúa `SitioCaido` (sondeo cada 5 s, 30 s sostenidos); Alertmanager llama a un webhook del Hub, que abre un incidente P1 con la hora real de la caída; la huella de la alerta tiene un índice único para no duplicar. **Alternativas.** Notificar por correo o chat: no hay canal externo configurado. **Consecuencias.** Las alertas de plataforma (`HubCaido`, memoria, disco) no avisan a nadie fuera de Alertmanager.

*Evidencia.* `observability/prometheus/reglas/sitios.yml:1-12`, `backend/app/services/incident_alerts.py:30-42`, commit `767a044` (migración 0008), `backend/app/routers/alerts.py:27`.

## Producto

### ADR-18. Reportes en PDF con reportlab

**Estado.** Aceptada (14 de noviembre de 2026). **Contexto.** El plan 013 proponía WeasyPrint con Jinja2. **Decisión.** Se usa reportlab, una biblioteca de Python puro. **Alternativas.** WeasyPrint: exige Pango y otras bibliotecas del sistema en la imagen. **Consecuencias.** La imagen de producción pasó de 308 a 371 MB (con Pillow y OpenTelemetry); el reporte ejecutivo se encoge para caber siempre en una página.

*Evidencia.* `backend/requirements.txt:13`, `backend/app/services/report_pdf.py:2`, `docs/bitacora.md:546`.

## Inteligencia artificial

### ADR-19. RAG propio dentro del Hub

**Estado.** Aceptada (14 de noviembre de 2026). **Contexto.** La constitución nombraba AnythingLLM como servicio de RAG. **Decisión.** El Hub implementa el RAG: trozos de la ayuda con embeddings de `nomic-embed-text` servidos por Ollama, guardados en PostgreSQL y consultados por similitud coseno. **Alternativas.** AnythingLLM: habría sumado un servicio en un equipo con RAM y GPU justas. **Consecuencias.** Todo queda versionado en el Hub y se prueba con simulaciones y sin red; la decisión se aparta de la constitución, que se actualizó, aunque quedan menciones antiguas en `README.md`. La rúbrica del diplomado evalúa la capacidad y no la marca.

*Evidencia.* `backend/app/services/knowledge.py`, `backend/app/services/assistant_context.py`, `backend/app/models/knowledge.py`, commits `cc1b5a1` y `b356f00`, `constitution/tech-stack.md:62`.

### ADR-20. Índice vectorial en una tabla, sin pgvector

**Estado.** Aceptada con riesgo. **Contexto.** El índice contiene 31 trozos. **Decisión.** El vector se guarda como lista de números en una columna de documentos y el coseno se calcula en Python; no se usa pgvector. **Alternativas.** pgvector, evaluado con el experimento `ai/eval/experimento_hibrido.py` (43 preguntas con embeddings reales): con K=4 empatan en 41 de 43, y la variante híbrida sube a 42 de 43 pero pierde 1 de 12 en el conjunto ciego. **Consecuencias.** No cambia la imagen de PostgreSQL ni el manifiesto, funciona igual en PostgreSQL y SQLite; no escala a miles de trozos, donde habría que pasar a pgvector.

*Evidencia.* `backend/app/models/knowledge.py:1-2`, `backend/app/services/knowledge.py:74`, `ai/eval/experimento_hibrido.py`, commit `b47da03`, `docs/bitacora.md:545`.

### ADR-21. Modo de contexto configurable, `completo` por defecto

**Estado.** Aceptada. **Contexto.** El asistente puede enviar al modelo toda la ayuda (`completo`) o solo los trozos más parecidos (`rag`). **Decisión.** El modo se elige con `ASSISTANT_CONTEXT_MODE`; el valor por defecto es `completo` porque puntúa más en el conjunto de ajuste (97,5 % frente a 92,5 %), y el clúster usa `rag`. **Alternativas.** `rag` como valor por defecto. **Consecuencias.** Quien quiera mostrar el RAG debe fijar la variable; seis pruebas del asistente suponen el valor por defecto y fallan con otro (ver la sección de pruebas funcionales).

*Evidencia.* `backend/app/config.py:64`, `backend/app/services/assistant.py:37`, `docs/bitacora.md:622`, `docker-compose.yml:69`.

### ADR-22. Compuerta de aprendizaje automático antes del modelo de lenguaje

**Estado.** Aceptada (14 de noviembre de 2026). **Contexto.** Cada llamada al modelo de 7 B ocupa la GPU; muchas preguntas no tratan del Hub. **Decisión.** Un clasificador Naive Bayes en Python puro, con inferencia sobre un JSON de conteos, decide si la pregunta es del tema antes de despertar al modelo; se entrena con `ai/classifier/train.py` y se registra y promueve en MLflow. Una guarda de vocabulario nunca omite el modelo si aparece un término del Hub. **Alternativas.** Dejar que el modelo decida; el clasificador también puede servirse como modelo remoto (`gate_model_url`). **Consecuencias.** Exactitud de 95,8 % sobre 24 ejemplos de prueba, con 0 preguntas del Hub dejadas sin modelo y 91,7 % de llamadas evitadas; la muestra es pequeña y la cifra es orientativa.

*Evidencia.* `ai/classifier/train.py:1,97`, `backend/app/services/assistant_gate.py:1-4`, `backend/app/config.py:58`, `docs/modelos/compuerta-asistente.md`, commit `b3a5126`, `backend/tests/test_gate_remota.py`.

### ADR-23. Qwen2.5 7B Instruct como modelo del asistente

**Estado.** Aceptada (14 de noviembre de 2026). **Contexto.** El asistente, los borradores y el diagnóstico necesitan un modelo local con español aceptable, que quepa en la GPU del equipo. **Decisión.** `qwen2.5:7b-instruct` (Q4_K_M, licencia Apache 2.0) vía Ollama. **Alternativas.** (a) Qwen2.5 3B: más rápido (1,72 s frente a 3,61 s) y con menos memoria (2.063 MiB frente a 4.535 MiB), pero con 87,5 % en el conjunto de ajuste (inventó un paso) frente a 97,5 % del 7 B; no son comparables del todo, porque el 3 B se probó en modo `secciones` y el 7 B en modo `completo`; además su licencia es solo de investigación, por lo que se usa únicamente para comparar. (b) Llama 3.1 8B: figuraba como opción en la constitución. **Consecuencias.** 33,7 tokens/s y arranque en frío de 12,6 s; un modelo de 7 B no se blinda del todo contra la inyección de instrucciones (resiste 9 de 10). **`[COMPLETAR: Llama 3.1 8B no tiene medición en el repositorio; confirmar si se evaluó]`.**

*Evidencia.* `backend/app/config.py:52`, `docs/modelos/qwen2.5-7b-instruct.md`, `docs/modelos/qwen2.5-3b-instruct.md`, `ai/eval/medir_modelos.py`, commits `b356f00` y `4a05853`.

### ADR-24. MLflow en el clúster con un solo proceso

**Estado.** Aceptada (14 de noviembre de 2026). **Contexto.** El registro de modelos debía vivir en el clúster con un límite de memoria de 512 MB. **Decisión.** Imagen propia de MLflow con `MLFLOW_SERVER_ENABLE_JOB_EXECUTION=false` y `--workers 1`. **Alternativas.** La configuración por defecto: usaba cerca de 1,8 GB y 267 procesos, y el contenedor moría. **Consecuencias.** Se pierden funciones de MLflow que no se usan.

*Evidencia.* `ai/servidor-mlflow/Dockerfile:5,11-14`, `gitops/platform/mlops/`, commit `9ef0377`, `docs/bitacora.md:625`.

### ADR-25. Voz en CPU como modalidad adicional

**Estado.** Aceptada (15 de noviembre de 2026). **Contexto.** El diplomado pide una modalidad multimodal adicional. El plan original era imagen con Stability Matrix y ComfyUI (Stable Diffusion 1.5), que pedía unos 5 GB de VRAM y turnos de GPU. **Decisión.** Voz del asistente con faster-whisper `small` para transcribir y Piper para hablar, ambos en CPU y en un servicio aparte; el audio no se guarda. **Alternativas.** (a) faster-whisper `base`: 3,5 veces más rápido que el audio y con 433 MiB, pero con 84,1 % de términos del Hub bien transcritos y 9,1 % de error de palabras. (b) Imagen, video y 3D: fuera de alcance por el consumo de GPU. **Consecuencias.** `small` acierta 93,7 % de los términos del Hub y 6,6 % de error de palabras, a costa de 1,9 s por transcripción y 1.188 MiB; la medición usa voz sintetizada limpia (el mejor caso). La infografía de la especificación 014 queda como mejora y el módulo 6 cubre solo audio. **`[COMPLETAR: confirmar con el profesor que el audio cubre el módulo 6]`.**

*Evidencia.* `voz/Dockerfile:23`, `voz/descargar_modelos.py:15,50`, `docs/modelos/faster-whisper-small.md`, `docs/modelos/faster-whisper-base.md`, `constitution/tech-stack.md:63`, commits `370bac7` y `c90bccb`.

### ADR-26. Piper (GPL) aislado en su propio servicio

**Estado.** Aceptada (15 de noviembre de 2026). **Contexto.** El motor `piper-tts` 1.8.0 tiene licencia GPL-3.0 o posterior. **Decisión.** Piper corre en el servicio `voz/`, al que el Hub llama por HTTP sin importar su código. **Alternativas.** Importar Piper dentro de la API: el Hub quedaría alcanzado por la GPL. **Consecuencias.** El Hub no queda cubierto por la GPL, pero si la imagen `hub-voz` se entrega a un tercero hay que acompañarla de su código fuente.

*Evidencia.* `docs/modelos/README.md:54-58`, `backend/app/integrations/voz.py`, `voz/Dockerfile`, commit `b490789`.

## Riesgos aceptados

### ADR-28. Backstage y MLflow sin autenticación, solo en red local

**Estado.** Aceptada con riesgo. **Contexto.** Backstage y MLflow se usan en la red local de la demostración. **Decisión.** Backstage permite el acceso de invitado (`dangerouslyAllowOutsideDevelopment`) y MLflow no tiene autenticación; la entrada a MLflow se limita a Traefik y a su namespace por política de red, y Backstage solo se sirve por HTTPS. **Alternativas.** Autenticación de ambos: no se hizo; el equipo la clasificó como riesgo aceptado, no como olvido. **Consecuencias.** Quien llegue a la red local ve el catálogo y los modelos; no se debe exponer a Internet.

*Evidencia.* `gitops/platform/backstage/app-config.hub.yaml:29-33`, `gitops/platform/mlops/`, `backend/tests/test_entrada_de_mlops.py`, `docs/bitacora.md:551`, commit `903210a`.

## Decisiones por confirmar

El repositorio muestra la huella de estas decisiones pero no su motivo. El equipo debe responder cada pregunta antes de convertirlas en ADR.

::: {custom-style="Table Caption"}
**Tabla {T:adr-pend}**\
*Decisiones sin motivo reconstruible desde el repositorio*
:::

| Decisión | Huella | Pregunta para el equipo |
|------------|---------------------|------------------------------|
| k3d y k3s con Traefik como entrada | `gitops/platform/k3s/crear-cluster.sh` | `[COMPLETAR: ¿por qué k3s y no otro Kubernetes ligero como kind o minikube?]` |
| Gitea con Actions y registro dentro del clúster | `pipelines/puerta.yaml`, `gitops/platform/gitea/` | `[COMPLETAR: ¿por qué un Git propio además de GitHub?]` |
| Backstage como catálogo y plantillas | `gitops/platform/backstage/` | `[COMPLETAR: ¿qué otras opciones de portal se consideraron?]` |
| PostgreSQL 16 como base del Hub | `docker-compose.yml`, `gitops/hub/postgres.yaml` | `[COMPLETAR: ¿por qué PostgreSQL y no otro motor?]` |

::: {custom-style="Nota"}
*Nota.* Elaboración propia a partir de la revisión del código y del historial de Git del 16 de noviembre de 2026.
:::

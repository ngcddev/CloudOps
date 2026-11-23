<!-- Sección 12 · Fuente: gitops/, observability/, backend/app/, docker-compose.yml, constitution/ (descripción anterior de hardware ya corregida: ver ADR-27) -->
<!-- Los diagramas los dibuja el equipo: cada marcador [FIGURA ...] dice qué elementos, relaciones y fronteras debe tener. -->

# Diagramas de arquitectura

La arquitectura se describe con el modelo C4 (Brown, s. f.), en sus niveles de contexto, contenedores y componentes, con una vista de despliegue organizada según el modelo 4+1 (Kruchten, 1995) y con un diagrama de flujo de datos. Todas las vistas se organizan en siete dominios: código, entrega, artefactos, ejecución, plataforma, operación e inteligencia artificial (Tabla {T:dominios}). Cada figura se acompaña de la descripción de lo que debe mostrar; los diagramas se incorporan en el lugar del marcador.

::: {custom-style="Table Caption"}
**Tabla {T:dominios}**\
*Dominios de la arquitectura y sus componentes*
:::

| Dominio | Componentes | Dónde está en el repositorio |
|-------|--------------------------------|------------------------|
| Código | Repositorio Git con la aplicación (`backend/`, `frontend/`, `voz/`, `ai/`), la infraestructura (`infra/`, `gitops/`, `observability/`, `pipelines/`) y las especificaciones (`specs/`); ramas y commits con la convención del proyecto | `CLAUDE.md`, `constitution/conventions.md` |
| Entrega | CI de GitHub (lint, pruebas, escaneos) y puerta de seguridad en Gitea Actions (Gitleaks, pruebas, construcción, Trivy, Syft, Cosign) con un ejecutor propio | `.github/workflows/ci.yml`, `pipelines/puerta.yaml` |
| Artefactos | Registro de contenedores de Gitea, SBOM y atestaciones, repositorio de configuración `hub-gitops`, registro de modelos de MLflow y modelos de Ollama | `gitops/platform/gitea/`, `ai/servidor-mlflow/` |
| Ejecución | Clúster k3d `k3d-hub` con los espacios `hub`, `argocd`, `monitoring`, `gitea`, `mlops` y uno por cliente; API del Hub, consola web, PostgreSQL, servicio de voz y los sitios de los clientes | `gitops/hub/`, `gitops/clients/` |
| Plataforma | Argo CD, Traefik (entrada), Backstage, políticas de red, Pod Security, política de admisión de imágenes y respaldos programados | `gitops/platform/` |
| Operación | Prometheus, Alertmanager, Blackbox Exporter, kube-state-metrics, Loki, Alloy, Tempo, Grafana y los procedimientos de operación | `observability/`, `runbooks/` |
| IA | Ollama (`qwen2.5:7b-instruct`, `nomic-embed-text`), compuerta de aprendizaje automático, RAG, servicio de voz (faster-whisper y Piper) y MLflow | `ai/`, `voz/`, `backend/app/services/assistant*.py` |

::: {custom-style="Nota"}
*Nota.* Elaboración propia a partir de la estructura del repositorio y de los manifiestos del 16 de noviembre de 2026.
:::

## Contexto (C4, nivel 1)

El sistema CloudOps Client Hub lo usan tres tipos de persona: el administrador y el técnico de la agencia (rol `agencia`) y el cliente PyME (rol `cliente`). El Hub no depende de servicios de Internet para operar: sus únicos sistemas vecinos son la plataforma de entrega (Gitea y Argo CD), la telemetría (Prometheus y Alertmanager) y el servidor de modelos local (Ollama).

::: {custom-style="Image Caption"}
**Figura {F:c4-contexto}**\
*Diagrama de contexto del sistema (C4, nivel 1)*
:::

[FIGURA F-01 · Contexto del sistema CloudOps Client Hub · Una caja central CloudOps Client Hub rodeada de tres personas (administrador de la agencia, técnico de la agencia y cliente PyME) con flechas hacia el sistema rotuladas gestionar clientes, atender incidentes y consultar el portal. A la derecha cuatro sistemas vecinos con flechas rotuladas: Gitea hub-gitops (escribe commits de versión y rollback), Argo CD (lee estado de sincronización), Prometheus y Alertmanager (envían alertas por webhook y se consultan métricas) y Ollama (recibe preguntas y devuelve texto). Un borde exterior rotulado laboratorio sin Internet. Los sitios de los clientes aparecen como sistema externo monitoreado por el Hub]

::: {custom-style="Nota"}
*Nota.* Elaboración propia. Fuentes: `docs/requerimientos.md` (actores) y `backend/app/integrations/`.
:::

## Contenedores (C4, nivel 2)

La consola web (React servida por nginx sin privilegios) llama a la API del Hub (FastAPI), que guarda sus datos en PostgreSQL. La API escribe en Gitea, lee de Argo CD, Prometheus y Loki, llama a Ollama y al servicio de voz y recibe alertas de Alertmanager y eventos de la puerta de seguridad. Todo se despliega como contenedores y todo, salvo Ollama, corre dentro del clúster.

::: {custom-style="Image Caption"}
**Figura {F:c4-contenedores}**\
*Diagrama de contenedores (C4, nivel 2)*
:::

[FIGURA F-02 · Contenedores del Hub y de la plataforma · Frontera clúster k3d con cinco espacios. Espacio hub: consola web (React y nginx, puerto 8080), API del Hub (FastAPI), PostgreSQL 16 con volumen, servicio de voz (faster-whisper y Piper) y Backstage. Espacio argocd: Argo CD. Espacio gitea: Gitea con registro de contenedores y repositorio hub-gitops. Espacio monitoring: Prometheus, Alertmanager, Blackbox Exporter, kube-state-metrics, Loki, Alloy como DaemonSet, Tempo y Grafana. Espacio mlops: MLflow. Un espacio cliente-nombre por cliente con el sitio. Fuera del clúster: Ollama en el anfitrión y el ejecutor de Gitea Actions. Flechas: navegador a Traefik a consola web y API; API a PostgreSQL; API a Gitea; Argo CD lee Gitea y aplica a los espacios de clientes; Blackbox sondea los sitios; Prometheus a Alertmanager y de ahí al webhook de la API; Alloy a Loki; API a Tempo; API a Ollama y a voz]

::: {custom-style="Nota"}
*Nota.* Elaboración propia. Fuentes: `gitops/platform/namespaces.yaml`, `gitops/hub/`, `observability/` y `gitops/platform/argocd/applications/`.
:::

## Componentes de la API (C4, nivel 3)

La API se organiza en tres capas: routers (HTTP y autorización), servicios (reglas de negocio) e integraciones (clientes de sistemas externos), sobre los modelos de datos. Las reglas de negocio viven en `services/`, no en los routers.

::: {custom-style="Table Caption"}
**Tabla {T:componentes}**\
*Componentes de la API del Hub por capa*
:::

| Capa | Componentes | Responsabilidad |
|-----|---------------------|-------------------------------|
| Routers (`backend/app/routers/`) | `auth`, `clients`, `services`, `tickets`, `change_requests`, `incidents`, `alerts`, `pipeline`, `security`, `dashboard`, `reports`, `ai_drafts`, `assistant`, `audit_logs`, `catalog` | Contratos HTTP, validación de entrada y control de acceso por rol |
| Servicios (`backend/app/services/`) | `priority`, `sla`, `ticket_flow`, `change_flow`, `gitops_publish`, `kustomization`, `rollback`, `deploy_watch`, `incident_alerts`, `incident_flow`, `security_gate`, `kpi`, `reports`, `report_pdf`, `ai_drafts`, `aiops`, `assistant`, `assistant_gate`, `assistant_context`, `knowledge`, `redaccion`, `audit`, `provisioning` | Reglas de negocio: prioridades, SLA, flujos de estados, publicación por GitOps, rollback, puerta de seguridad, indicadores, IA |
| Integraciones (`backend/app/integrations/`) | `gitea`, `argocd`, `prometheus`, `loki`, `ollama`, `voz` | Clientes de los sistemas externos con tiempos de espera acotados |
| Transversales | `deps` (sesión y roles), `telemetry` (trazas), `db` y `models/` (acceso a datos), `config` (variables de entorno), `limite_cuerpo` (tamaño de petición) | Autenticación, observabilidad y límites |
| Tareas de fondo | Vigilante de despliegues (`deploy_watch`) con candado para que solo una réplica lo ejecute | Confirmar cada publicación y cada rollback leyendo Argo CD |

::: {custom-style="Nota"}
*Nota.* Elaboración propia a partir de `backend/app/`. El vigilante usa un candado de base de datos (`backend/app/services/bloqueos.py`) para que varias réplicas no dupliquen el trabajo.
:::

::: {custom-style="Image Caption"}
**Figura {F:c4-componentes}**\
*Diagrama de componentes de la API del Hub (C4, nivel 3)*
:::

[FIGURA F-03 · Componentes de la API del Hub · Tres capas apiladas dentro de la caja API del Hub. Capa superior de routers agrupados por función: acceso (auth), negocio de clientes (clients, services, catalog), mesa de servicio (tickets, change_requests), incidentes (incidents, alerts), seguridad (pipeline, security, audit_logs), tableros y reportes (dashboard, reports) e IA (assistant, ai_drafts). Capa intermedia de servicios con flechas desde cada router a sus servicios, por ejemplo incidents a incident_flow, rollback y sla, change_requests a change_flow y gitops_publish, assistant a assistant_gate, knowledge y redaccion. Capa inferior de integraciones hacia Gitea, Argo CD, Prometheus, Loki, Ollama y voz. A un lado, modelos y PostgreSQL; arriba, deps como filtro de autenticación y roles; el vigilante de despliegues como componente de fondo]

::: {custom-style="Nota"}
*Nota.* Elaboración propia. Fuente: `backend/app/` (ver Tabla {T:componentes}).
:::

## Despliegue (vista física del modelo 4+1)

El modelo 4+1 describe la arquitectura con cinco vistas. La Tabla {T:vistas} indica dónde se documenta cada una; la vista física es el diagrama de despliegue.

::: {custom-style="Table Caption"}
**Tabla {T:vistas}**\
*Vistas del modelo 4+1 y su documentación*
:::

| Vista | Qué muestra | Dónde se documenta |
|-------|--------------------|------------------------|
| Lógica | Entidades y servicios del Hub | Sección de modelo de datos y Tabla {T:componentes} |
| Procesos | Flujos concurrentes: alertas, vigilante de despliegues, pipeline | Sección de diagramas de secuencia |
| Desarrollo | Organización del código y de las ramas | Tabla {T:dominios} y `constitution/conventions.md` |
| Física | Dónde corre cada componente | Figura {F:despliegue} |
| Escenarios | Casos de uso que unen las cuatro vistas | Sección de casos de uso y caso del restaurante |

::: {custom-style="Nota"}
*Nota.* Elaboración propia.
:::

El despliegue de laboratorio usa un solo equipo con Docker Desktop. El clúster k3d tiene un nodo servidor y un balanceador; el estado de OpenTofu y el ejecutor de Gitea Actions corren como contenedores fuera del clúster; Ollama corre en el anfitrión y el clúster lo alcanza por la dirección del anfitrión de Docker (ver ADR-27). El nodo único es una limitación conocida: no hay alta disponibilidad.

::: {custom-style="Image Caption"}
**Figura {F:despliegue}**\
*Diagrama de despliegue del laboratorio*
:::

[FIGURA F-04 · Despliegue físico del laboratorio · Un nodo exterior rotulado equipo anfitrión Windows con Docker Desktop. Dentro, cuatro contenedores: k3d-hub-server-0 (nodo único de Kubernetes con los espacios hub, argocd, monitoring, gitea, mlops y cliente-restaurante, cliente-ferreteria, cliente-consultorio, cliente-ferreteria-staging; el sitio del colegio se crea durante la demostración), k3d-hub-serverlb (balanceador hacia el puerto 443 y 80 del anfitrión), estado-remoto (estado de OpenTofu con bloqueo) y runner (ejecutor de Gitea Actions). Fuera de los contenedores y dentro del anfitrión: Ollama en el puerto 11434 con GPU. Flechas: navegador del usuario a serverlb con nombres hub.local, grafana.hub.local, argocd.hub.local, gitea.hub.local, mlflow.hub.local y backstage.hub.local; clúster a Ollama por 192.168.65.254 puerto 11434; runner a Gitea. Rotular que no hay alta disponibilidad]

::: {custom-style="Nota"}
*Nota.* Elaboración propia. Fuentes: `gitops/platform/k3s/crear-cluster.sh`, `gitops/hub/networkpolicy.yaml:91-92` y los contenedores en ejecución del 16 de noviembre de 2026.
:::

## Flujo de datos

El diagrama de flujo de datos muestra por dónde viajan los datos y dónde cruzan fronteras de confianza. Los datos personales (nombre, correo, teléfono y dirección IP) permanecen dentro de la API y de PostgreSQL; al modelo de lenguaje y a los registros solo llegan textos con las claves y los secretos ya tapados (`backend/app/services/redaccion.py`), y nada sale del laboratorio.

::: {custom-style="Image Caption"}
**Figura {F:flujo-datos}**\
*Diagrama de flujo de datos con fronteras de confianza*
:::

[FIGURA F-05 · Flujo de datos del Hub · Entidades externas: usuarios (agencia y cliente), Alertmanager, pipeline de Gitea Actions y Ollama. Procesos: autenticación y roles, gestión de clientes y solicitudes, incidentes y SLA, publicación y rollback por GitOps, asistente de IA, reportes. Almacenes: PostgreSQL (22 tablas), repositorio hub-gitops, Loki, Tempo y Prometheus. Flujos rotulados con el dato que viaja: credenciales (bcrypt y token JWT de 60 minutos), solicitudes e incidentes, alertas con huella, eventos del pipeline con token de máquina, etiqueta de versión hacia Gitea, preguntas redactadas hacia Ollama, trazas sin texto hacia Tempo y registros hacia Loki. Marcar con color los flujos que contienen datos personales y dibujar tres fronteras: navegador y API, API y plataforma, laboratorio e Internet (sin flujos que la crucen)]

::: {custom-style="Nota"}
*Nota.* Elaboración propia. Fuentes: `docs/modelo-de-amenazas.md` (fronteras de confianza), `backend/app/services/redaccion.py` y `backend/app/telemetry.py`.
:::

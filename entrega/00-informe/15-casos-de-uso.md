<!-- Sección 15 · Fuente: routers y dependencias de acceso (deps.py), leídos el 16 nov 2026. En el código solo hay dos roles: `agencia` y `cliente`. -->

# Diagrama de casos de uso

El diagrama de casos de uso muestra qué hace cada actor con el Hub. En el código existen dos roles de usuario: `agencia` y `cliente`. El administrador y el técnico de la agencia comparten el rol `agencia` (no hay un rol de administrador separado), de modo que la distinción entre ambos es de uso y no de permisos. El operador de la plataforma es el equipo de ingeniería y trabaja con las herramientas de plataforma (Gitea, Argo CD, Grafana, Backstage y MLflow), fuera del Hub. Los actores de sistema son Alertmanager, el pipeline de la puerta de seguridad, el sistema de IA local (Ollama y el servicio de voz), el almacenamiento (PostgreSQL y `hub-gitops`) y la observabilidad (Prometheus, Loki y Tempo).

::: {custom-style="Image Caption"}
**Figura {F:casos-uso}**\
*Diagrama de casos de uso del Hub*
:::

[FIGURA F-12 · Casos de uso del Hub · Marco del sistema CloudOps Client Hub con tres actores humanos a la izquierda (cliente PyME, técnico de la agencia, administrador de la agencia) y el operador de la plataforma abajo, fuera del marco. A la derecha los actores de sistema: Alertmanager, pipeline de la puerta de seguridad, IA local (Ollama y voz), almacenamiento (PostgreSQL y hub-gitops) y observabilidad (Prometheus, Loki, Tempo). Casos de uso dentro del marco agrupados: del cliente (crear solicitud, ver estado del sitio, ver incidentes y mensajes, ver reporte ejecutivo); del técnico (clasificar y asignar solicitudes, registrar horas, aprobar cambios, ver controles de seguridad, tomar y cerrar incidentes, hacer rollback, generar y aprobar borradores, pedir diagnóstico, preguntar al asistente por texto y por voz); del administrador (registrar clientes, proyectos y servicios, dar de alta un sitio, ver tableros, generar reportes, consultar la bitácora). Relaciones include: hacer rollback incluye escribir en hub-gitops; borradores incluyen redactar con IA local y verificar. Relaciones extend: preguntar por voz extiende preguntar al asistente. Los actores de sistema se conectan a: abrir incidente automático (Alertmanager), registrar controles de la puerta (pipeline)]

::: {custom-style="Nota"}
*Nota.* Elaboración propia. Fuente: Tabla {T:casos} y `backend/app/deps.py`.
:::

::: {custom-style="Table Caption"}
**Tabla {T:casos}**\
*Casos de uso por actor y requisito que cubren*
:::

| ID | Actor | Caso de uso | Requisito | Control de acceso (código) |
|-----|---------|----------------------------|----------|-----------------------|
| CU-01 | Cliente PyME | Crear una solicitud sobre su servicio | RF-04 | `current_user`; el cliente solo ve y crea lo de su cliente (`backend/app/routers/tickets.py:87`) |
| CU-02 | Cliente PyME | Ver el estado de su sitio, su disponibilidad y sus incidentes en lenguaje de negocio | RF-16 | `current_user` con alcance por cliente (`backend/app/routers/dashboard.py:82,115`) |
| CU-03 | Cliente PyME | Ver y descargar su reporte ejecutivo | RF-20 | Solo reportes ejecutivos de su cliente (`backend/app/routers/reports.py:64-82`) |
| CU-04 | Técnico | Clasificar, asignar y mover una solicitud; registrar horas | RF-04, RF-05 | `require_agency` (`backend/app/routers/tickets.py:134,189,223,258`) |
| CU-05 | Técnico | Pedir y aprobar un cambio de versión (otra persona distinta de quien lo pidió) | RF-06 | `require_agency` y segregación de funciones (`backend/app/routers/change_requests.py:161,181`) |
| CU-06 | Técnico | Ver la versión que corre y los controles de seguridad de cada versión | RF-07, RF-09 | `require_agency` (`backend/app/routers/services.py:24`, `backend/app/routers/security.py`) |
| CU-07 | Técnico | Tomar, anotar, mitigar y cerrar un incidente | RF-13 | `require_agency` (`backend/app/routers/incidents.py:306-374`) |
| CU-08 | Técnico | Hacer rollback desde un incidente | RF-14 | `require_agency` (`backend/app/routers/incidents.py:231`) |
| CU-09 | Técnico | Generar y aprobar borradores de IA; pedir un diagnóstico con evidencia | RF-18, RF-19, RF-23 | `require_agency` (`backend/app/routers/ai_drafts.py:61-100`) |
| CU-10 | Técnico | Preguntar al asistente por texto y por voz | RF-25, RF-27, RF-28 | `require_agency` (`backend/app/routers/assistant.py:38,93,113`) |
| CU-11 | Administrador | Registrar clientes, proyectos y servicios y dar de alta un sitio | RF-02, RF-26 | `require_agency` (`backend/app/routers/clients.py:62,110`, `backend/app/routers/services.py:100`) |
| CU-12 | Administrador | Ver los tableros de la agencia y generar reportes | RF-15, RF-17, RF-20 | `require_agency` (`backend/app/routers/dashboard.py:30`, `backend/app/routers/reports.py:42`) |
| CU-13 | Administrador | Consultar la bitácora de auditoría | RF-10 | Solo lectura (`backend/app/routers/audit_logs.py:18`) |
| CU-14 | Alertmanager | Abrir y resolver incidentes automáticamente | RF-12 | Token de máquina (`backend/app/routers/alerts.py:27`) |
| CU-15 | Pipeline | Registrar los controles de la puerta de seguridad | RF-08 | Token de máquina (`backend/app/routers/pipeline.py:30`) |
| CU-16 | Operador de la plataforma | Sincronizar, observar y recuperar la plataforma; promover modelos; respaldar y restaurar | RF-29, RNF-13 | Fuera del Hub: Gitea, Argo CD, Grafana, MLflow y los procedimientos de `runbooks/` |

::: {custom-style="Nota"}
*Nota.* Elaboración propia a partir de los routers y de `backend/app/deps.py`. Los usuarios `cliente` no pueden usar el asistente ni los tableros de agencia; el usuario `agencia` ve todos los clientes.
:::

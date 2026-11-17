<!-- Secciones 16 a 19 · CI/CD, IaC, GitOps y observabilidad. Fuente: HECHOS.md §16–§19. -->

# Pipeline CI/CD

El proyecto tiene dos cadenas de verificación: el CI del repositorio y la puerta de seguridad de cada versión (Tabla {T:cicd}).

**CI del repositorio (GitHub Actions).** Corre en cada push y en cada PR a `dev` y a `main`, con cinco trabajos:

| Trabajo | Qué hace |
|---|---|
| `calidad` | ruff, `tsc` y build del frontend |
| `pruebas` | pytest del backend y de `ai/` |
| `operacion` | validación de la observabilidad, Grafana, trazas, Helm frente a Kustomize, y respaldo |
| `analisis` | bandit, Trivy del sistema de archivos y registro de hallazgos con VEX |
| `seguridad` | Gitleaks en toda la historia, humo de la imagen de producción, Trivy de imagen y de configuración, y SBOM con escaneo de licencias |

Las últimas corridas en `dev` terminaron con éxito (por ejemplo, la del PR #211 tardó 3 min 5 s; corrida F02).

**Puerta de seguridad de cada versión (Gitea Actions).** Cada etiqueta que se sube al repositorio de un sitio dispara la puerta (Figura {F:seq-cicd}), y el Hub registra cada corrida.

::: {custom-style="Table Caption"}
**Tabla {T:cicd}**\
*Etapas de la puerta de seguridad*
:::

| Etapa | Herramienta | Bloquea si |
|---|---|---|
| Secretos | Gitleaks 8.30.1 | Hay un secreto en el commit |
| Pruebas y construcción | `docker build` y pruebas del sitio | Las pruebas fallan o la imagen no construye |
| Vulnerabilidades | Trivy 0.76.1 | Hay una CVE crítica con arreglo, configuración insegura o un manifiesto con privilegios |
| SBOM | Syft 1.55.0 | Hay una licencia crítica en el inventario |
| Firma y procedencia | Cosign 3.1.4 (y Skopeo para subir) | No se puede subir, firmar o atestiguar |
| Verificación | Cosign verify | La firma es ajena o la procedencia declara otro commit |

*Nota.* Los nueve escenarios de la simulación dan el resultado esperado (B06), y la puerta real en el runner rechazó una versión con un secreto y aprobó la siguiente (C23).

- **Política de vulnerabilidades:** las CVE críticas con arreglo bloquean. Las excepciones se registran con fecha de vencimiento en `pipelines/hallazgos.yaml` y se publican como VEX (A12).
- **Secretos y accesos:** los secretos viven en `.env` y en Secrets del clúster, nunca en el repositorio, y Gitleaks revisa toda la historia. El bot del Hub solo puede escribir sus propias rutas en hub-gitops. La rama `dev` todavía no tiene protección en GitHub [COMPLETAR: activarla].
- **Uso de IA en el desarrollo:** el equipo usó agentes de auditoría con *skills* específicas en Claude Code para revisar y mejorar la aplicación. Todo cambio se revisó con la lista de comprobación del PR para código asistido por IA (`.github/pull_request_template.md`).

# Infraestructura como código

- **Herramienta:** OpenTofu 1.13.2 (o Terraform 1.17.0), en contenedor (`infra/tofu.sh`), con los proveedores `hashicorp/kubernetes` 3.4.0 y `go-gitea/gitea` 0.8.1 y versión mínima 1.10.
- **Recursos:** el módulo `client-env` crea, por cliente, el namespace con su cuota según el plan y el overlay en hub-gitops. La `Application` la crea el ApplicationSet.
- **Variables y secretos:** el inventario de clientes está en `clients.auto.tfvars.json`. Los tokens de Gitea vienen del entorno, nunca del código. El estado es local, con la opción de un estado remoto en `infra/estado-remoto.sh`.
- **Plan, aplicación y drift:** la prueba `plan -detailed-exitcode` pasa (A10). El `apply` de un cliente nuevo funciona («Apply complete! Resources: 4 added»).
- **Hallazgo grave H-IAC-01:** el `apply` reescribió los overlays de los tres clientes existentes, porque están en el inventario y no en el estado, y los sitios quedaron sin imagen hasta revertir los commits en hub-gitops (C30).
- **Justificación:** se administra con IaC solo lo que existe en el laboratorio (namespaces, cuotas y archivos en Gitea), no máquinas ni redes que no hay.

# GitOps y despliegue

- **Repositorio GitOps:** `forja-digital/hub-gitops`, rama `main`, vigilado por Argo CD 2.13.3 con nueve Applications (Hub, observabilidad, Backstage, MLOps, respaldo y cuatro clientes) y un ApplicationSet. Todas quedaron *Synced* y *Healthy* al terminar la verificación (Z01; Figura {F:argocd} del Apéndice C).
- **Sincronización:** reconciliación cada 30 s. Un cambio de versión llega al sitio en 50 s y su revert en 55 s (C21). La sincronía con el repositorio principal se verifica con una prueba (C04).
- **Drift:** Argo CD devolvió a 1 réplica un despliegue escalado a mano en 2 s y recreó un Ingress borrado en 55 s (C20).
- **Rollback:** desde el incidente, el Hub hace `git revert` del cambio en hub-gitops. Un segundo rollback se rechaza con 409 (C25).
- **Evidencia de despliegue:** las imágenes desplegadas y el estado de los Pods están en C02 y C03, y la demo del colegio crea un sitio en vivo por GitOps (spec 016).

# Observabilidad, SLI y SLO

- **Señales:** métricas (Prometheus v3.5.0), registros (Loki 3.5.3 con Alloy), trazas (Tempo 2.8.2 con OpenTelemetry) y disponibilidad (Blackbox v0.27.0). Tableros en Grafana 12.1.1: `servicio-sitios` y `red-use` (Figuras {F:grafana-lista} y {F:grafana-tablero}).
- **SLI y SLO:** el SLI es la fracción de sondeos exitosos de cada sitio (`probe_success`, cada 5 s), y el SLO es el del plan (Tabla {T:planes}).
- **Error budget:** dos alertas de consumo, una rápida (más de 14,4 veces en 1 h y 5 min) y una lenta (más de 3 veces en 6 h y 30 min), según la receta de varias ventanas del SRE Workbook (Beyer et al., 2018).

::: {custom-style="Table Caption"}
**Tabla {T:alertas}**\
*Alertas accionables*
:::

| Alerta | Condición | Acción |
|---|---|---|
| SitioCaido (P1) | Sondeo fallido durante 30 s; se mantiene 2 min | Webhook al Hub: incidente P1 con plan de rollback; runbook de caída del sitio |
| HubCaido, MonitoreoCiego, Watchdog | El Hub o el monitoreo no responden | Runbooks de caída del Hub y de monitoreo ciego |
| ContenedorSinMemoria, ContenedorEnBucle | Reinicios o falta de memoria | Runbook de contenedor en bucle |
| NodoSinMemoria, DiscoDelNodoLleno | Recursos del nodo | Runbook de saturación |
| RespaldoDelHubSinExito | El CronJob de respaldo falló | Runbook de respaldo y restauración |
| PresupuestoQuemadoRapido / Lento | Consumo del presupuesto de error | Revisar publicaciones recientes y la tendencia |

*Nota.* Las 11 reglas están en `observability/prometheus/reglas/` y cargadas en el Prometheus en vivo (C16).

**Simulación de fallas y saturación (C28 y C26):**

| Falla provocada | Resultado |
|---|---|
| Caída de réplica | El sitio volvió a los 8 s y no abrió incidente, porque duró menos de los 30 s de la alerta |
| Latencia de +150 ms en la red | El sondeo pasó de 0,003 s a 1,81 s y volvió a la normalidad |
| Saturación | El HPA subió la API a 2 réplicas |
| Versión rota (3 corridas) | Incidente P1 a los 48–49 s y mitigación automática 166–169 s después del revert |

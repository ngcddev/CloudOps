<!-- Sección 19 · Fuente: observability/, docs/kpi.md, runbooks/. Valores en vivo consultados a Prometheus el 16 nov 2026. -->

# Observabilidad, SLI y SLO

La observabilidad cubre las tres señales: métricas (Prometheus), registros (Loki, recogidos por Alloy) y trazas (Tempo, enviadas por OpenTelemetry desde la API del Hub), visualizadas en Grafana. Los registros de la API llevan `trace_id`, de modo que un registro y su traza se enlazan en ambos sentidos. Todo corre en el espacio `monitoring`, se despliega por Argo CD y se valida sin el clúster con `bash observability/pruebas/validar.sh` (`promtool`, `amtool` y `kustomize`), que también corre en la CI.

## Métricas, registros y trazas

::: {custom-style="Table Caption"}
**Tabla {T:senales}**\
*Señales de observabilidad, herramienta y conservación*
:::

| Señal | Herramienta | Qué recoge | Conservación |
|------|----------------|------------------------------|----------------|
| Métricas | Prometheus; Blackbox Exporter; kube-state-metrics; cAdvisor y kubelet; Traefik | Disponibilidad y duración del sondeo de cada sitio (cada 5 s), del Hub (cada 15 s) y de la plataforma; recursos de los contenedores; estado de los CronJobs | 30 días y 1 GB |
| Registros | Loki con Alloy como DaemonSet | Registros JSON de los Pods de clientes (Alloy descarta el resto) y registros del Hub con `trace_id` | 72 horas |
| Trazas | OpenTelemetry (API del Hub) y Tempo | Un span por petición y por etapa del asistente (compuerta, contexto, modelo); sin texto de preguntas ni de respuestas | 24 horas |
| Alertas | Alertmanager | Alertas de los sitios, de la plataforma y del presupuesto de error | — |

::: {custom-style="Nota"}
*Nota.* Elaboración propia a partir de `observability/prometheus/prometheus.yml`, `docs/operacion-responsable.md` y `backend/app/telemetry.py`. Las decisiones de Alloy y de las trazas están en ADR-15 y ADR-16.
:::

**Correlación.** El 16 de noviembre de 2026 se comprobó con una petición nueva que su `trace_id` aparece en Loki (una línea, también por `request_id`) y en Tempo (el span de `GET /api/tickets`), y que Grafana tiene aprovisionados los dos enlaces (de Loki a Tempo y de Tempo a Loki). No se abrió el enlace en la interfaz (`docs/bitacora.md:28`).

## Tableros

Hay tres tableros: dos de Grafana provisionados desde código (`observability/grafana/dashboards/`) y el tablero del propio Hub.

- **Servicio de los sitios · SLI y SLO** (`servicio-sitios.json`): la disponibilidad de cada cliente frente al objetivo de su plan y el gasto de su presupuesto de error.
- **RED y USE · sitios y Pods** (`red-use.json`): tasa de peticiones, proporción de errores y duración por sitio, y utilización, saturación y errores de los Pods.
- **Tablero de la agencia en el Hub**: disponibilidad del mes frente al objetivo del plan, MTTR, carga por técnico y costo por cliente (`GET /api/dashboard/agency`).

Las capturas de los tableros (E-10, E-11 y E-12) se incorporan en el Apéndice A.

## SLI y SLO

Los indicadores de nivel de servicio (SLI) y los objetivos (SLO) se definen sobre lo que el cliente percibe: que su sitio responda. Las fórmulas son las de `docs/kpi.md`.

::: {custom-style="Table Caption"}
**Tabla {T:sli-slo}**\
*Indicadores y objetivos de nivel de servicio*
:::

| SLI | Fórmula | SLO (objetivo) | Fuente |
|----------|--------------------------|-------------------|--------------|
| Disponibilidad del mes | `avg_over_time(probe_success{client="<c>"}[mes]) × 100` | Premium 99,9 %; Estándar 99,5 %; Básico 99,0 % (`seed/plans.json`) | Prometheus y Blackbox, job `sitios` |
| Latencia p95 del sitio | `histogram_quantile(0.95, …traefik_service_request_duration_seconds_bucket…)` | Se mide por sitio; no hay objetivo numérico fijado | Prometheus y Traefik |
| Cumplimiento de SLA de respuesta y solución | Casos resueltos dentro del plazo ÷ casos terminados del mes | P1: respuesta 15 min y solución 4 h; tiempos de las demás prioridades en `sla_policies` | Hub (`backend/app/services/sla.py`) |
| Tiempo de recuperación (MTTR) | Promedio de mitigación menos inicio de los incidentes del mes | Se mide; con cero incidentes se muestra «sin incidentes este mes» | Hub (`backend/app/services/kpi.py`) |
| Detección de una caída | Tiempo entre la caída y el incidente abierto | 60 segundos o menos (RNF-07) | Alerta `SitioCaido` y webhook |

::: {custom-style="Nota"}
*Nota.* Elaboración propia a partir de `docs/kpi.md`, `seed/plans.json` y `observability/prometheus/reglas/`. El objetivo de latencia queda como mejora: el proyecto mide la latencia pero no fija un umbral.
:::

**Valores medidos.** El 16 de noviembre de 2026, consultado a Prometheus, los cuatro sitios (restaurante, ferretería, consultorio y ferretería de pruebas) tenían disponibilidad de 1 (100 %) en la ventana de 6 horas y un gasto del presupuesto de error de 0.

## Presupuesto de error

El margen de error de un plan es uno menos su objetivo (`sitio:margen_error:ratio`). Para un mes de 30 días equivale a unos 43 minutos de caída en el plan Premium, 216 en el Estándar y 432 en el Básico (cálculo propio: 43.200 minutos multiplicados por el margen). El gasto se expresa como una tasa de quema: 1 significa que el margen alcanza justo para el mes. Las alertas usan la receta de varias ventanas del libro de SRE de Google (Beyer et al., 2018):

- `PresupuestoQuemadoRapido`: quema superior a 14,4 en 1 hora y en 5 minutos; a ese ritmo el mes se gasta en unos 2 días.
- `PresupuestoQuemadoLento`: quema superior a 3 en 6 horas y en 30 minutos; a ese ritmo el mes se gasta en unos 10 días.

El objetivo por cliente de las reglas (`observability/prometheus/reglas/presupuesto.yml`) está escrito a mano para los tres clientes del plan y espeja `seed/plans.json`; un cliente sin fila, como la ferretería de pruebas, usa el del plan Básico. Es una duplicación conocida: si se agrega un cliente con otro plan hay que actualizar la regla.

## Alertas accionables

Cada alerta lleva una anotación `accion` (qué hacer) y una `runbook_url` (procedimiento en `runbooks/`). Las alertas de un sitio llegan al Hub por webhook y abren un incidente; las de plataforma y las de presupuesto van al receptor `solo-ver`, porque no son la caída de un sitio y `HubCaido` no puede avisar a quien está caído.

::: {custom-style="Table Caption"}
**Tabla {T:alertas}**\
*Alertas, condición, gravedad y procedimiento*
:::

| Alerta | Condición | Gravedad | A dónde va | Procedimiento |
|-----------|-------------------------|---------|----------|---------------------|
| `SitioCaido` | El sondeo del sitio falla 30 s seguidos (`keep_firing_for` 2 min) | Crítica (P1) | Webhook del Hub: abre incidente | `runbooks/caida-del-sitio.md` |
| `HubCaido` | El sondeo del Hub falla 1 min | Crítica | Solo ver | `runbooks/caida-del-hub.md` |
| `MonitoreoCiego` | Un sondeo deja de funcionar o no hay objetivos, 2 min | Crítica | Solo ver | `runbooks/monitoreo-ciego.md` |
| `ContenedorSinMemoria` | Un contenedor muere por falta de memoria en 10 min | Advertencia | Solo ver | `runbooks/saturacion.md` |
| `ContenedorEnBucle` | Un contenedor se reinicia 3 veces en 15 min | Advertencia | Solo ver | `runbooks/contenedor-en-bucle.md` |
| `NodoSinMemoria` | Memoria del nodo superior a 90 %, 10 min | Advertencia | Solo ver | `runbooks/saturacion.md` |
| `DiscoDelNodoLleno` | Menos de 15 % de espacio libre, 10 min | Advertencia | Solo ver | `runbooks/saturacion.md` |
| `RespaldoDelHubSinExito` | Más de 36 h sin un respaldo exitoso del Hub, 15 min | Advertencia | Solo ver | `runbooks/respaldo-y-restauracion.md` |
| `PresupuestoQuemadoRapido` | Quema superior a 14,4 (1 h y 5 min), 2 min | Advertencia | Solo ver | `runbooks/rollback.md` |
| `PresupuestoQuemadoLento` | Quema superior a 3 (6 h y 30 min), 15 min | Advertencia | Solo ver | `runbooks/latencia.md` |
| `Watchdog` | Siempre activa: prueba que la cadena de alertas funciona | Ninguna | Solo ver | `runbooks/monitoreo-ciego.md` |

::: {custom-style="Nota"}
*Nota.* Elaboración propia a partir de `observability/prometheus/reglas/` y `observability/alertmanager/alertmanager.yml`. El 16 de noviembre de 2026 Prometheus tenía 21 reglas sanas en tres grupos, con 11 alertas: solo `Watchdog` estaba activa.
:::

**Límite.** Las alertas de plataforma no avisan a nadie fuera de Alertmanager y Prometheus: no hay un canal externo (correo o mensajería) configurado. Se ven en la pestaña Alerts de Prometheus, en Alertmanager y en Grafana.

## Evidencia de simulación de falla y saturación

El script `gitops/pruebas/simulaciones.sh` provoca tres situaciones en el clúster y deshace lo que cambia al terminar:

- **Réplica caída:** borra el Pod del sitio; el Deployment lo recrea y la prueba comprueba que no se dispara `SitioCaido`, porque una caída más corta que los 30 s no es un incidente.
- **Latencia:** añade espera de red a los Pods y mide la duración del sondeo en Prometheus; en la medición del 14 de noviembre de 2026 pasó de 3 ms a 1,8 s, y después de ajustar la prueba quedó en 150 ms sobre cada interfaz virtual.
- **Saturación:** lanza carga contra la API y comprueba que el escalado automático sube de 1 a 2 réplicas y vuelve a 1 al terminar.

Las tres pasaron en el clúster el 14 de noviembre de 2026 (`docs/bitacora.md:452,461`). Por defecto el script usa el sitio `colegio`, que ya no está dado de alta, así que hoy se corre con `SITIO=restaurante`. Además, el caso completo del restaurante (`gitops/pruebas/demo-caso-restaurante.sh`) y el cronómetro (`observability/pruebas/cronometro.sh`) miden de punta a punta la detección y la recuperación: en la medición registrada el incidente P1 se abrió dentro del minuto y el MTTR fue de 1,3 a 1,5 minutos. Provocar una falla real para ver las alertas nuevas en estado `firing` sigue sin hacerse (spec 015, T07).

La captura de la alerta `SitioCaido` en estado `firing` (E-13) se incorpora en el Apéndice A cuando se provoque la falla.

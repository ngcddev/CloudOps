# Guion de la demo final (30 nov) — borrador para ensayar

> Spec [015](../specs/015-demo-integrada/spec.md). **15 minutos** para el recorrido principal y una **ronda de preguntas con comandos listos**.
> Regla de oro: si no se ve en pantalla, no cuenta. No se agrega nada nuevo: se muestra lo que ya funciona.
> Los tiempos son estimados; se fijan en el ensayo (CA-3: tres ensayos completos en la red del salón).
> **Cambio frente a la spec 015:** el punto 10 («infografía») pasa a **voz del asistente** (módulo 6, decisión del 15 nov). Hay que actualizar la matriz de trazabilidad.

## Reparto (5 personas)

| Rol | Muestra | Puntos |
|---|---|---|
| **A · Producto/Backend** | Hub, clientes, asistente y borradores | 1, 7 (borradores), 8 |
| **B · Cloud/Plataforma** | k3s, Argo CD, Backstage, IaC, rollback | 2, 6, 9 |
| **C · DevSecOps** | La puerta de seguridad | 3 |
| **D · SRE/Frontend** | Falla, incidente, Grafana, trazas, voz | 4, 5, 10 |
| **E · Industrial** | Contexto, SLA, KPI, reportes, cierre | 0, 5 (SLA), 7 (reportes), 11 |

## Cobertura: qué módulo del diplomado se ve y cuándo

| Módulo | Se demuestra en | Minuto |
|---|---|---|
| 1 · Contenedores | Pila de contenedores y sitios del cliente; imágenes sin root | 1:00 |
| 2 · Kubernetes, GitOps, Backstage | Alta de cliente → Argo CD crea el namespace; deriva corregida; catálogo de Backstage | 1:00 y 11:30 |
| 3 · DevSecOps | Puerta de seguridad: secretos, Trivy, SBOM, firma; una versión sin firma no pasa | 3:00 |
| 4 · IaC, observabilidad, SRE | Alerta → incidente P1, tableros RED/USE, registro ↔ traza, MTTR; OpenTofu | 5:30 y 11:30 |
| 5 · MLOps y LLMOps | Asistente con compuerta y RAG; MLflow con alias `production`; borradores aprobados por una persona | 8:30 |
| 6 · IA multimodal | Preguntar hablando y escuchar la respuesta | 10:00 |
| 7 · Integrador | Todo en un solo flujo, con un clúster reiniciable | 0:00–15:00 |

## Antes de empezar (T-30 min)

1. Encender en orden: Docker Desktop → `k3d-hub-serverlb` → `k3d-hub-server-0` → `estado-remoto` → `runner-runner-1` (3 s entre cada uno; ver `runbooks/reinicio-del-cluster.md`) y confirmar que el nodo quedó en `172.30.0.3`. Ollama abierto con `qwen2.5:7b-instruct` y `nomic-embed-text`.
2. **Reiniciar a un estado conocido:** `bash demo/reiniciar-cluster.sh` (borra la base del Hub y el sitio del colegio) y `bash demo/preparar-colegio.sh` (deja en `ok` la puerta de seguridad de las versiones v1 y v2 del colegio).
3. Comprobar: `kubectl get app -n argocd` (todas `Synced/Healthy`), las 3 URL de sitios (200), `http://hub.local/health`, Grafana con los dos tableros, el micrófono del navegador con permiso para `hub.local`.
4. Archivo `hosts` con **todos** los nombres: `127.0.0.1 hub.local restaurante.hub.local ferreteria.hub.local consultorio.hub.local gitea.hub.local argocd.hub.local grafana.hub.local mlflow.hub.local backstage.hub.local ferreteria-staging.hub.local`. (MLflow y Backstage no abrían por faltar sus nombres.)
5. Contraseña de los usuarios de demostración: `kubectl -n hub get secret hub-auth -o jsonpath='{.data.SEED_USER_PASSWORD}' | base64 -d`.
6. Pestañas ya abiertas: Hub (agencia, Sofía), Hub en otra ventana de incógnito (portal, cliente de La Sazón), Argo CD, Grafana, Backstage (`https://`), terminal con `kubectl`.
7. Video de respaldo del recorrido completo grabado y abierto en otra pantalla (CA-4).

## Recorrido principal (15:00)

| Min | Punto | Quién | Qué se hace | Qué debe verse | Plan B |
|---|---|---|---|---|---|
| 0:00–1:00 | **0 · Apertura** | E, B | Una diapositiva: agencia con varios clientes; el Hub como centro de operación; qué cuesta una caída. Abrir el catálogo de Backstage 15 s | Catálogo con los clientes, el Hub y la plantilla de alta | Captura de Backstage |
| 1:00–2:30 | **1 y 2 · Clientes y plataforma** | A, B | En el Hub: clientes y planes (3 sembrados). **Registrar el colegio** y darlo de alta en GitOps. En la terminal: `kubectl get ns,pods,quota -n cliente-colegio`; Argo CD lo muestra `Synced` | Namespace nuevo con `restricted`, cuota del plan y Pod sin root, creado sin tocar el clúster a mano | Colegio ya dado de alta; mostrar el commit en Gitea |
| 2:30–4:30 | **3 · Puerta de seguridad** | C | En «Cambios» del colegio: v1 con los 6 controles en `ok`; descargar la evidencia (SBOM). Después una **versión preparada a propósito con un secreto** (ver T03 de la spec 015): la puerta la rechaza y el Hub no deja aprobarla, con el motivo | Gitleaks, Trivy, Syft y Cosign con su resultado; rechazo con motivo en lenguaje de negocio | Corrida grabada del pipeline |
| 4:30–6:30 | **4 y 5 · Falla e incidente** | D, E | Aprobar (otra persona de la agencia, por la segregación de funciones) la v2 rota de La Sazón. El sitio da 500; en ≤ 45 s se abre el P1 con su reloj de SLA. Mostrar el incidente, tomarlo, abrir Grafana (RED y USE) y el registro con su traza | P1 abierto solo por la alerta, SLA corriendo; panel de errores; registro con enlace a la traza | Video del minuto de detección; `gitops/pruebas/demo-caso-restaurante.sh` |
| 6:30–8:00 | **6 y 7 · Rollback** | B, E | «Rollback» desde el incidente (el Hub escribe el `revert` en Git, Argo CD reconcilia). El sitio vuelve; el incidente pasa a mitigado con su MTTR medido | Commit `revert`, sitio 200, MTTR, historial de versiones y bitácora | Ya mitigado: mostrar MTTR y línea de tiempo |
| 8:00–9:30 | **8 · IA con verificación humana** | A | Pedir hipótesis a la IA; generar los borradores del incidente (resumen técnico y mensaje al cliente); **editar y aprobar**; abrir el portal del cliente y ver llegar el mensaje. Pregunta del tema al asistente y una ajena (la compuerta la descarta sin despertar al modelo). Mostrar `mlflow.hub.local` con `compuerta-asistente@production` | Borrador marcado «de la IA», aprobación que llega al portal; respuesta con la fuente de la ayuda; registro del modelo | Borrador semilla ya aprobado |
| 9:30–11:00 | **10 · Voz (módulo 6)** | D | En el asistente: pulsar el micrófono, preguntar hablando, ver y corregir lo entendido, escuchar la respuesta | Transcripción editable y audio de la respuesta | Audio pregrabado; preguntar por texto |
| 11:00–12:30 | **8 · Reportes y KPI** | E | Portal del cliente: estado del mes. En agencia: reporte operativo y ejecutivo de La Sazón con el incidente del día explicado; descargar el PDF | Disponibilidad frente al SLO del plan, costo, MTTR, PDF | PDF ya generado |
| 12:30–14:00 | **IaC y operación** | B | `tofu` crea un cliente nuevo (overlay + Application) y Argo CD lo sincroniza; mostrar la prueba de deriva; abrir `runbooks/` y el respaldo de PostgreSQL | Cliente creado desde código, deriva detectada, runbook y respaldo | Salida grabada de `infra/pruebas/crear-cliente.sh` |
| 14:00–15:00 | **Cierre** | E | Mapa de la rúbrica del diplomado en una diapositiva; qué es de verdad y qué son límites honestos (nodo único, firma verificada en el pipeline, audio y no imagen) | — | — |

## Ronda de preguntas: comandos listos

| Si preguntan por… | Mostrar |
|---|---|
| Aislamiento de red | `bash gitops/pruebas/salida-red.sh restaurante` y `bash gitops/pruebas/salida-hub.sh` |
| Pod Security y admisión | `bash gitops/pruebas/pod-security.sh`, `bash gitops/pruebas/admision.sh` |
| Deriva y selfHeal | `bash gitops/pruebas/drift.sh` |
| ¿Quién escribe en el repositorio de configuración? | `bash gitops/pruebas/sincronia.sh` y la regla de Gitea (`python gitops/proteccion_hub_gitops.py --comprobar`) |
| Respaldo y restauración | `bash gitops/pruebas/respaldo.sh` |
| Cuota y capacidad por cliente | `KUBECONFIG=... bash observability/capacidad.sh` |
| Evaluación de la IA | `python ai/eval/run_eval.py --archivo ai/eval/preguntas_ayuda_ciegas.jsonl`; `python ai/eval/probar_documento_malicioso.py` |
| Latencia y memoria del modelo | `python ai/eval/medir_modelos.py` y `docs/modelos/` (fichas) |
| Integridad de los modelos | `python ai/verificar_modelos.py` |
| Tutor de Kubernetes (módulo 2) | `python ai/tutor/tutor.py "¿Para qué sirve un DaemonSet?"` |
| Trazas y registros | Grafana → Explore → Loki, enlace «Ver la traza» (el registro de la API lleva `trace_id`) |
| Pruebas | `docker compose exec api pytest` (más de mil) y el CI de GitHub |

## Riesgos y respuesta

| Riesgo | Respuesta |
|---|---|
| El nodo k3d reinicia en bucle tras encender (IP) | Orden de arranque y comprobar `172.30.0.3` en T-30 (`runbooks/reinicio-del-cluster.md`) |
| La IA tarda (modelo frío) | Hacer una pregunta de calentamiento en T-5; `keep_alive` corto |
| Memoria justa con Backstage encendido | Encenderlo solo para el minuto 0 y 11:30 si hace falta; límites ya puestos |
| La red del salón | Todo es local en un PC (IA incluida): no depende de la red. Probar el navegador y el micrófono en ese equipo |
| Pasarse de tiempo | Cortar explicación, nunca pasos; ensayos cronometrados |
| El micrófono real bajo la política de seguridad del navegador | **Probar antes del 30 nov** (no se ha probado con una persona real) |

## Ensayos

1. **Ensayo 1** (sin público): recorrer los 11 minutos y medio de puntos en orden, anotar tiempos reales y lo que falla.
2. **Ensayo 2:** con reinicio previo (`demo/reiniciar-cluster.sh`) y cambio de relevos entre personas.
3. **Ensayo 3:** en el equipo y la red del salón, grabando el video de respaldo.
4. Después de cada ensayo, anotar tiempos y fallos en `docs/context.md` (spec 015, «Cómo se verifica»).

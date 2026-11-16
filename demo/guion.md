# Guion de la demo final (30 nov) — presenta una sola persona

> Spec [015](../specs/015-demo-integrada/spec.md). **15 minutos** de recorrido y una ronda de preguntas con comandos listos.
> Regla de oro: si no se ve en pantalla, no cuenta. No se agrega nada nuevo: se muestra lo que ya funciona.
> Los tiempos son estimados hasta el primer ensayo cronometrado (CA-3).
> **Cambio frente a la spec 015:** el punto 10 («infografía») pasa a **voz del asistente** (módulo 6, decisión del 15 nov).
> **Voz comprobada** el 16 nov: en un navegador real contra el clúster y con la política de seguridad estricta puesta, el micrófono (falso) llegó a transcripción, respuesta escrita y audio reproducido, sin errores de JavaScript. Falta probarla con una voz humana.

## Cómo se organiza una sola persona

- **Tres ventanas ya iniciadas** (todas en `hub.local`):
  1. **Sofía** (agencia): la ventana principal.
  2. **Camilo** (agencia), perfil o ventana aparte: solo para aprobar un cambio (el sistema no deja que quien lo pidió lo apruebe; mostrarlo es parte de la demo, y con una segunda ventana no necesitas a otra persona).
  3. **Marta** (cliente de La Sazón), ventana de incógnito: el portal.
- **Segunda pantalla o mitad de pantalla:** terminal con `kubectl` (`KUBECONFIG` ya puesto) y, al lado, Grafana y Argo CD.
- **Tiempo muerto = trabajo hecho en segundo plano.** Lo lento (alta del sitio, publicación, detección de la falla) se lanza y se habla de otra cosa mientras ocurre; los minutos del guion ya cuentan con eso.
- **Un cronómetro visible** (el del celular). Puntos de control abajo: si vas más de un minuto tarde, usa el recorte.
- Frases entre comillas = lo que se dice. Lo demás es lo que se hace.

## Antes de empezar (T-30 min)

1. Encender en orden: Docker Desktop → `k3d-hub-serverlb` → `k3d-hub-server-0` → `estado-remoto` → `runner-runner-1` (3 s entre cada uno; `runbooks/reinicio-del-cluster.md`) y confirmar el nodo en `172.30.0.3`. Ollama abierto con `qwen2.5:7b-instruct` y `nomic-embed-text`.
2. **Reiniciar a un estado conocido:** `bash demo/reiniciar-cluster.sh` y `bash demo/preparar-colegio.sh`.
3. Comprobar: `kubectl get app -n argocd` (todas `Synced/Healthy`); los tres sitios dan 200; `http://hub.local/health`; Grafana con los dos tableros.
4. Archivo `hosts` con todos los nombres: `127.0.0.1 hub.local restaurante.hub.local ferreteria.hub.local consultorio.hub.local gitea.hub.local argocd.hub.local grafana.hub.local mlflow.hub.local backstage.hub.local ferreteria-staging.hub.local`.
5. Contraseña de los usuarios: `kubectl -n hub get secret hub-auth -o jsonpath='{.data.SEED_USER_PASSWORD}' | base64 -d`.
6. **Calentar la IA** (T-5 min): una pregunta al asistente, para que el modelo no esté frío.
7. **Micrófono:** permitir el micrófono para `hub.local` y probar una pregunta hablada (la primera vez con una voz real).
8. Pestañas abiertas y ordenadas: Hub (Sofía) en *Clientes*; Hub (Camilo) en *Cambios*; Hub (Marta) en el portal; Argo CD; Grafana (tablero RED y USE); MLflow; Backstage (`https://`).
9. Plan B listo: el video del recorrido completo, el PDF del reporte ya generado y un borrador de incidente semilla aprobado.

## Recorrido (15:00)

### 0:00–0:45 · Apertura
- **Hacer:** abre Backstage (catálogo) 10 s y vuelve al Hub.
- **Decir:** «Una agencia web atiende varias PyMEs y hoy no sabe, con medidas, si sus sitios están arriba ni cuánto tarda en recuperarlos. CloudOps Client Hub es el centro de operación: clientes, planes con acuerdos de servicio, cambios, incidentes, rollback, reportes e IA local, sobre una plataforma de Kubernetes con GitOps y seguridad en la entrega.»
- **Ver:** catálogo con los clientes, el Hub y la plantilla de alta.
- **Si falla:** captura de Backstage.

### 0:45–2:15 · Puntos 1 y 2 · Clientes y plataforma (módulos 1 y 2)
- **Hacer:** en Sofía, *Clientes* (3 clientes y sus planes). Pulsa **Registrar cliente**: ya tienes los datos del colegio listos para pegar (cliente, proyecto y servicio con host y namespace). Guarda y pulsa **dar de alta el sitio en GitOps**.
- **Decir:** «El Hub nunca toca Kubernetes. Escribe la configuración del sitio en Git; Argo CD la ve y crea el namespace con su cuota, sus límites y la política de seguridad `restricted`.»
- **Mientras Argo CD trabaja (≈ 30 s):** pasa al siguiente punto y vuelve al minuto 4.
- **Si falla:** colegio ya dado de alta; muestra el commit en Gitea.

### 2:15–4:00 · Punto 3 · Puerta de seguridad (módulo 3)
- **Hacer:** *Cambios* → la v1 del colegio con sus 6 controles en `ok`; descarga la evidencia (SBOM). Abre después la **versión con un secreto puesto a propósito** (tarea T03 de la spec 015): rechazada, sin poder aprobarse, con el motivo.
- **Decir:** «Cada versión pasa por Gitleaks, pruebas y construcción, Trivy, el inventario de componentes con Syft y la firma con Cosign, que se verifica antes de aprobar. Quien aprueba no ve un semáforo: ve qué control falló y por qué.»
- **Ver:** controles con su resultado y evidencia; rechazo con motivo en lenguaje de negocio.
- **Si falla:** corrida grabada del pipeline.

### 4:00–4:30 · Vuelta al colegio (filler útil)
- **Hacer:** terminal: `kubectl get ns,pods,quota -n cliente-colegio`.
- **Ver:** namespace nuevo, Pod sin root, cuota del plan. «Nadie tocó el clúster a mano.»

### 4:30–6:30 · Puntos 4, 5 y 6 · La falla (módulo 4)
- **Hacer:** en la ventana de Camilo, **aprobar** la v2 rota de La Sazón (es el cambio que pidió Sofía: «una persona distinta aprueba»). Vuelve a Sofía, abre *Incidentes* y deja el tablero a la vista. A los ≤ 45 s aparece el **P1** con su reloj de SLA. Pulsa **Tomar incidente**. Abre Grafana (RED y USE) y el registro con **Ver la traza**.
- **Decir:** «Prometheus sondea cada 5 segundos; a los 30 de caída Alertmanager avisa al Hub y se abre el incidente solo, con prioridad P1 y un reloj contra el SLA del plan del cliente.»
- **Ver:** P1 abierto por la alerta, reloj corriendo, errores en el panel, registro enlazado con su traza.
- **Si falla:** video del minuto de detección o `bash gitops/pruebas/demo-caso-restaurante.sh`.

### 6:30–8:00 · Puntos 6 y 7 · Rollback
- **Hacer:** en el incidente, **Rollback** → **Confirmar rollback**. Espera a que pase a mitigado.
- **Decir:** «El rollback es un `revert` en Git; Argo CD lo reconcilia. El tiempo de recuperación no se estima: se mide.»
- **Ver:** commit `revert`, sitio en 200, MTTR, línea de tiempo y bitácora.
- **Si falla:** incidente ya mitigado: muestra MTTR y línea de tiempo.

### 8:00–9:30 · Punto 9 · IA con verificación humana (módulo 5)
- **Hacer:** **Pedir hipótesis a la IA** → **Generar borradores** → edita una frase y **Aprobar** el mensaje al cliente. En la ventana de Marta, recarga: llega el mensaje. En *Asistente*, una pregunta del tema y una ajena («¿quién ganó el mundial de 1998?»). Abre `mlflow.hub.local` (`compuerta-asistente@production`).
- **Decir:** «La IA propone, una persona aprueba. Corre en esta máquina con Ollama, no sale ningún dato. Una compuerta entrenada y registrada en MLflow decide si la pregunta es del Hub antes de despertar al modelo; el contexto sale de la ayuda del Hub con búsqueda por embeddings.»
- **Ver:** borrador marcado «de la IA», aprobación que llega al portal, la ajena descartada por la compuerta, el modelo registrado.
- **Si falla:** borrador semilla aprobado.

### 9:30–11:00 · Punto 10 · Voz (módulo 6)
- **Hacer:** en *Asistente*, pulsa **Hablar**, pregunta «¿cómo apruebo un cambio?», pulsa **Detener**, mira el texto, corrige una palabra y envía; escucha la respuesta.
- **Decir:** «El módulo 6 es multimodal: la voz va a texto con faster-whisper y vuelve a voz con Piper, en CPU, sin competir con el modelo por la GPU.»
- **Ver:** transcripción editable y respuesta hablada.
- **Si falla:** audio pregrabado; pregunta escrita.

### 11:00–12:30 · Punto 8 · Portal, reportes y KPI
- **Hacer:** ventana de Marta: el estado del mes y el incidente explicado en su lenguaje. En Sofía, *Reportes*: **Generar** operativo y ejecutivo; descarga el PDF ejecutivo.
- **Decir:** «El cliente no ve términos técnicos: ve disponibilidad frente a lo acordado, qué pasó y qué hicimos. La agencia ve costo, horas y tiempos de respuesta.»
- **Si falla:** PDF ya generado.

### 12:30–14:00 · IaC y operación (módulos 2 y 4)
- **Hacer:** `infra/client-new.sh` (o el módulo `client-env` con `tofu`) crea un cliente desde código; Argo CD lo sincroniza. Después `bash gitops/pruebas/drift.sh` (un cambio a mano se corrige solo) y abre `runbooks/`.
- **Decir:** «Todo lo anterior se reconstruye desde código: OpenTofu crea el cliente, Git es la verdad, y si alguien cambia algo a mano Argo CD lo devuelve. Hay runbooks y un respaldo probado de la base.»
- **Si falla:** salida grabada de `infra/pruebas/crear-cliente.sh`.

### 14:00–15:00 · Cierre
- **Decir:** «Lo que vieron cubre los siete módulos: contenedores, Kubernetes y GitOps, cadena de suministro, observabilidad e IaC, MLOps con IA local y voz. Límites honestos: un solo nodo, la firma se verifica en el pipeline y no dentro del clúster, y la modalidad adicional es audio, no imagen.»

## Puntos de control y recortes

| Si al llegar al minuto… | vas en… | Recorte |
|---|---|---|
| 4:30 | el P1 aún no aparece | Habla del reloj mientras esperas; si pasa de 6:00, usa el video de la detección |
| 8:00 | el rollback no terminó | Muestra el commit `revert` y sigue; el MTTR se ve después |
| 11:00 | más de 1 min tarde | Salta la voz en vivo (pon el audio pregrabado) |
| 12:30 | más de 1 min tarde | Omite IaC y el drift; muestra `runbooks/` 20 s y cierra |

## Ronda de preguntas: comandos listos

| Si preguntan por… | Mostrar |
|---|---|
| Aislamiento de red | `bash gitops/pruebas/salida-red.sh restaurante`, `bash gitops/pruebas/salida-hub.sh` |
| Pod Security y admisión | `bash gitops/pruebas/pod-security.sh`, `bash gitops/pruebas/admision.sh` |
| Deriva y selfHeal | `bash gitops/pruebas/drift.sh` |
| ¿Quién escribe en la configuración? | `bash gitops/pruebas/sincronia.sh`; `python gitops/proteccion_hub_gitops.py --comprobar` |
| Respaldo y restauración | `bash gitops/pruebas/respaldo.sh` |
| Cuota y capacidad por cliente | `KUBECONFIG=... bash observability/capacidad.sh` |
| Evaluación de la IA | `python ai/eval/run_eval.py --archivo ai/eval/preguntas_ayuda_ciegas.jsonl`; `python ai/eval/probar_documento_malicioso.py` |
| Latencia y memoria del modelo | `python ai/eval/medir_modelos.py`; fichas en `docs/modelos/` |
| Integridad de los modelos | `python ai/verificar_modelos.py` |
| Tutor de Kubernetes | `python ai/tutor/tutor.py "¿Para qué sirve un DaemonSet?"` |
| Voz | `HUB_WEB=https://hub.local HUB_NOMBRE=hub.local ... bash voz/pruebas/voz-ui.sh` |
| Pruebas | `docker compose exec api pytest` y el CI de GitHub |

## Riesgos

| Riesgo | Respuesta |
|---|---|
| El nodo k3d reinicia en bucle tras encender (IP) | Orden de arranque y comprobar `172.30.0.3` en T-30 |
| La IA tarda con el modelo frío | Pregunta de calentamiento en T-5 |
| Memoria justa con Backstage | Abrirlo solo en el minuto 0 si hace falta |
| La red del salón | Todo corre en tu PC, IA incluida: no depende de la red. Probar navegador y micrófono en ese equipo |
| Pasarse de tiempo | Cronómetro visible, puntos de control y recortes |
| Hablar con otra voz u otro micrófono | Probar la voz real antes; plan B con audio pregrabado |

## Ensayos

1. **Ensayo 1** (solo): cronometrar cada bloque y anotar lo que falla.
2. **Ensayo 2:** con reinicio previo (`demo/reiniciar-cluster.sh`), sin parar.
3. **Ensayo 3:** en el equipo y la red del salón, grabando el video de respaldo.
4. Anotar tiempos y fallos en `docs/context.md`.

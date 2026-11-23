<!-- Guion de la demo en vivo de la sustentación del 30 nov 2026 (15 min, la presenta Nicolás Gaviria solo), con plan B por paso. -->

# Demo en vivo · CloudOps Hub (15 min)

**Presenta:** Nicolás Gaviria Cerón, solo. **Arranca** en la diapositiva 48 (la última) de [Presentación de 48 diapositivas](Sustentacion_CloudOps_Hub_v1.4.pptx).
**Formato:** 35 min de exposición (48 diapositivas), esta demo de 15 min y 10 min de preguntas.
**Regla:** si no se ve en pantalla, no cuenta. No se muestra nada que no esté en el paquete de evidencias.
**Fuentes:** `demo/guion.md` (guion base de la spec 015), `entrega/evidencias/2026-11-16_bb5a284/` (tiempos medidos) y el runbook 05.

## Antes de entrar al salón

| Cuándo | Qué | Por qué |
|---|---|---|
| T-60 min | Encender Docker Desktop y los contenedores de k3d en orden (`runbooks/reinicio-del-cluster.md`); confirmar el nodo en `Ready` y las 9 Applications en `Synced/Healthy` | El nodo puede cambiar de IP al reiniciar (RT-04) |
| T-50 min | `KUBECONFIG=... bash entrega/evidencias/dejar-demo-lista.sh` (unos 15 min) | Deja la base limpia, vuelve a pasar v1, v1.1 y v2 por la puerta y pone los tres sitios en v1 (Z01). **No usar** `demo/reiniciar-cluster.sh` solo: borra las corridas de la puerta (H-DEMO-01) |
| T-30 min | Ollama abierto con `qwen2.5:7b-instruct` y `nomic-embed-text`; `python ai/verificar_modelos.py` | Integridad de los modelos (D01) |
| T-15 min | Abrir y ordenar las pestañas (lista abajo); probar el micrófono del salón con una pregunta hablada | La voz nunca se ha probado con el micrófono del salón |
| T-5 min | Una pregunta al asistente para calentar el modelo | En frío tarda 9,9 s (D06) |
| T-5 min | Cronómetro visible y el plan B abierto en una carpeta | — |

**Pestañas, en este orden:**
1. Hub como Sofía (agencia), en *Cambios*.
2. Hub como Camilo (agencia), en una ventana aparte: solo sirve para aprobar.
3. Hub como Marta (cliente de La Sazón), en incógnito: el portal.
4. Gitea, en `hub-gitops`.
5. Argo CD, en `cliente-restaurante`.
6. Grafana, en el tablero de servicio de los sitios.
7. MLflow, en `compuerta-asistente`.
8. Backstage.
9. Una terminal con `KUBECONFIG` puesto.

**Contraseña de los usuarios sembrados:** `kubectl -n hub get secret hub-auth -o jsonpath='{.data.SEED_USER_PASSWORD}' | base64 -d`. No se escribe en ningún lado.

## Cómo nombrar las cosas al hablar

Por indicación del docente, al hablar se usan nombres genéricos aunque la pantalla muestre los de la base de datos. No se menciona que los casos sean simulados; si el jurado pregunta de frente, la respuesta honesta está en el banco de preguntas.

| En pantalla verás | Di |
|---|---|
| Restaurante La Sazón (`cliente-restaurante`) | Empresa A |
| Ferretería El Tornillo (`cliente-ferreteria`) | Empresa B |
| Consultorio Dental Popayán (`cliente-consultorio`) | Empresa C |
| Colegio (el sitio que se da de alta en la demo) | Empresa D |
| Forja Digital | la agencia |
| Sofía y Camilo (técnicos de la agencia) | la técnica y el técnico de la agencia |
| Marta (cliente) | la cliente de la Empresa A |
| Compuerta (`compuerta-asistente` en MLflow) | el clasificador de preguntas que entrenamos |

## Recorrido

| # | Tiempo | Qué hago | Qué digo | Módulo | Plan B si falla |
|---|---|---|---|---|---|
| 1 | 0:00–1:00 | Paso de la diapositiva 48 al Hub. Muestro el portal de Marta (estado del sitio sin jerga) y luego la consola de Sofía (*Clientes*: tres clientes con su plan) | «Esto corre en contenedores sobre un clúster k3s en esta laptop. Es la misma API, vista por la agencia y por el cliente.» | M1 | Capturas E13 y E02 (`entrega/evidencias/2026-11-16_bb5a284/E/capturas/`) |
| 2 | 1:00–2:30 | *Cambios* → abro las corridas de la puerta de la v2 de La Sazón: los 6 controles en «ok» y la evidencia (SBOM) | «Cada versión pasa por Gitleaks, pruebas, Trivy, Syft y la firma con Cosign, que se verifica antes de poder aprobar. Ojo: esta v2 pasa la puerta porque es segura, pero está rota. La puerta revisa seguridad, no funcionamiento. Para eso está el monitoreo.» | M3 | Captura E42 (puerta de ferretería en Gitea) y registro `C/C23-demo-006.log` (versión con secreto rechazada) |
| 3 | 2:30–3:30 | Como Sofía, registro el cambio de La Sazón a v2 e intento aprobarlo: el Hub lo rechaza. Paso a la ventana de Camilo y lo apruebo | «Quien pide un cambio no puede aprobarlo: es segregación de funciones, y el intento queda en la bitácora. Lo aprueba otra persona.» | M2, M3 | Registro `C/C22-demo-005.log` (403 y aprobación con la segunda cuenta) |
| 4 | 3:30–4:30 | Gitea: el commit del Hub en `hub-gitops`. Argo CD: `cliente-restaurante` sincroniza a v2 | «El Hub no toca Kubernetes: escribe la versión en Git y Argo CD la aplica. Un cambio así llega al sitio en unos 50 s.» | M2 | Captura F16 (`entrega/evidencias/apendices-2026-11-20/`) y registro `C/C21-ciclo-gitops.log` |
| 5 | 4:30–6:00 | Sofía → *Incidentes*. Espero el P1 (en las corridas tardó 48 a 49 s desde el corte). Pulso **Tomar incidente**. Muestro Grafana: el sondeo en 0 | «Blackbox sondea cada 5 s. A los 30 s de caída, Alertmanager avisa al Hub y se abre un P1 solo, con su reloj contra el SLA del plan Premium: 15 min para responder y 4 h para resolver.» | M4 | Si a las 6:00 no aparece: registro `C/C26-cronometro.log` (48, 48 y 49 s) y captura F17. Sigo con el paso 7 |
| 6 | 6:00–6:30 | En el incidente: **Rollback** → **Confirmar rollback** | «El rollback es un git revert en hub-gitops. Mientras Argo CD vuelve a la v1, les muestro la IA.» | M2, M4 | Registro `C/C25-caso-restaurante.log` (MTTR 3,4 min) |
| 7 | 6:30–9:00 | En el mismo incidente: **Pedir hipótesis a la IA** → **Generar borradores**; edito una frase y **Aprobar** el mensaje al cliente. Recargo el portal de Marta: llega el mensaje. En *Asistente*: una pregunta del Hub y una ajena («¿quién ganó el mundial de 1998?»). En MLflow: el modelo `compuerta-asistente` (es el clasificador) con el alias production | «La IA propone y una persona aprueba. Todo corre en Ollama en esta máquina: ningún dato sale. Un clasificador que entrenamos y versionamos en MLflow decide si la pregunta es del Hub antes de despertar al modelo. La ajena ni siquiera llega al LLM. Lo demás es RAG: busca en la ayuda del Hub y responde solo con eso.» | M5 | Si Ollama no responde, el Hub lo dice y sigue funcionando (F01). Captura E11 y F19; borrador escrito a mano |
| 8 | 9:00–10:00 | Vuelvo al incidente: «mitigado», con el MTTR medido. En Gitea, el commit `revert`. En *Bitácora*, las acciones con su autor y hora | «El tiempo de recuperación no se estima, se mide. En las corridas fue de 3,4 min, dentro de la meta de 5.» | M4, M2 | Si aún no está mitigado: muestro el commit `revert` y vuelvo al final |
| 9 | 10:00–11:30 | *Asistente* → **Hablar**: «¿cómo apruebo un cambio?» → **Callar**. Corrijo una palabra si hace falta, envío y escucho la respuesta | «El componente multimodal es la voz: faster-whisper pasa la voz a texto y Piper el texto a voz, en CPU, para no competir por la GPU con el modelo. El audio no se guarda.» | M6 | Capturas 1 a 4 de `D/capturas-voz/` y la pregunta escrita |
| 10 | 11:30–13:00 | Terminal: `KUBECONFIG=... SITIO=ferreteria bash gitops/pruebas/drift.sh` (escala a mano y borra el Ingress). En Argo CD, cómo vuelve a Synced | «Si alguien cambia el clúster a mano, Argo CD lo devuelve a lo que dice Git. Las réplicas vuelven en unos 2 s y el Ingress se recrea.» | M2 | Registro `C/C20-drift-selfheal.log` (2 s y 55 s) |
| 11 | 13:00–14:15 | Backstage: el catálogo con los sitios y la plantilla «Sitio de cliente». Sofía → *Reportes*: **Generar** el reporte ejecutivo en PDF | «La plataforma tiene un catálogo para encontrar cada sitio y su documentación. La agencia reporta disponibilidad, horas y costo por cliente.» | M2, M4 | Capturas de `D/capturas-backstage/` y E10 |
| 12 | 14:15–15:00 | Vuelvo a la diapositiva 48 | «Vieron un cambio pasar la puerta, publicarse por Git, romper el sitio, abrir un P1 solo y recuperarse por rollback, con IA local y voz. Gracias, quedamos atentos a sus preguntas.» | Todos | — |

## Puntos de control

| Si al minuto… | vas en… | Recorte |
|---|---|---|
| 4:30 | Argo CD no ha sincronizado | Muestra el commit en Gitea y habla del reloj del SLA mientras tanto |
| 6:00 | no aparece el P1 | Plan B del paso 5; pide el rollback igual |
| 9:30 | más de 1 min tarde | Recorta el paso 8 a 20 s |
| 11:30 | más de 1 min tarde | Salta el paso 10 (drift) y muéstralo en las preguntas si lo piden |
| 13:00 | más de 1 min tarde | Salta Backstage; cierra con el reporte |

## Plan B general

- **Si el clúster no arranca:** se presenta desde el paquete de evidencias. Las capturas están en `E/capturas/`, `D/capturas-voz/`, `D/capturas-backstage/` y `apendices-2026-11-20/`, y los registros con tiempos en `C/` y `D/`. Cada paso de la tabla dice qué abrir.
- **Video del recorrido completo:** [PENDIENTE: grabar el video del recorrido en el ensayo del 26 al 28 nov; hoy no existe ningún video en el repositorio].
- **Escalamiento** (runbook 05): Nicolás atiende el nivel 2 y Andrés el nivel 1 durante la demo.

## Comandos listos para las preguntas

| Si preguntan por… | Mostrar |
|---|---|
| Aislamiento de red | `bash gitops/pruebas/salida-red.sh restaurante` |
| Pod Security | `bash gitops/pruebas/pod-security.sh` |
| Respaldo | `bash gitops/pruebas/respaldo.sh` |
| Capacidad por cliente | `KUBECONFIG=... bash observability/capacidad.sh` |
| Integridad de los modelos | `python ai/verificar_modelos.py` |
| Tutor del módulo 2 | `python ai/tutor/tutor.py "¿Para qué sirve un DaemonSet?"` |
| Pruebas | `docker compose exec api pytest` y el CI en GitHub |

**No mostrar en vivo:** `infra/pruebas/crear-cliente.sh`. Con el inventario actual reescribe a los tres clientes existentes (H-IAC-01).

## Pendientes de la demo

- [PENDIENTE: confirmar en el ensayo que, tras `dejar-demo-lista.sh`, la v2 de La Sazón aparece en *Cambios* con la puerta en «ok» y que los nombres de los botones coinciden con este guion].
- [PENDIENTE: decidir si se muestra en vivo una versión rechazada por la puerta (`gitops/pruebas/demo-006.sh`, unos 70 s) o solo con el plan B].
- [PENDIENTE: confirmar el modo del asistente en el clúster el día de la demo (`rag` según el despliegue del 20 nov; el CI usa `completo`)].
- [PENDIENTE: probar la voz con el micrófono y la red del salón].
- [PENDIENTE: grabar el video de respaldo].

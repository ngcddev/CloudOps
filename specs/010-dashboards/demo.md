# Guion de la demo de cierre (T20)

> **Tarea:** T20 · Demo: consola, carga y costo, detalle técnico, portal de La Sazón y Prometheus
> apagado.
> **Criterio:** se cumplen todos los criterios de [spec.md](spec.md#criterios-de-aceptación) (CA-1 a
> CA-9).
> **Duración:** 30–45 minutos de demo, más 10 minutos de preparación.
> **Quién la presenta:** una persona del equipo; otra toma nota de cada CA y de la hora.

Esta demo es la misma que usan T18 y la sustentación. Se puede hacer con el script
[`gitops/pruebas/demo-010.sh`](../../gitops/pruebas/demo-010.sh) (recomendado) o a mano con las
pantallas. El script no reemplaza la demostración visual: comprueba los datos y deja la evidencia,
pero el jurado tiene que ver la consola y el portal.

> **Si la demo se hace después de octubre de 2026**, las pantallas usan el mes en curso y los datos
> sembrados son de octubre. Abrir el portal con `http://hub.local/portal?month=2026-10` y la consola
> con `http://hub.local/agencia?month=2026-10`; el mes queda recordado en la pestaña. El script ya
> acepta `MES=2026-10`.

## 1. Antes de empezar (10 min)

| # | Requisito | Cómo se comprueba |
|---|---|---|
| 1 | Clúster con las specs 003–009 aplicadas | `kubectl get nodes` → `Ready`; `kubectl -n hub get pods` sin `CrashLoopBackOff` |
| 2 | T18 ejecutada al menos una vez | La consola muestra disponibilidad distinta de `null` |
| 3 | Entradas de `hosts` | `curl -I http://hub.local` y `curl -I http://restaurante.hub.local` responden |
| 4 | Contraseña de usuarios sembrados | `kubectl -n hub get secret hub-auth -o jsonpath='{.data.SEED_USER_PASSWORD}' \| base64 -d` |
| 5 | Grafana responde | Abrir `http://grafana.hub.local` (usuario y contraseña del Secret `grafana-admin`) |
| 6 | Prometheus con datos | En Grafana, la consulta `probe_success{job="sitios"}` tiene series de los 3 clientes |
| 7 | `curl` y `kubectl` en el equipo | `curl --version` y `kubectl version --client` |
| 8 | Reloj del equipo en hora | La hora de los incidentes y del MTTR depende de ella |

Guardar la contraseña en una variable de la terminal para no escribirla en pantalla:

```bash
export HUB=http://hub.local
export HUB_PASSWORD="$(kubectl -n hub get secret hub-auth -o jsonpath='{.data.SEED_USER_PASSWORD}' | base64 -d)"
```

> En desarrollo con `docker compose`, usar `HUB=http://localhost:8000` y la contraseña de
> `.env` (`SEED_USER_PASSWORD`).

Comprobar el punto de partida (sin cambiar nada):

```bash
curl -s -o /dev/null -w '%{http_code}\n' http://restaurante.hub.local/health   # 200
kubectl -n cliente-restaurante get deploy/web                                  # READY 1/1
kubectl -n monitoring get deploy/prometheus                                    # READY 1/1
```

Si algo falla aquí, **no empezar la demo**: primero se arregla el clúster (T18).

## 2. Opción rápida: script automatizado

```bash
HUB_PASSWORD="$HUB_PASSWORD" bash gitops/pruebas/demo-010.sh
```

El script hace, en orden:

1. Entra como agencia y como cliente de La Sazón.
2. Consulta el tablero de la agencia y comprueba 3 clientes, carga por técnico, SLA, solicitudes,
   horas/costo, disponibilidad y «cumple el objetivo».
3. Consulta el portal y comprueba que no trae costo, horas ni técnicos, y que pedir otro cliente da
   404.
4. Consulta la serie del mes y cuenta los puntos de 5 minutos.
5. **Apaga** el sitio (`kubectl -n cliente-restaurante scale deploy/web --replicas=0`), espera el
   incidente de alerta y comprueba que el tablero lo muestra caído.
6. **Enciende** el sitio, espera a que el incidente quede mitigado y comprueba el MTTR y el hueco de
   disponibilidad en la serie.
7. **Apaga Prometheus**, espera 65 s a que venza la caché de la API y comprueba que la consola y el
   portal responden 200 con `availability: null` y series vacías.
8. Restaura el sitio y Prometheus al salir, incluso si algo falla (`trap`).

Duración aproximada: 8–12 minutos, más la espera de 65 s del punto 7 y el tiempo de recuperación del
sitio (hasta 3 minutos). La salida debe terminar en:

```text
Demo de la spec 010: todo OK (mes YYYY-MM, incidente N).
```

Si imprime `FALLA`, el código de salida es 1 y hay que anotar cuál comprobación falló. El script
restaura el sitio y Prometheus, pero **verificar al final** (sección 6).

> La espera de 65 s es obligatoria: la API cachea la disponibilidad 60 s. Si se consulta antes, se ve
> el valor anterior y CA-8 parecería incumplido.

## 3. Opción guiada: paso a paso con las pantallas

Si el jurado quiere ver cada pantalla, hacer esta secuencia. El script puede correr al final como
evidencia, o antes para dejar los datos listos.

### Paso 1 · Consola de la agencia (CA-1, CA-2, CA-3)

1. Abrir `http://hub.local`, entrar como `sofia@forjadigital.test`.
2. Ir a **Inicio** (`/agencia`).
3. Señalar en la tabla:
   - Los **3 clientes**: La Sazón, El Tornillo y el Consultorio.
   - **Estado** del sitio, **disponibilidad** del mes y si **cumple el objetivo** del plan.
   - **Cumplimiento de SLA**, **MTTR**, **solicitudes abiertas/cerradas**, **horas** y **costo**.
   - La tarjeta o columna de **carga por técnico**: horas registradas frente a 120 disponibles.
4. Decir en voz alta la fórmula y la fuente de cada KPI; están en [`docs/kpi.md`](../../docs/kpi.md).
   La consola no inventa valores: si un dato no existe, muestra «sin datos».

**Esperado:** La Sazón con disponibilidad y SLA del mes, MTTR con el incidente de T18 (no `null`), y
la carga de cada técnico. El consultorio puede aparecer con «sin datos» si su serie no tiene puntos:
eso también es correcto (CA-8).

### Paso 2 · Carga y costo (CA-2, CA-3)

1. En la misma pantalla, leer las horas y el costo de La Sazón.
2. Verificar la cuenta: `horas × 25 000 COP = costo` (valor provisional aprobado en T02).
3. Señalar la carga del técnico: `horas ÷ 120` y la marca de riesgo cuando supera el 80 %.

**Esperado:** los números coinciden con `work_logs` del mes; ningún cliente ve esta información en su
portal.

### Paso 3 · Detalle técnico y Grafana (CA-6)

1. Abrir `http://hub.local/agencia/clientes/1/metricas` (o hacer clic en La Sazón → **Métricas**).
2. Mostrar las dos gráficas SVG: disponibilidad y latencia p95, con puntos cada 5 minutos.
3. Señalar el **hueco** de la caída de T18 (disponibilidad en 0 durante la caída).
4. Hacer clic en **Abrir en Grafana**: debe abrir `http://grafana.hub.local` en el panel del sitio.

**Esperado:** la gráfica tiene el hueco y el enlace abre Grafana con la sesión o el formulario de
entrada. Si Grafana pide contraseña, tener a mano la del Secret `grafana-admin`.

### Paso 4 · Portal del cliente (CA-4, CA-7)

1. Cerrar sesión y entrar como `contacto@lasazon.test` (contraseña `HUB_PASSWORD`).
2. La aplicación lleva a **Inicio** (`/portal`). Leer en voz alta:
   - **Estado actual:** «Su sitio está disponible.» (o la frase de caído si aún no se recuperó).
   - **Disponibilidad del mes** frente al **objetivo acordado** (99,9 % en Premium).
   - La frase de disponibilidad: dentro o por debajo del objetivo, según el mes.
   - **Fallas del mes**, con título y estado, sin jerga.
   - **Solicitudes del mes**, con su estado.
3. Comprobar que **no** aparecen costo, horas ni nombres de técnicos (CA-7).
4. Probar que la URL de otro cliente no es accesible: `http://hub.local/portal` no tiene selector de
   cliente; el alcance lo fija la sesión (spec 007).

**Esperado:** todo el texto sale de [`frontend/src/texts/cliente.ts`](../../frontend/src/texts/cliente.ts)
y coincide con el [glosario](../../docs/glosario.md). Ninguna palabra técnica en pantalla.

### Paso 5 · La caída (CA-1, CA-4, CA-9)

Se puede hacer a mano o dejar que el script lo haga:

```bash
kubectl -n cliente-restaurante scale deploy/web --replicas=0
```

1. El sitio deja de responder (`curl -I http://restaurante.hub.local/health`).
2. En **30–45 s** Alertmanager avisa al Hub y se abre el incidente P1 (regla `SitioCaido`, `for: 30s`).
3. Refrescar la consola: La Sazón queda **caída** y el incidente aparece en la lista.
4. Refrescar el portal: «Su sitio no está disponible en este momento; ya estamos trabajando en ello.»
5. Esperar a que el incidente esté **abierto** y mostrar la hora de inicio (no la de la alerta).
6. Mantener el sitio caído hasta pasar el siguiente múltiplo de 5 minutos. La serie se dibuja cada 5
   minutos; si la caída dura menos, puede no quedar ningún punto en 0 y la gráfica no mostraría el
   hueco. El script espera solo; a mano, mirar el reloj y recuperar después del siguiente `:00`,
   `:05`, `:10`, etc. El MTTR incluirá esa espera, y es correcto: la caída duró eso.

Recuperar:

```bash
kubectl -n cliente-restaurante scale deploy/web --replicas=1
kubectl -n cliente-restaurante rollout status deploy/web --timeout=180s
```

7. Cuando el sitio responde 200, en **30–45 s** el incidente queda **mitigado**.
8. Refrescar la consola: el **MTTR** deja de ser `null` y muestra los minutos de la caída.
9. Refrescar el portal: la falla aparece como **Mitigada** y el texto explica qué pasó sin jerga.
10. Abrir **Métricas**: la serie muestra el hueco en 0.

**Esperado:** un solo incidente (no duplicados), MTTR calculado con la hora real de la caída y el
sitio respondiendo 200 al final.

### Paso 6 · Prometheus apagado (CA-8)

1. Apagar Prometheus:

   ```bash
   kubectl -n monitoring scale deploy/prometheus --replicas=0
   kubectl -n monitoring rollout status deploy/prometheus --timeout=90s
   ```

2. **Esperar 65 s** (caché de 60 s de la API).
3. Refrescar la consola: sigue cargando (200) y las tarjetas de disponibilidad dicen **«sin datos»**.
4. Refrescar el portal: sigue cargando y la disponibilidad dice **«Todavía no tenemos datos de su
   sitio este mes.»**
5. Abrir **Métricas**: las gráficas quedan vacías, sin error.
6. Encender Prometheus:

   ```bash
   kubectl -n monitoring scale deploy/prometheus --replicas=1
   ```

**Esperado:** ningún 100 % inventado, ninguna pantalla en error y el resto de la consola (SLA, MTTR,
solicitudes, costo) sigue funcionando. Puede tardar uno o dos minutos en volver a tener datos.

### Paso 7 · Cero incidentes (CA-9)

No hay que borrar nada: el diseño ya lo cubre. Para mostrarlo, elegir un cliente o un mes sin
incidentes (por ejemplo, el mes anterior) y señalar que el MTTR dice **«sin incidentes este mes»**, no
`0`. En la API: `mttr` es `null`.

## 3.1. Ejecución registrada de T18 (26 oct 2026)

Primera corrida completa en el clúster `hub` (k3d, k3s 1.32.9) con el Hub, los 3 sitios, Prometheus,
Blackbox, Alertmanager y Grafana. Salida del script:

```text
Demo de la spec 010: todo OK (mes 2026-10, incidente 1).
```

| Comprobación | Resultado |
|---|---|
| Tablero: 3 clientes, 2 técnicos, SLA, solicitudes, horas/costo, disponibilidad | OK |
| Portal: disponibilidad, objetivo, sin costo/horas/técnicos, 404 cruzado | OK |
| Serie del mes | 2 puntos al inicio; con la caída mostró el valor 0 |
| Caída del sitio | Incidente #1 abierto por la alerta en menos de 5 min |
| Recuperación | Incidente mitigado; MTTR 3,25 min |
| Prometheus apagado | 3 clientes con `availability: null`, portal igual y series vacías, todo con 200 |

Hallazgos corregidos antes de la corrida: la etiqueta `client` de Prometheus no lleva el prefijo
`cliente-` (el tablero salía `null`) y la disponibilidad tomaba el último sondeo en vez del promedio
del mes. Ver [revision-industrial.md](revision-industrial.md#8-hallazgos-de-la-puesta-en-marcha-en-el-clúster-26-oct-2026).

Esta corrida cierra **T18**. **T20 sigue abierta**: falta la demo visual con el jurado y las capturas.

## 4. Mapa de criterios a evidencia

| CA | Qué se ve | Dónde |
|---|---|---|
| CA-1 | Estado, disponibilidad vs. objetivo, SLA, MTTR, solicitudes, horas y costo por cliente | `/agencia` |
| CA-2 | Horas registradas vs. disponibles por técnico | `/agencia` |
| CA-3 | Fórmulas de `docs/kpi.md` aplicadas sin cambios | `/agencia` y `docs/kpi.md` |
| CA-4 | Estado, disponibilidad, incidentes y solicitudes con textos del glosario | `/portal` |
| CA-5 | 3 personas no técnicas, al menos 2 entienden el estado | [`context.md`](context.md) |
| CA-6 | Disponibilidad, latencia y errores; enlace a Grafana | `/agencia/clientes/1/metricas` |
| CA-7 | El cliente solo ve lo suyo; sin costo, horas ni técnicos | `/portal` y 404 al pedir otro cliente |
| CA-8 | Prometheus apagado: 200 y «sin datos» | `/agencia`, `/portal`, `/metricas` |
| CA-9 | Sin incidentes: «sin incidentes este mes», no 0 | `/portal` y `mttr: null` |

## 5. Si algo sale mal

| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| La disponibilidad sigue en el valor anterior después de apagar Prometheus | Caché de 60 s | Esperar 65 s y refrescar; no reiniciar la API |
| El incidente no aparece | Regla `SitioCaido` o webhook de Alertmanager | Revisar `kubectl -n monitoring logs deploy/alertmanager` y `kubectl -n hub logs deploy/api`; confirmar el Secret `hub-alertmanager` |
| El incidente no se mitiga | `send_resolved` o `group_interval` | Revisar Alertmanager; el sitio debe responder 200 antes de esperar |
| El tablero muestra «sin datos» con Prometheus encendido | Blackbox o job `sitios` sin datos | Revisar `probe_success{job="sitios"}` en Grafana; puede tardar en tener el primer punto |
| Grafana no abre | Entrada de `hosts` o Ingress | `curl -I http://grafana.hub.local`; revisar `kubectl -n monitoring get ingress` |
| El portal muestra otro cliente | Sesión equivocada | Cerrar sesión y entrar con `contacto@lasazon.test` |
| El MTTR sigue en `null` | El incidente no quedó `mitigado`/`cerrado` | Ver el detalle del incidente; el script espera hasta 300 s |
| El script falla al entrar | `HUB_PASSWORD` vacía o usuarios no sembrados | Repetir el comando del Secret; revisar el seed |

## 6. Cierre y restauración

Siempre, aunque la demo haya salido bien:

```bash
kubectl -n cliente-restaurante scale deploy/web --replicas=1
kubectl -n monitoring scale deploy/prometheus --replicas=1
kubectl -n cliente-restaurante rollout status deploy/web --timeout=180s
kubectl -n monitoring rollout status deploy/prometheus --timeout=180s
curl -s -o /dev/null -w '%{http_code}\n' http://restaurante.hub.local/health   # 200
```

Después:

1. Anotar en `tasks.md` el resultado de T20 y marcar la línea con el nombre de quien presentó:
   `- [x] T20 · … [Andres]`.
2. Guardar la salida del script y las capturas de las pantallas como evidencia de la demo.
3. Si la demo mostró un fallo de una tarea anterior, **no** marcar T20: abrir la tarea de corrección y
   repetir la demo.
4. Si se cambió un KPI o un texto durante la demo, repetir `pytest` y `npm run build` antes de cerrar.

## 7. Tiempos sugeridos

| Bloque | Minutos |
|---|---|
| Preparación y comprobaciones | 10 |
| Consola, carga/costo y detalle técnico | 10 |
| Portal del cliente | 5 |
| Caída, recuperación y MTTR | 5–10 |
| Prometheus apagado | 2 (más 65 s de espera) |
| Cierre y restauración | 5 |
| **Total** | **35–45** |

# Erratas del borrador `entrega/00-informe`

> Lista de lo que el borrador sin versionar dice y la evidencia de esta corrida (o el código) contradice. **El borrador no se editó.** Sirve para no arrastrar errores al informe nuevo, que se escribe desde `HECHOS.md`.

## Errores de fondo

| # | Dónde | El borrador dice | Lo verificado | Fuente |
|---|---|---|---|---|
| 1 | §11, ADR-12 | Red denegada por defecto, de entrada **y de salida**, en `hub`, `monitoring`, `gitea`, `mlops` y clientes | La salida solo se deniega en `hub` y en los clientes; `monitoring`, `gitea` y `mlops` solo restringen la entrada, y `gitea` y `mlops` no tienen `default-deny` | `gitops/hub/networkpolicy.yaml`, `gitops/clients/_base/networkpolicy.yaml`, `observability/networkpolicy.yaml`, `gitops/platform/gitea/networkpolicy.yaml`, `gitops/platform/mlops/networkpolicy.yaml` |
| 2 | §13, tabla de conservación (línea 132) | Loki guarda 72 h «solo de los Pods de clientes» | También recoge el namespace `hub` (expresión `cliente-.+\|hub`) | `observability/alloy/config.alloy` |
| 3 | §22 (texto fijo en `entrega/generar_tablas.py`) | La diferencia entre 956 y 1.134 se debe a pruebas que pertenecen a varias PF | Ningún archivo se repite entre PF; la diferencia son 21 archivos de prueba sin PF asignada. Hoy hay **1.139** recogidas (5 nuevas de T06/T07) | `B/junit-modo-completo.xml` |
| 4 | RNF-11, §19, E-05, `evidencias.csv`, `trazabilidad.csv` | Cita «spec 015, T02 / T03 / T07» | En `dev` la spec 015 no tiene `tasks.md`; esas tareas (T02 reinicio, T03 versión con secreto, T07 caída real) existen en el PR #214, **sin fusionar**. Citarlas solo si se fusiona | `specs/015-demo-integrada/`, PR #214 |
| 5 | RF-27, E-18 | Prueba de voz en navegador del 16 nov | Las capturas eran del 15 nov (sin versionar); en esta corrida se repitió y pasó el **17 nov** con 4 capturas | `D/D12-voz-navegador.log`, `D/capturas-voz/` |
| 6 | §3, §8, §9, §14, §18, §19 | MTTR de 1,3 a 1,5 min en el caso del restaurante (`docs/bitacora.md`) | El 1,3 era del colegio. **Medido hoy:** caso del restaurante con rollback, MTTR **3,4 min** (mitigado a los 170 s del rollback); mitigación automática 166–169 s después de revertir; detección 48–49 s | `C/C25-caso-restaurante.log`, `C/C26-cronometro.log` |

## Imprecisiones

| # | Dónde | Detalle | Fuente |
|---|---|---|---|
| 7 | RNF-09 | Dice que solo existen `OLLAMA_URL` y `VOZ_URL`; también está `gate_model_url` | `backend/app/config.py` |
| 8 | ADR-24 | Atribuye a `9ef0377` los ajustes de MLflow, pero los introdujo `b3a5126` | `git show b3a5126` |
| 9 | ADR-17 | «Índice único» de la huella del incidente: es único **parcial** (solo entre incidentes abiertos) | `backend/app/models/incident.py` |
| 10 | RNF-07 | La evidencia citada mide la recuperación, no la detección; la detección medida hoy es de 48–49 s | `C/C26-cronometro.log` |
| 11 | §3 | «95 % a 100 % de acierto» omite el modo RAG (hoy 92,5 % en ayuda) | `D/D02-eval-rag-ayuda.log` |
| 12 | Varias | `docs/bitacora.md:30` cae en una línea vacía (el texto está en la 29) | `docs/bitacora.md` |
| 13 | RNF-11 | «Hecho en Compose» en §9 y «Parcial» en la matriz | `entrega/datos/trazabilidad.csv` |
| 14 | ADR-21 | «El clúster usa `rag`» no se puede comprobar desde el código; `configurar-ia.sh` trae `completo` por defecto | `gitops/hub/configurar-ia.sh` |
| 15 | ADR-25 (§11, línea 216) | Transcripción de 1,9 s | Hoy, con faster-whisper `small`: 3,3 s de media (p95 4,2 s) | `D/D11-voz-evaluacion.log` |

## Problemas de método del borrador

| # | Problema | Consecuencia | Ahora |
|---|---|---|---|
| 16 | `entrega/ejecutar_pruebas.py` fuerza `ASSISTANT_CONTEXT_MODE=completo` | Esconde las 6 pruebas que fallan con el `.env` del equipo (H-TEST-01) | Las dos corridas están en `B/` |
| 17 | `ejecutar_pruebas.py` no guarda la salida y cuenta las omitidas como «Cumplido» | Las cifras de la §22 no tenían respaldo | Hay JUnit en `B/` |
| 18 | 28 de 30 evidencias estaban «pendientes» y aun así la matriz marcaba «Cumplido» | Estado sin prueba | Las capturas y los registros están en `E/`, `D/` y `C/` |
| 19 | Las «repeticiones del 16 nov» de la evaluación de la IA no se guardaron | Cifras sin archivo | `D/eval-*` con JSON. Coinciden con el borrador en 95,0 % (ayuda), 90,0 % (inyección), recuperación 93,5 % y 5/5 maliciosos |
| 20 | `entrega/datos/licencias.csv` no está reverificado | Versiones o licencias pueden estar viejas | Regenerar desde el SBOM del CI |

## Lo que el borrador tenía bien y esta corrida confirma

- 40 pruebas de `ai/`, 9 Applications Synced y Healthy, 17 migraciones y 22 tablas.
- Las versiones de las herramientas de la puerta (Gitleaks 8.30.1, Trivy 0.76.1, Syft 1.55.0, Cosign 3.1.4) y de OpenTofu y sus proveedores.
- Los SLO (99,0 / 99,5 / 99,9) y el SLA de P1 (15 min y 4 h).
- Las 11 alertas y los digests de los modelos.

Fuentes: `RESUMEN.md`, `HECHOS.md`.

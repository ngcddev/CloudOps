# Plan 015 · Demo integrada

> Cómo se construye [la spec](spec.md).

## Estructura

```
demo/
├── reset.sh              # reinicia base, hub-gitops y sitios a v1
├── guion.md              # 10 puntos con tiempo, responsable, pantalla y plan B
├── checklist-salon.md    # IPs, /etc/hosts, PC B visible, modelos cargados, Trivy DB descargada
└── video/                # enlace al video de respaldo (el archivo no va al repo)
seed/
└── demo/                 # datos del estado inicial: clientes, usuarios, tickets, borradores aprobados
```

## `reset.sh`

1. Vacía y recrea la base del Hub (`alembic downgrade base && upgrade head`) y carga `seed/`.
2. Fuerza en `hub-gitops` los tags `v1` de los 3 clientes (commit `chore(demo): reinicio`).
3. Espera a que Argo CD reporte `Synced` + `Healthy` en los 3.
4. Verifica `/health` de los 3 sitios y del Hub; imprime ✓ / ✗ por punto.

## Guion (borrador de tiempos)

| # | Punto | Min | Responsable | Plan B |
|---|---|---|---|---|
| 1 | Agencia y clientes | 1 | Backend | — |
| 2 | Contenedores y k3s | 1,5 | Cloud | Captura de `kubectl` |
| 3 | Puerta de seguridad | 2 | DevSecOps | Corrida grabada del pipeline |
| 4 | Dashboard y portal | 1,5 | Frontend | — |
| 5 | Falla e incidente | 2 | SRE | Video del minuto de detección |
| 6 | Prioridad y SLA | 1 | Industrial | — |
| 7 | Rollback y MTTR | 1,5 | Cloud | — |
| 8 | Reportes | 1 | Industrial | PDF ya generado |
| 9 | Asistente IA | 1,5 | Backend | Borrador semilla aprobado |
| 10 | Infografía | 1,5 | Frontend | Infografía ya generada |
| | **Total** | **14,5** | | |

## Riesgos

| Riesgo | Respuesta |
|---|---|
| Red del salón bloquea tráfico entre PC | Router propio o cable directo; probado antes |
| Pasarse de tiempo | Ensayos cronometrados; cortar explicación, nunca pasos |

## Cómo se verifica

- Tres ensayos completos cronometrados, anotados en `context.md`.
- `reset.sh` corrido dos veces seguidas deja el mismo estado.

# Plan 013 · Reportes operativo y ejecutivo

> Cómo se construye [la spec](spec.md). Reutiliza `services/kpi.py` de la spec 010.

## Stack

Hub (FastAPI + PostgreSQL); plantilla HTML con Jinja2; PDF con WeasyPrint en el contenedor del API
(sin servicios externos).

## Generación

- `services/reports.py`: `operational(month)` y `executive(client_id, month)` devuelven un dict con
  todos los datos (misma fuente que el dashboard).
- `templates/reports/operational.html`, `templates/reports/executive.html`: blanco y negro, A4.
- Textos del ejecutivo desde el glosario y desde `ai_drafts` aprobados (spec 012) si existen.

## Modelo de datos

| Tabla | Campos |
|---|---|
| `reports` | `id` · `kind` (`operativo` / `ejecutivo`) · `client_id` (nullable) · `month` · `data` jsonb · `pdf_path` · `generated_by_id` · `created_at` |

Guardar `data` congela los números del mes para que el reporte no cambie después.

## API y pantallas

| Método | Ruta | Rol |
|---|---|---|
| POST | `/api/reports` (`kind`, `client_id`, `month`) | agencia |
| GET | `/api/reports/{id}` | agencia, cliente dueño |
| GET | `/api/reports/{id}/pdf` | agencia, cliente dueño |

- `/agencia/reportes`: generar y listar.
- `/portal/reportes`: el cliente ve y descarga los suyos.

## Riesgos

| Riesgo | Respuesta |
|---|---|
| WeasyPrint pesa en la imagen | Imagen multi-stage; si no cabe, impresión del navegador a PDF |

## Cómo se verifica

- `pytest`: los números del reporte = los del dashboard con los mismos datos semilla.
- Revisión del ejecutivo contra el glosario.

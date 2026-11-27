# Plan 013 · Reportes operativo y ejecutivo

> Cómo se construye [la spec](spec.md). Reutiliza `services/kpi.py` de la spec 010.

## Stack

Hub (FastAPI + PostgreSQL); PDF con **reportlab** (Python puro, A4 blanco y negro) en el contenedor de la API, sin servicios
externos. Cambio respecto del plan original (14 nov): no se usó WeasyPrint + Jinja2 porque WeasyPrint exige librerías del
sistema (Pango) en la imagen; reportlab suma ~60 MB y nada más.

## Generación

- `services/reports.py`: `operational(month)` y `executive(client_id, month)` devuelven un dict con
  todos los datos (misma fuente que el dashboard).
- `services/report_pdf.py`: `ejecutivo_pdf` (una página A4 vertical, se encoge si no cabe) y `operativo_pdf` (A4 horizontal).
- Textos del ejecutivo desde el glosario y desde `ai_drafts` aprobados (spec 012) si existen.

## Modelo de datos

| Tabla | Campos |
|---|---|
| `reports` | `id` · `kind` (`operativo` / `ejecutivo`) · `client_id` (nullable) · `month` · `data` JSON · `generated_by_id` · `created_at` (migración 0014; sin `pdf_path`: el PDF sale siempre de `data`) |

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

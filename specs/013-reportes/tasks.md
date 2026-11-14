# Tareas 013 · Reportes operativo y ejecutivo

> Cada tarea: una acción con verbo · se comprueba en minutos · menos de un día · se integra sola.
> Rama por tarea: `feat/013-tNN-slug`. Poner el nombre de quien la toma entre corchetes.

## Datos y API

- [x] T01 · Crear la tabla `reports` con su modelo y la migración 0014 — **Verifica:** `alembic upgrade head` y `downgrade` funcionan (`test_migrations.py`).
- [x] T02 · Escribir `services/reports.py`: `operativo(db, mes)` y `ejecutivo(db, cliente, mes)` con las mismas funciones de `services/kpi.py` que los tableros — **Verifica:** `pytest tests/test_reports.py`: las cifras del operativo son las de `GET /api/dashboard/agency` para el mismo mes (CA-1, CA-5).
- [x] T03 · Escribir el texto del ejecutivo con las frases del glosario y solo mensajes aprobados por una persona (spec 012) — **Verifica:** ningún texto del ejecutivo ni de su PDF trae un término de `terminos_prohibidos.txt`; un borrador o un resumen técnico no entran (CA-3).
- [x] T04 · Crear `POST /api/reports`, `GET /api/reports`, `GET /api/reports/{id}` y `GET /api/reports/{id}/pdf`, con la bitácora y el alcance por cliente — **Verifica:** el cliente solo ve y descarga su ejecutivo (404 con el de otro y con el operativo); sin sesión, 401; los datos quedan congelados.

## PDF

- [x] T05 · Escribir `services/report_pdf.py` con reportlab — **Verifica:** el ejecutivo ocupa **una** página incluso con 9 fallas de mensajes largos; el texto del PDF coincide con el reporte; el PDF se genera también en la imagen de producción (CA-2, CA-4). *Revisado a ojo: ambos PDF renderizados a imagen.*

## Pantallas

- [x] T06 · Crear `/agencia/reportes` (generar por tipo, cliente y mes, y descargar) y `/portal/reportes` (el cliente descarga los suyos) — **Verifica:** `tsc` y `vite build` pasan. *Falta recorrerlas en el navegador con la API real.* [ ]
- [ ] T07 · Revisar con Industrial el contenido del operativo (qué KPI y qué comparación) y el lenguaje del ejecutivo — **Verifica:** Industrial aprueba el formato. [ ]

## Cierre

- [ ] T08 · Demo: reporte operativo del mes y ejecutivo de La Sazón con el incidente del día explicado, descargado en PDF — **Verifica:** todos los criterios de [spec.md](spec.md#criterios-de-aceptación). [ ]

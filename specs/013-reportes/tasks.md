# Tareas 013 · Reportes operativo y ejecutivo

> Cada tarea: una acción con verbo · se comprueba en minutos · menos de un día · se integra sola.
> Rama por tarea: `feat/013-tNN-slug`. Poner el nombre de quien la toma entre corchetes.
>
> Fechas: módulo 5 del 3 al 12 nov. La spec se adelanta desde el 31 oct porque solo usa datos del Hub
> (carril de producto, principio 9). Se apoya en la 010 (`services/kpi.py`) y en la 012 (mensajes aprobados).

## Cómo repartirlo

| Carril | Tareas | Necesita el clúster | Puede empezar |
|---|---|---|---|
| Backend | T01–T06 | No (`pytest` con la semilla) | Ya: la 010 está terminada y la 012 tiene T10 |
| Frontend | T07–T11 | No (datos de prueba hasta que la API responda) | Cuando el Backend tenga T04–T06 |
| Servicio (Industrial) | T12 | No | Cuando el Frontend tenga T10 |
| Integración | T13 | Sí | Al cerrar Backend y Frontend |

Decisiones de esta lista:

1. **El PDF lo hace el navegador** («Imprimir → Guardar como PDF»), con una hoja de estilos A4 en blanco y
   negro. Es la respuesta al riesgo que ya anota el [plan](plan.md#riesgos): WeasyPrint necesita Pango y
   Cairo en la imagen del API, que el PC A no tiene de sobra. Por eso no hay `pdf_path` ni
   `GET /api/reports/{id}/pdf`, y la imagen no crece.
2. **Los números salen de las mismas funciones del dashboard** (`services/kpi.py`), así coinciden siempre
   (CA-5). El reporte guarda una copia en `data` al generarse: los números del mes quedan congelados.
3. **El ejecutivo usa el mensaje aprobado de la 012.** Si una falla no tiene mensaje aprobado, usa la
   frase del glosario («Se detectó una falla temporal y se activó el proceso de recuperación.»). Nunca
   muestra un borrador.
4. **El cliente solo ve sus reportes ejecutivos.** El operativo (costos, horas, técnicos) es de la agencia.

## Backend

- [x] T01 · Crear el modelo `Report` (tabla `reports`) con la migración `0011` — **Verifica:** `alembic upgrade head` y `alembic downgrade -1` sin errores; los borradores de la 012 siguen ahí. *`tests/test_migrations.py` sube a `0011` y baja a `0010` con `ai_drafts` intacta.* [sebastian-debug]
- [x] T02 · Escribir `operational(db, month)` en `services/reports.py`: KPI de la spec 000 por cliente, el total de la agencia y los mismos valores del mes anterior — **Verifica:** `pytest`: con la semilla, cada cliente trae exactamente lo que da `GET /api/dashboard/agency` para ese mes y el total suma horas, costo y solicitudes (CA-1, CA-5). *Para garantizar CA-5 se sacó `kpi.client_month_kpis`, que ahora usan el dashboard y el reporte. El total suma horas, costo y solicitudes y promedia disponibilidad, SLA y MTTR solo de los clientes con dato.* [sebastian-debug]
- [x] T03 · Escribir `executive(db, client_id, month)` en `services/reports.py`: disponibilidad frente al objetivo, fallas con su mensaje aprobado, cambios publicados y solicitudes atendidas, con los textos del glosario — **Verifica:** `pytest`: una falla con mensaje aprobado lo trae, una sin él trae la frase del glosario, un borrador nunca aparece, y `forbidden_terms` sobre todo el texto da vacío (CA-2, CA-3). *No se usa el título del incidente (una alerta puede traer texto técnico): solo fecha, hora y mensaje. Las recuperaciones no cuentan como «actualización publicada». El tiempo de recuperación se redondea igual que en el portal.* [sebastian-debug]
- [x] T04 · Crear `POST /api/reports` (`kind`, `client_id`, `month`) solo para la agencia, que guarda `data` — **Verifica:** `pytest`: 201 con el reporte; ejecutivo sin cliente → 422; mes con otro formato → 422; como cliente → 403; queda fila en `audit_logs` (CA-4). *El operativo ignora `client_id`. Se agregó al manejador de errores el caso de formato (antes salía en inglés) y los nombres «mes» y «cliente».* [sebastian-debug]
- [x] T05 · Crear `GET /api/reports` y `GET /api/reports/{id}` con alcance por rol — **Verifica:** `pytest`: la agencia ve todos; el cliente ve solo sus ejecutivos; el operativo o el de otro cliente → 404 para el cliente (CA-4). *La lista no trae `data` (puede pesar). Para el cliente, un reporte ajeno o el operativo responde 404, igual que los demás recursos con alcance por cliente.* [sebastian-debug]
- [x] T06 · Comprobar que un reporte guardado no cambia si después llega una falla nueva en el mismo mes — **Verifica:** `pytest`: el `GET` del reporte trae los números de cuando se generó (plan: «guardar `data` congela los números»). *Tras generar el ejecutivo se abrió una falla nueva en octubre: el guardado siguió igual y uno nuevo del mismo mes sí la contó.* [sebastian-debug]

## Frontend

- [x] T07 · Agregar a `frontend/src/api.ts` los tipos y llamadas de reportes, con datos de prueba si la API no responde — **Verifica:** `tsc` sin errores. *Los datos de prueba reutilizan `mockClientKpi` del dashboard y los mensajes aprobados de la 012.* [sebastian-debug]
- [ ] T08 · Crear `/agencia/reportes`: formulario para generar (tipo, cliente, mes) y lista de reportes, y activar «Reportes» en el menú — **Verifica:** con datos de prueba se genera un operativo y un ejecutivo de La Sazón y aparecen en la lista. [ ]
- [ ] T09 · Crear la vista del reporte operativo: tabla por cliente con el mes anterior al lado y el total, y botón «Descargar PDF» — **Verifica:** la vista de impresión del navegador muestra la tabla en A4, en blanco y negro, sin menús (CA-1, CA-4). [ ]
- [ ] T10 · Crear la vista del reporte ejecutivo en **una página** A4 con «Descargar PDF» — **Verifica:** la vista de impresión del navegador cabe en una página con La Sazón (disponibilidad, una falla con su mensaje, cambios y solicitudes) (CA-2, CA-4). [ ]
- [ ] T11 · Crear `/portal/reportes` para que el cliente vea y descargue sus reportes ejecutivos, y agregarlo al menú del portal — **Verifica:** con datos de prueba el cliente ve solo los ejecutivos de su empresa y abre la vista de una página (CA-4). [ ]

## Servicio (Industrial)

- [ ] T12 · Revisar el ejecutivo de La Sazón contra el glosario y aprobar el formato de los dos reportes — **Verifica:** nota de aprobación en este archivo, con lo que se cambió (CA-3). [ ]

## Integración

- [ ] T13 · Publicar el Hub con la 013 (migración `0011`) — **Verifica:** `kubectl rollout status` en verde y `alembic current` en `0011 (head)`. [ ]

## Cierre

- [ ] T14 · Demo: generar el operativo del mes (SLA, MTTR, carga y costo por cliente) y el ejecutivo de La Sazón, y descargarlo en PDF: una página, sin jerga, con la falla del día explicada — **Verifica:** todos los criterios de [spec.md](spec.md#criterios-de-aceptación). [ ]

# Plan 002 — Incidente con rollback

## Cambios al modelo de datos
- **clients**: añadir `status` (operativo/caído), `stable_version`, `current_version`.
- **incident_events**: id, ticket_id, event (texto), created_at.

## API
| Método | Ruta | Función |
|---|---|---|
| POST | `/api/clients/{id}/simulate-failure` | Marca caído, crea ticket P1, registra eventos |
| POST | `/api/clients/{id}/rollback` | Vuelve a versión estable, cierra el ticket, registra eventos |
| GET | `/api/tickets/{id}/timeline` | Línea de tiempo del incidente |
| GET | `/api/tickets/{id}/client-message` | Mensaje simple para el cliente |

## Lógica
- **Simular falla:** `status='caído'`, `current_version='v1.1-defectuosa'`; crear ticket P1 reutilizando la lógica de SLA de la feature 001; eventos "Falla detectada" e "Incidente P1 abierto".
- **Rollback:** `current_version = stable_version`, `status='operativo'`; cerrar ticket; eventos "Rollback ejecutado" y "Servicio recuperado"; tiempo de recuperación = cierre − creación.
- **Mensaje al cliente (plantilla):** "Hola {cliente}, detectamos una falla temporal en su sitio a las {hora}. Activamos la recuperación y a las {hora_fin} el servicio volvió a funcionar. Tiempo total: {min} minutos."

## Interfaz
En la tarjeta de cada cliente: estado, versiones y botones "Simular falla" / "Rollback". Panel de línea de tiempo y mensaje al cliente para el incidente seleccionado.

# Plan 001 — Clientes, tickets y SLA

## Modelo de datos (SQLite)
- **clients**: id, name, site_url, plan, created_at
- **tickets**: id, client_id, title, description, priority (P1–P4), status, created_at, respond_by, resolve_by, closed_at

## API
| Método | Ruta | Función |
|---|---|---|
| GET | `/api/clients` | Lista clientes |
| POST | `/api/clients` | Crea cliente |
| GET | `/api/tickets` | Lista tickets con estado de SLA |
| POST | `/api/tickets` | Crea ticket y calcula SLA |
| POST | `/api/tickets/{id}/close` | Cierra ticket |

## Lógica de SLA (`sla.py`)
- Diccionario prioridad → (minutos de respuesta, minutos de solución).
- `respond_by = created_at + respuesta`; `resolve_by = created_at + solución`.
- Estado SLA: si el ticket no está cerrado y `ahora > resolve_by` → "Vencido"; si no → "A tiempo".

## Interfaz
Una sola página con: formulario de cliente, formulario de ticket y tabla de tickets (columnas: cliente, título, prioridad, estado, SLA).

## Datos de demo (`seed.py`)
Restaurante "La Sazón", tienda "Moda Cauca", clínica "Dental Popayán", con un ticket de ejemplo cada uno.

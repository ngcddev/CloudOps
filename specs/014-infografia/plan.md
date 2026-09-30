# Plan 014 · Infografía mensual

> Cómo se construye [la spec](spec.md). Corre en el **PC B**, por turnos con Ollama (6 GB de VRAM).

## Stack (módulo 6)

| Pieza | Herramienta |
|---|---|
| Imagen | Stability Matrix + ComfyUI, SD 1.5 (SDXL Turbo solo si cabe en 6 GB) |
| Composición | Plantilla SVG/HTML en el Hub con los datos + imagen incrustada |
| Sugerencia de causa (opcional) | Modelo de código en Ollama (ej. Qwen2.5-Coder 7B) |

## Flujo

1. `POST /api/infographics` (`client_id`, `month`) → toma `data` del reporte ejecutivo (spec 013).
2. `integrations/comfyui.py`: envía un workflow JSON guardado en `ai/comfyui/infografia.json`
   (prompt según el tipo de negocio: restaurante, ferretería, consultorio; 512×512; 20 pasos) por la
   API de ComfyUI (`/prompt`, luego `/history`). Timeout 90 s.
3. Compone `templates/infographic.svg` con los números y la imagen; exporta PNG.
4. Guarda con estado `borrador_ia`; aprobación igual que la spec 012.

## Modelo de datos

| Tabla | Campos |
|---|---|
| `infographics` | `id` · `client_id` · `month` · `status` · `image_path` · `seed` · `model` · `duration_ms` · `approved_by_id` · `created_at` |

## Sugerencia de causa (RF-23, opcional)

`POST /api/incidents/{id}/cause-suggestion`: envía al modelo de código las últimas líneas de Loki y
el diff del último cambio en `hub-gitops`; guarda la respuesta como `borrador_ia` en `ai_drafts`
(`kind = causa`). Nunca se muestra al cliente.

## Riesgos

| Riesgo | Respuesta |
|---|---|
| VRAM compartida con Ollama | `keep_alive` corto; generar infografías cuando no hay borradores en curso |
| Generación > 2 min | SD 1.5 a 512 px y pocos pasos; ilustración por defecto como respaldo |

## Cómo se verifica

- Cronometrar 3 generaciones seguidas (< 2 min cada una).
- Comparar los números de la infografía con el reporte ejecutivo del mismo mes.

# frontend/ — Consola de agencia y portal del cliente

React + Vite + TypeScript, con react-router-dom y CSS propio (sin librerías de UI): monocromo con un solo acento verde, en tema claro y oscuro.
Las fuentes Geist se sirven desde el propio paquete (`@fontsource-variable`), sin CDN. Los colores, radios y tipografía
son variables al inicio de `src/styles.css`; el tema lo fija `data-theme` en `<html>` (script de `index.html` y `ThemeToggle`).
Ver el [plan 001](../specs/001-clientes-y-planes/plan.md#pantallas).

**Responsable en el módulo 1:** Sistemas 4 (Frontend). El `Dockerfile` lo escribe Sistemas 3
(DevSecOps) junto con el servicio `web` de `docker-compose.yml`.

## Estructura esperada

```
frontend/
├── Dockerfile           # build con Node → nginx-unprivileged (puerto 8080)
└── src/
    ├── main.tsx, App.tsx
    ├── api.ts           # todas las llamadas a la API pasan por aquí
    ├── styles.css
    ├── pages/agencia/   # pantallas de la consola
    └── components/
```

## Cómo se ejecuta

| Qué | Comando |
|---|---|
| Desarrollo con recarga en caliente (`localhost:5173`, `/api` → `localhost:8000`) | `npm install` y `npm run dev` |
| Compilar | `npm run build` |
| Con todo el Hub | `docker compose up --build` (nginx sirve la SPA y reenvía `/api` al servicio `api`) |

## Trabajar antes de que exista la API

La forma de los datos está en [`seed/`](../seed/README.md). Mientras el backend no responda, `api.ts`
puede devolver esos JSON como datos de prueba, pero **solo en desarrollo** (`npm run dev`) o si se compila con
`VITE_MOCK=1` (una demo sin API): `VITE_MOCK=1 npm run build`. En producción esos datos no existen: el compilador
los quita del bundle (`MOCK_PERMITIDO` en `api.ts`) y un fallo de la API se ve como un error en pantalla, no como una
sesión de agencia falsa.

## Carga por pantalla y errores

Cada pantalla se carga en su propio archivo cuando se visita (`React.lazy` en `App.tsx`), con «Cargando…» mientras llega.
Un error al mostrar una pantalla no la deja en blanco: `ErrorBoundary` muestra un aviso con «Reintentar» y el marco
(menú y sesión) sigue en pantalla. Se prueba en un DOM real con `bash frontend/pruebas/error-boundary.sh` (Docker).
nginx comprime JS, CSS y JSON (`gzip`).

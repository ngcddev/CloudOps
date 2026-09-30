# frontend/ — Consola de agencia y portal del cliente

React + Vite + TypeScript, con react-router-dom y CSS propio en blanco y negro (sin librerías de UI).
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

## Trabajar antes de que exista la API

La forma de los datos está en [`seed/`](../seed/README.md). Mientras el backend no responda, `api.ts`
puede devolver esos JSON como datos de prueba; al conectar la API real solo cambia `api.ts`.

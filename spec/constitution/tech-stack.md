# Stack y convenciones

> Propuesta básica. El stack definitivo del equipo está **por definir**; se puede cambiar antes de generar código.

## Tecnologías
- **Backend:** Python 3.11 + FastAPI
- **Base de datos:** SQLite (archivo local, sin instalación)
- **Frontend:** HTML + CSS + JavaScript simple, servido por el mismo backend
- **Ejecución:** `uvicorn`; opcional Dockerfile
- **Sin servicios de terceros:** todo debe funcionar sin internet.

## Convenciones
- Idioma de la interfaz y textos: **español**.
- Diseño **blanco y negro**, sin temas de color.
- Código completo, **comentado en español**, con indicación de qué archivo es cada uno y cómo ejecutarlo.
- Nombres de código en inglés y snake_case; textos visibles en español.
- Prioridades: P1 (crítica), P2 (alta), P3 (media), P4 (baja).
- Fechas en ISO 8601 (UTC) en la base de datos.
- Datos de demostración ficticios (agencia + 3 clientes).

## Estructura esperada de `código/`
```
código/
├── app/
│   ├── main.py        # API
│   ├── models.py      # tablas
│   ├── sla.py         # reglas de SLA
│   └── static/        # HTML/CSS/JS
├── seed.py            # datos ficticios
├── requirements.txt
└── README.md
```

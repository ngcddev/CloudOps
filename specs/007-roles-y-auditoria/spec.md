# 007 · Acceso por roles y auditoría

> **Acciona:** Sistemas (Backend, Frontend)
>
> **Módulo:** 3 (producto: puede adelantarse) · **Requerimientos:** RF-01 (roles), RF-10 · **Depende de:** 001, 004, 005 · **Estado:** Tareas listas

## Qué y por qué

Cada usuario ve solo lo que le corresponde y toda acción sensible queda registrada. El cliente de
una PyME nunca ve datos de otra, y la agencia puede responder "¿quién hizo esto y cuándo?".

Hoy la consola y el portal no piden identidad: quien llama a la API dice qué rol tiene, qué cliente
es y a nombre de quién hace cada acción, y el portal usa un selector de cliente de desarrollo. Así,
cualquiera que alcance la API puede aprobar un cambio y publicar una versión (nota que dejó la 005).
Esta spec cambia eso por una sesión real y deja una bitácora que las specs siguientes también usan.

## Actores

| Actor | Qué hace en esta spec |
|---|---|
| Usuario `agencia` | Entra a la consola, ve y opera todo, consulta la bitácora |
| Usuario `cliente` | Entra al portal y ve solo su empresa, sus servicios y sus solicitudes |
| Sistema | Registra en la bitácora lo que hace solo (por ejemplo, confirmar una publicación) |

## Historias de usuario

- **HU-1.** Como usuario, quiero entrar con mi correo y contraseña, para acceder a lo mío.
- **HU-2.** Como cliente, quiero ver solo la información de mi empresa.
- **HU-3.** Como agencia, quiero que las acciones queden a nombre de quien las hizo, sin que nadie
  pueda firmarlas por otro.
- **HU-4.** Como agencia, quiero una bitácora de las acciones sensibles, para saber quién hizo qué y
  cuándo.

## Criterios de aceptación

- [ ] CA-1. Existen usuarios sembrados: al menos 2 de agencia y 1 por cliente, todos con contraseña
  de desarrollo.
- [ ] CA-2. Sin sesión, ninguna ruta de la API (salvo la salud del servicio y el inicio de sesión)
  ni del portal o la consola responde datos.
- [ ] CA-3. Un usuario `cliente` solo ve datos de su cliente; pedir los de otro responde "no
  encontrado". El portal ya no tiene selector de cliente.
- [ ] CA-4. Un usuario `cliente` no puede ejecutar acciones de agencia (clasificar, asignar, cambiar
  estado, registrar horas, crear o editar clientes, registrar, aprobar o rechazar cambios, ver el
  estado técnico de los servicios); el intento responde "sin permiso".
- [ ] CA-5. Las acciones quedan a nombre del usuario de la sesión: la petición ya no trae quién la
  hace, y nadie puede aprobar, rechazar ni registrar nada en nombre de otro.
- [ ] CA-6. Quedan en la bitácora, con usuario (o "Sistema"), acción, objeto y hora: cambiar
  prioridad, asignar y cambiar el estado de una solicitud; crear y editar un cliente; registrar,
  aprobar y rechazar un cambio; y la publicación confirmada o fallida de un cambio. Las specs
  siguientes registran sus acciones en la misma bitácora.
- [ ] CA-7. La bitácora no se puede editar ni borrar desde la aplicación.
- [ ] CA-8. Las contraseñas se guardan cifradas con hash; ninguna está en el código ni en el repo.

## Fuera de alcance

- Registro público de usuarios, recuperación de contraseña, inicio de sesión con terceros.
- Permisos finos más allá de dos roles.
- Gestión de usuarios desde la consola (los usuarios salen de los datos semilla).

## Demo de cierre

1. Entrar como cliente de La Sazón: solo aparecen sus datos y sus solicitudes.
2. Pedir a mano la solicitud o el cliente de El Tornillo: "no encontrado".
3. Entrar como agencia, aprobar un cambio de El Tornillo y abrir la bitácora: aparecen la aprobación
   con usuario y hora y, al terminar la publicación, la confirmación a nombre de "Sistema".
4. Cerrar sesión y abrir la consola: pide entrar de nuevo.

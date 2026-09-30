# 007 · Acceso por roles y auditoría

> **Módulo:** 3 (backend/frontend pueden adelantarse) · **Requerimientos:** RF-01 (roles), RF-10 · **Depende de:** 001 · **Estado:** Spec y plan

## Qué y por qué

Cada usuario ve solo lo que le corresponde y toda acción sensible queda registrada. El cliente de
una PyME nunca ve datos de otra, y la agencia puede responder "¿quién hizo esto y cuándo?".

## Actores

| Actor | Qué hace en esta spec |
|---|---|
| Usuario `agencia` | Ve y opera todo |
| Usuario `cliente` | Ve solo su empresa, sus servicios y sus solicitudes |
| Administrador | Consulta la bitácora |

## Historias de usuario

- **HU-1.** Como usuario, quiero entrar con mi correo y contraseña, para acceder a lo mío.
- **HU-2.** Como cliente, quiero ver solo la información de mi empresa.
- **HU-3.** Como administrador, quiero una bitácora de aprobaciones, despliegues y rollbacks, para
  saber quién hizo qué y cuándo.

## Criterios de aceptación

- [ ] CA-1. Existen usuarios sembrados: al menos 2 de agencia y 1 por cliente.
- [ ] CA-2. Sin sesión, ninguna ruta de la API ni del portal responde datos.
- [ ] CA-3. Un usuario `cliente` solo ve datos de su cliente; pedir los de otro responde "no
  encontrado".
- [ ] CA-4. Un usuario `cliente` no puede ejecutar acciones de agencia (aprobar, asignar, rollback).
- [ ] CA-5. Aprobar, rechazar, desplegar, hacer rollback, cambiar prioridad y aprobar textos de IA
  quedan en la bitácora con usuario, acción, objeto y hora.
- [ ] CA-6. La bitácora no se puede editar ni borrar desde la aplicación.
- [ ] CA-7. Las contraseñas se guardan cifradas con hash; ninguna está en el código.

## Fuera de alcance

- Registro público de usuarios, recuperación de contraseña, inicio de sesión con terceros.
- Permisos finos más allá de dos roles.

## Demo de cierre

1. Entrar como cliente de La Sazón: solo aparecen sus datos.
2. Cambiar a mano el id en la URL por el de El Tornillo: "no encontrado".
3. Entrar como agencia, aprobar un cambio y abrir la bitácora: la acción aparece con usuario y hora.

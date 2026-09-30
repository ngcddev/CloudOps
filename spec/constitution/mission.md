# Misión

## Qué construimos
**CloudOps Client Hub**: un centro de operación de servicios digitales para agencias web que atienden a varias PyMEs. Gestiona clientes, solicitudes, incidentes, SLA y reportes. **No es un Vercel**: el despliegue es solo una capacidad técnica dentro del flujo.

## Para quién
- **Agencia (usuario técnico):** necesita organizar el soporte de varios clientes, cumplir tiempos y recuperarse rápido de fallas.
- **Cliente PyME (usuario no técnico):** necesita saber, en lenguaje simple, si su sitio está bien y qué se hizo cuando falló.

## Flujo central
cliente → proyecto → servicio → solicitud/falla → prioridad (P1–P4) → SLA → resolución → comunicación al cliente.

## Caso demo de referencia
El sitio de un restaurante cae tras una actualización: se abre un incidente P1, arranca el SLA (respuesta 15 min, solución 4 h), se hace rollback a la versión estable y el cliente recibe una explicación sencilla.

## Alcance de esta versión básica (solo 2 funcionalidades)
1. Clientes, tickets y SLA.
2. Incidente con rollback y mensaje para el cliente.

## Fuera de alcance (por ahora)
Kubernetes real, GitOps, escáneres de seguridad, IA local, infografía, dashboards avanzados, multiusuario/roles. Quedan en el roadmap.

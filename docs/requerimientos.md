# Requerimientos

> Fuente: documento "CloudOps Client Hub — Plan por módulos y requerimientos".
> Cada requerimiento indica en qué módulo se construye y qué spec lo cubre, para que nada quede fuera del [roadmap](../constitution/roadmap.md).
> El mapa de specs con enlaces a cada carpeta está en [specs/README.md](../specs/README.md).
> Priorización MoSCoW: **M** = Debe, **S** = Debería, **C** = Podría, **W** = No esta vez.

## Actores

| Actor | Rol en el sistema | Qué necesita |
|---|---|---|
| Administrador de la agencia | `agencia` | Registrar clientes, planes y equipo; ver carga, SLA, costos y rentabilidad |
| Técnico de la agencia | `agencia` | Atender tickets, aprobar cambios, responder incidentes y hacer rollback |
| Cliente PyME | `cliente` | Crear solicitudes, ver el estado de su sitio y entender los incidentes sin jerga técnica |
| Sistema de monitoreo | (máquina) | Avisar fallas al Hub de forma automática |
| Asistente de IA local | (máquina) | Redactar resúmenes que un humano revisa |

## Cómo se levantan (lo lidera el ingeniero industrial)

- **Entrevistas:** 2 o 3 agencias pequeñas o freelancers web de Popayán, 30 min cada una. Cómo reciben solicitudes, cómo se enteran de las caídas, cómo cobran.
- **Personas:** una ficha por actor (nombre ficticio, objetivos, frustraciones).
- **Benchmark:** qué hacen las herramientas de mesa de ayuda y de monitoreo, y qué no hacen para agencias.
- **Historias de usuario** con criterios de aceptación medibles. Ejemplo:
  - *Como técnico, quiero que una caída abra un incidente sola, para no depender de que el cliente llame.*
  - *Criterio: si el sitio responde 500 durante 1 minuto, se crea un incidente P1 con hora de inicio y se notifica al responsable.*

Los entregables de este levantamiento son tareas de la [spec 000](../specs/000-modelo-de-servicio/tasks.md).

## Requerimientos funcionales

| ID | Requerimiento | Prioridad | Módulo | Spec |
|---|---|---|---|---|
| RF-01 | Registrar agencia, usuarios y roles | M | 1 (roles en 3) | 001, 007 |
| RF-02 | Gestionar clientes, proyectos, servicios y planes | M | 1 | 001 |
| RF-03 | Desplegar la app de cada cliente en su propio namespace | M | 2 | 003 |
| RF-04 | Crear, asignar y cambiar estado de tickets | M | 2 | 004 |
| RF-05 | Clasificar tickets e incidentes P1–P4 según la matriz | M | 2 | 000, 004 |
| RF-06 | Aprobar una solicitud de cambio y desplegarla por GitOps | M | 2 | 005 |
| RF-07 | Ver la versión que corre en cada cliente | S | 2 | 005 |
| RF-08 | Validar cada cambio con pruebas y escaneos de seguridad | M | 3 | 006 |
| RF-09 | Bloquear cambios que no pasan la validación y mostrar el motivo | M | 3 | 006 |
| RF-10 | Registrar auditoría de acciones | S | 3 | 007 |
| RF-11 | Monitorear disponibilidad de cada sitio | M | 4 | 008 |
| RF-12 | Abrir incidente automático desde una alerta | M | 4 | 008 |
| RF-13 | Medir SLA de respuesta y solución con hora real | M | 4 | 008 |
| RF-14 | Hacer rollback a la última versión estable | M | 4 | 009 |
| RF-15 | Dashboard técnico de la agencia | M | 4 | 010 |
| RF-16 | Portal simplificado del cliente | M | 4 | 010 |
| RF-17 | Calcular MTTR, carga por técnico y costo por cliente | S | 4 | 010 |
| RF-18 | Resumir incidentes con IA local y aprobación humana | M | 5 | 012 |
| RF-19 | Traducir el incidente a lenguaje del cliente | M | 5 | 012 |
| RF-20 | Generar reporte operativo y reporte ejecutivo | M | 5 | 013 |
| RF-21 | Generar infografía mensual por cliente | M | 6 | 014 |
| RF-22 | Catálogo mínimo de clientes y servicios en Backstage | S | 2 | 005 |
| RF-23 | Sugerir la causa del incidente con un modelo de código | C | 6 | 014 |
| RF-24 | Facturación, pagos y dominios reales | W | — | — |

## Requerimientos no funcionales

| ID | Requerimiento | Módulo | Spec |
|---|---|---|---|
| RNF-01 | Todo corre en infraestructura propia, sin servicios externos para la demo | 1 | 002 (y todas) |
| RNF-02 | Cada componente se ejecuta en contenedores | 1 | 002 |
| RNF-03 | Aislamiento entre clientes (namespaces y roles) | 2 | 003 |
| RNF-04 | Toda la configuración de despliegue vive en Git | 2 | 005 |
| RNF-05 | Solo se despliegan imágenes escaneadas, firmadas y verificadas en el pipeline; ningún contenedor de cliente corre como root | 3 | 006 |
| RNF-06 | Contraseñas y secretos nunca en el código | 3 | 006 |
| RNF-07 | Una falla se detecta en 1 minuto o menos | 4 | 008 |
| RNF-08 | La infraestructura se recrea desde código | 4 | 011 |
| RNF-09 | Ningún dato de clientes sale a una IA externa | 5 | 012 |
| RNF-10 | El portal del cliente se entiende sin conocimientos técnicos | 4 | 010 |
| RNF-11 | La demo arranca siempre desde datos semilla conocidos | 7 | 015 |

## Matriz de trazabilidad: demo final → requerimientos → specs

| Punto de la demo final | Requerimientos | Módulo | Specs | Insumo industrial (spec 000) |
|---|---|---|---|---|
| 1. Agencia y 3 clientes registrados | RF-01, RF-02 | 1 | 001 | Definición de planes |
| 2. Apps en contenedores y Kubernetes | RF-03, RNF-02, RNF-03 | 1–2 | 002, 003 | Cuotas por plan |
| 3. Validación con seguridad antes de publicar | RF-08, RF-09, RNF-05 | 3 | 006 | Proceso de gestión de cambios |
| 4. Dashboard técnico y portal del cliente | RF-15, RF-16 | 4 | 010 | KPI que se muestran |
| 5. Falla detectada e incidente abierto | RF-11, RF-12, RNF-07 | 4 | 008 | — |
| 6. Prioridad, responsable y SLA medido | RF-05, RF-13 | 2–4 | 004, 008 | Matriz P1–P4 y tiempos SLA |
| 7. Rollback | RF-14, RF-06 | 2–4 | 005, 009 | — |
| 8. Reporte operativo y ejecutivo | RF-17, RF-20 | 4–5 | 010, 013 | Formato del reporte, costos y MTTR |
| 9. Asistente IA con verificación humana | RF-18, RF-19, RNF-09 | 5 | 012 | — |
| 10. Infografía operativa | RF-21 | 6 | 014 | Contenido de la infografía |

## Decisiones pendientes

| Decisión | Quién decide | Spec afectada | Fecha límite |
|---|---|---|---|
| OpenTofu o Terraform | Profesor | 011 | Inicio del módulo 4 (24 oct) |
| Qwen2.5 7B o Llama 3.1 8B | Prueba en PC B | 012 | Inicio del módulo 5 (3 nov) |
| SD 1.5 o SDXL Turbo | Prueba en PC B | 014 | Inicio del módulo 6 (13 nov) |
| Tiempos SLA por plan y matriz P1–P4 definitiva | Industrial + equipo | 000 | 2 oct |
| Qué se presenta en la sustentación del 3 nov | Equipo | 015 | 27 oct |

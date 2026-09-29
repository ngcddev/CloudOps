# CloudOps Client Hub

> Un centro de operación de servicios digitales para agencias que administran múltiples clientes.

CloudOps Client Hub **no es otro Vercel**. Ayuda a una agencia digital a gestionar el servicio completo que presta a sus clientes: solicitudes, cambios, despliegues, monitoreo, incidentes, recuperación, calidad y reportes.

## Tabla de contenidos

- [El problema](#el-problema)
- [Diferencia frente a Vercel](#diferencia-frente-a-vercel)
- [Flujo de operación](#flujo-de-operación)
- [Diferenciales](#diferenciales)
- [Ejemplo: falla en el sitio de un restaurante](#ejemplo-falla-en-el-sitio-de-un-restaurante)
- [Aporte del ingeniero industrial](#aporte-del-ingeniero-industrial)
- [Alcance de la demo](#alcance-de-la-demo)
- [Arquitectura del laboratorio](#arquitectura-del-laboratorio)
- [Equipo y roles](#equipo-y-roles)

## El problema

Publicar una página ya está resuelto por plataformas como Vercel. Lo que sigue sin resolverse, sobre todo para agencias pequeñas, es lo que pasa **después** de publicar:

- ¿Qué cliente pidió un cambio y cuándo se atiende?
- ¿Qué pasa si la página cae?
- ¿Cuánto tardó la solución y se cumplió lo prometido?
- ¿Qué se le informa al cliente?
- ¿Cuánto soporte consume cada cuenta?

CloudOps Client Hub organiza esas respuestas en un mismo sistema.

## Diferencia frente a Vercel

| Tema | Vercel | CloudOps Client Hub |
|---|---|---|
| Usuario principal | Desarrollador o equipo de producto | Agencia digital, soporte y cliente PyME |
| Problema central | Publicar y operar aplicaciones web | Gestionar el servicio de varios clientes |
| Inicio del flujo | Repositorio de código | Cliente, proyecto, servicio y acuerdo de atención |
| Monitoreo | Métricas y errores de la aplicación | Métricas conectadas con incidentes, SLA y reportes |
| Rollback | Volver a una versión anterior | Volver a versión estable y registrar incidente, causa y tiempo de recuperación |
| Tickets y solicitudes de cambio | No es su foco principal | Parte central del producto |
| Portal para cliente no técnico | No es su foco principal | Diseñado específicamente para esto |
| SLA y prioridades | No es la propuesta central | Se definen, miden y reportan por cliente o plan |
| Rentabilidad y capacidad | No es su foco | Indicadores de carga, costos y horas de soporte |
| IA local privada | No es su enfoque | Asistente local para apoyo operativo supervisado |
| Alcance | Plataforma global de despliegue | Producto acotado para agencias y PyMEs |

> Vercel responde: *"Tengo código, ¿cómo lo publico rápido?"*
> CloudOps Client Hub responde: *"Tengo varios clientes, ¿cómo organizo su soporte, detecto problemas, cumplo tiempos y explico el valor del servicio?"*

## Flujo de operación

El despliegue es una pieza necesaria, no el producto completo. Cada sitio o aplicación se trata como un **servicio** con cliente, responsables, prioridad, historial, versiones, alertas, incidentes y reportes.

```
Cliente solicita un cambio o el sistema detecta una falla
  → Se clasifica el caso y se asigna prioridad
  → El equipo realiza el cambio o corrección
  → Se valida antes de publicar
  → Se despliega de forma controlada
  → Se monitorea el resultado
  → Si algo falla, se recupera una versión estable
  → Se registra el incidente y se informa al cliente
  → Se mide el servicio y se mejora el proceso
```

## Diferenciales

1. **El servicio empieza en el cliente, no en el código.** Una página es un servicio con cliente, plan de atención, responsable y condiciones de calidad: historial de solicitudes, cambios e incidentes, criticidad, SLA, versiones recuperables, evidencias de seguridad y reportes periódicos.
2. **Traduce lo técnico a lenguaje de negocio.**

   | Dato técnico | Cómo lo ve el cliente |
   |---|---|
   | 99,2 % de disponibilidad | "Su sitio se mantuvo disponible dentro del objetivo acordado." |
   | Error HTTP 500 | "Se detectó una falla temporal y se activó el proceso de recuperación." |
   | Rollback de un despliegue | "Se restauró una versión estable para mantener la continuidad." |
   | Latencia elevada | "El sitio presentó lentitud y se inició una acción de mejora." |
   | Vulnerabilidad en una dependencia | "Una actualización fue detenida antes de publicarse por controles de seguridad." |

3. **Convierte el mantenimiento web en un servicio medible:** disponibilidad, cambios realizados, incidentes atendidos, tiempos de respuesta y recuperación, seguridad y mejoras.
4. **Puede operar con infraestructura propia:** contenedores, Kubernetes, GitOps, observabilidad y modelo local, sin depender de un proveedor comercial para la demo.

## Ejemplo: falla en el sitio de un restaurante

| Paso | Qué hace CloudOps Client Hub |
|---|---|
| 1. Detección | El monitoreo identifica que el sitio no responde. |
| 2. Incidente | Se crea un incidente asociado al cliente "Restaurante". |
| 3. Prioridad | Se clasifica como **P1** (puede afectar reservas o pedidos). |
| 4. SLA | Inicia la medición: respuesta en 15 min, solución objetivo en 4 h. |
| 5. Diagnóstico | El responsable revisa alertas, logs y cambios recientes. |
| 6. Recuperación | Rollback a una versión estable desde GitOps. |
| 7. Verificación | Las métricas confirman la recuperación. |
| 8. Comunicación | El cliente recibe una explicación sencilla de lo ocurrido. |
| 9. Mejora | El caso queda en el reporte y se evalúa ajustar el proceso o automatizar una prueba. |

## Aporte del ingeniero industrial

Los ingenieros de sistemas construyen la plataforma que publica, monitorea y recupera; el ingeniero industrial diseña **cómo se presta el servicio y cómo se mide** si se hace bien.

| Área | Aporte | Resultado en el producto |
|---|---|---|
| Proceso | Modela el paso a paso de solicitud a cierre | Flujo de tickets, estados, responsables y aprobaciones |
| Priorización | Define P1–P4 según impacto y urgencia | Reglas de clasificación y escalamiento |
| SLA | Define tiempos objetivo de respuesta y solución | Medición automática de cumplimiento |
| Indicadores | Diseña KPI técnicos, operativos y de negocio | Dashboards de SLA, MTTR, tickets, carga y calidad |
| Capacidad | Estima cuántos clientes y tickets puede atender el equipo | Alertas de sobrecapacidad |
| Costos | Analiza horas de soporte y costo por cliente o plan | Información para rentabilidad y planes |
| Mejora continua | Identifica reprocesos, fallas recurrentes y cuellos de botella | Acciones correctivas y automatización |
| Experiencia del cliente | Define qué debe entender el cliente | Reportes claros y portal no técnico |

## Alcance de la demo

- [ ] Registrar una agencia y tres clientes ficticios
- [ ] Crear un proyecto o servicio por cliente
- [ ] Desplegar aplicaciones demo con contenedores y Kubernetes
- [ ] Ejecutar validación automática antes de publicar
- [ ] Dashboard técnico para la agencia y uno simplificado para el cliente
- [ ] Simular una falla controlada
- [ ] Detectarla por monitoreo y abrir un incidente
- [ ] Clasificar prioridad, asignar responsable y medir SLA
- [ ] Recuperar el servicio mediante rollback
- [ ] Generar un reporte operativo y ejecutivo
- [ ] Usar un asistente local para resumir el incidente, con verificación humana
- [ ] Generar una infografía operativa como componente visual o multimodal

## Arquitectura del laboratorio

Contenedores · Kubernetes · GitOps · Pipelines con validaciones de seguridad · Observabilidad (métricas, logs, alertas) · Modelo de IA local

## Equipo y roles

| Integrante | Rol | Aporta |
|---|---|---|
| Sistemas 1 | Cloud / Platform | Kubernetes, GitOps, manifiestos, infraestructura y despliegue |
| Sistemas 2 | Backend | API, usuarios, roles, clientes, tickets, SLA y base de datos |
| Sistemas 3 | DevSecOps / SRE | Pipelines, seguridad, observabilidad, alertas, logs y recuperación |
| Sistemas 4 | Frontend / Producto | Portal de cliente, consola de agencia, UX y dashboards |
| Industrial | Operación de servicios | Procesos, prioridades, SLA, KPI, capacidad, costos y mejora continua |

## Conclusión

La propuesta no compite con Vercel en despliegue global. Usa capacidades cloud-native (contenedores, Kubernetes, GitOps, seguridad, observabilidad y recuperación) para profesionalizar la operación y la relación de servicio entre agencias digitales y PyMEs: una página web deja de ser una entrega puntual y se convierte en un servicio administrado, medible y mejorable.

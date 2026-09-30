# Principios

> Ninguna spec, plan ni PR puede romperlos. Si un plan rompe un principio, **se corrige el plan, no el principio**.

## Los 10 principios

1. **El flujo empieza en el cliente.** cliente → proyecto → servicio → acuerdo (plan + SLA). El despliegue es una capacidad interna, no el producto.
2. **Infraestructura propia.** La demo no depende de servicios de terceros, y ningún dato de clientes sale del laboratorio.
3. **Git es la única puerta.** Todo cambio entra por Gitea → Gitea Actions → Argo CD. Nadie despliega a mano.
4. **Seguridad antes de publicar.** Ninguna imagen se despliega sin escanear, firmar y verificar; ningún contenedor de cliente corre como root.
5. **El Hub no toca Kubernetes directamente.** Habla solo con Gitea, Argo CD y Prometheus.
6. **La IA propone, el humano decide.** Todo texto de IA es un borrador que alguien aprueba. El flujo completo funciona aunque la IA esté apagada.
7. **Medición real.** SLA, MTTR y disponibilidad se calculan con horas y métricas reales, nunca simuladas.
8. **El cliente no ve jerga técnica.** Todo lo que llega al portal del cliente está en lenguaje de negocio (ver [glosario](../docs/glosario.md)).
9. **Módulo a módulo.** Una herramienta de plataforma entra solo cuando el diplomado ya la cubrió. El carril de producto (backend, frontend, base de datos, procesos) sí puede adelantarse.
10. **Simple y verificable.** Diseño en blanco y negro, dos roles (agencia y cliente) y cada spec cierra con una demo reproducible desde datos semilla.

## Reglas derivadas

- **Regla de desacople:** el producto nunca depende de la plataforma para funcionar. Ejemplo: el backend registra incidentes manuales desde la semana 1; en el módulo 4 empiezan a llegar solos desde Alertmanager.
- **Regla de oro:** cada módulo termina con una demo de 3 a 5 minutos que conecta lo nuevo del módulo con el producto. Si la conexión no se ve en pantalla, el incremento no cuenta.
- **Regla de orden:** una spec se implementa cuando las specs de las que depende cumplen sus criterios de aceptación (o exponen ya el contrato que se necesita).
- **Regla de la tarea:** se trabaja una tarea de `tasks.md` a la vez; una tarea no se marca como hecha sin verificar su criterio.

## Revisión contra los principios

Antes de aprobar un plan o un PR, se comprueba:

- ¿El flujo sigue empezando en el cliente (principio 1)?
- ¿Algún dato de clientes sale del laboratorio o se envía a un servicio de IA externo (principio 2)?
- ¿Algo se despliega a mano o el Hub toca Kubernetes directamente (principios 3 y 5)?
- ¿Alguna imagen se publica sin escanear, firmar y verificar, o corre como root (principio 4)?
- ¿Un texto de IA llega a alguien sin aprobación humana, o el flujo falla con la IA apagada (principio 6)?
- ¿Un SLA, MTTR o disponibilidad está simulado (principio 7)?
- ¿Algún texto técnico llega al portal del cliente (principio 8)?
- ¿Se usa una herramienta de plataforma de un módulo que aún no se ha visto (principio 9)?
- ¿La demo arranca desde datos semilla y respeta el blanco y negro (principio 10)?

## Prohibido

- Secretos en el código o en el repo (se usan `.env` y `.env.example`).
- Desplegar a mano o hacer que el Hub hable con Kubernetes: solo Gitea, Argo CD y Prometheus.
- Contenedores que corren como root.
- Enviar datos de clientes a servicios de IA externos.
- Marcar una tarea como hecha sin verificar su criterio.

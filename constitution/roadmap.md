# Roadmap: calendario, specs y riesgos

> 120 horas en 9 semanas, del **28 sep** al **30 nov 2026**.
> Hitos: **sustentación del módulo 4 (3 nov)** y **sustentación final (30 nov)**.
> Entre el módulo 6 (20 nov) y el integrador (24 nov) quedan 3 días de colchón.
> Cada spec citada aquí vive en [specs/](../specs/README.md).

## Tres carriles en paralelo

| Carril | Qué incluye | Ritmo |
|---|---|---|
| **Plataforma** | Contenedores, Kubernetes, GitOps, seguridad, observabilidad, IaC, IA | Atado al módulo: solo lo que el diplomado ya enseñó |
| **Producto** | Backend, frontend, base de datos | Continuo: puede adelantarse y prepara dónde conectarse cada módulo |
| **Servicio (industrial)** | Procesos, prioridades, SLA, KPI, costos | Se diseña antes de que el código lo necesite |

## Módulos, incrementos y specs

| Módulo | Fechas | Incremento obligatorio | Specs | Demo de cierre |
|---|---|---|---|---|
| 1 · Cloud Native, Linux, Git, contenedores | 28 sep – 1 oct | Todo corre en contenedores con un solo comando | 000, 001, 002 | `docker compose up`, se registran los 3 clientes y se abren las 3 apps |
| 2 · Kubernetes, GitOps, Platform Engineering | 2 – 13 oct | Un cambio en Git despliega la app del cliente sin tocar el clúster; un revert la devuelve | 003, 004, 005 | Se aprueba un cambio en el Hub, Argo CD lo sincroniza y el sitio muestra la nueva versión |
| 3 · DevSecOps | 16 – 24 oct | Un cambio inseguro no llega a producción y el Hub muestra por qué | 006, 007 | Un commit con contraseña lo bloquea Gitleaks y el Hub marca "rechazado por seguridad" |
| 4 · IaC, observabilidad, SRE | 24 oct – 3 nov | El caso del restaurante de punta a punta, sin IA | 008, 009, 010, 011 | v2 rota → alerta → P1 → rollback → métrica verde → MTTR |
| 5 · MLOps, LLMOps, IA local | 3 – 12 nov | El Hub redacta el resumen con IA local y un humano lo aprueba | 012, 013 | Del incidente sale el mensaje al cliente, revisado y aprobado |
| 6 · IA multimodal | 13 – 20 nov | Infografía mensual de cada cliente | 014 | Se genera la infografía del restaurante en menos de 2 min |
| 7 · Integrador | 24 – 30 nov | Demo final ensayada; ninguna funcionalidad nueva | 015 | Los 10 puntos en menos de 15 min |

## Orden de arranque y dependencias

```
000 ─┬─> 001 ─┬─> 004 ─┬─> 005 ──> 006
     │        │        │     └────────> 009 ──> 010 ──> 013 ──> 014
     │        └─> 007  └─> 008 ──┘       ↑        ↑
002 ──> 003 ──┬─> 005             008 ───┘        │
              ├─> 008 ──> 012                     │
              └─> 011                   010 ──────┘
Todas ──> 015
```

- **Terminadas:** 001, 002 (la 000 sigue con tareas abiertas del industrial).
- **Ahora (módulo 2):** 003, 004, 005.
- **Pueden adelantarse (solo producto):** 004 y la parte de backend/frontend de 007, 008 (incidentes manuales), 010 y 013.
- **Esperan su módulo:** todo lo que instala herramientas de plataforma (003, 005, 006, 008-monitoreo, 009, 011, 012, 014).

## Hitos con fecha

| Fecha | Hito |
|---|---|
| 1 oct | Cierre módulo 1 (terminar el fin de semana 3–4 oct si hace falta) |
| 2 oct | Requerimientos y matriz P1–P4 cerrados (spec 000) |
| 13 oct | Cierre módulo 2: GitOps funcionando |
| 24 oct | Cierre módulo 3: puerta de seguridad |
| 31 oct | Caso del restaurante sin IA listo (1–2 nov solo se ensaya) |
| **3 nov** | **Sustentación módulo 4** |
| 12 nov | Cierre módulo 5: asistente IA y reportes |
| 20 nov | Cierre módulo 6: infografía |
| 21–23 nov | Colchón para correcciones |
| 24–29 nov | Integración, ensayos, video de respaldo |
| **30 nov** | **Sustentación final** |

## Hardware

Qué corre en cada equipo: [tech-stack.md](tech-stack.md#distribución-del-hardware).

## Riesgos

| Riesgo | Efecto | Respuesta |
|---|---|---|
| El módulo 1 termina el 1 oct y el equipo apenas arranca | Incremento 1 tarde | Terminarlo el fin de semana 3–4 oct, en paralelo con el módulo 2 |
| Sustentación del 3 nov al cierre del módulo 4 | Llegar sin flujo completo | Caso del restaurante sin IA listo el 31 oct |
| El Hub se construye desconectado de la infraestructura | Pantallas que no reflejan nada | Desde el módulo 2, cada pantalla nueva se conecta a Gitea, Argo CD o Prometheus antes de pulirse |
| PC A justo de RAM | Pods reiniciándose en la demo | Límites de memoria, retención corta en Prometheus/Loki, runner de Gitea Actions fuera del PC A |
| Backstage consume varios GB | Deja sin memoria al PC A | Catálogo mínimo; apagarlo si falta RAM (la consola del Hub cumple el rol) |
| Solo 6 GB de VRAM | LLM y ComfyUI no caben a la vez | Por turnos (Ollama con `keep_alive` corto) y resúmenes aprobados en los datos semilla |
| Los dos PC deben verse en la red | La IA no responde en la sustentación | IP fija para cada PC y prueba en la red del salón antes del 30 nov |
| La firma se verifica en el pipeline, no en el clúster | Un despliegue manual podría saltarla | Nadie despliega a mano (principio 3); verificación en clúster como mejora futura |
| La frontera de "no avanzar más de lo visto" | El profesor objeta avances | Adelantar solo el carril de producto; confirmar la regla con el docente |

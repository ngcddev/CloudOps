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
| 6 · IA multimodal | 13 – 20 nov | El asistente recibe voz y responde con voz | 021 | Se pregunta hablando, se corrige lo entendido y se escucha la respuesta (spec 014, la infografía, queda como mejora) |
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

- El estado de cada spec (terminada, en curso, pospuesta) está en un solo lugar: el [mapa de specs](../specs/README.md).
- Las specs 016 a 023 se agregaron después del plan inicial: alta de sitio y demo del colegio (016), cierres de los módulos 2 a 5 (017 a 020), voz del asistente (021, reemplaza a la infografía 014), sincronía GitOps (022) y entrega final (023).

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
| 20 nov | Cierre módulo 6: voz del asistente (la infografía quedó pospuesta) |
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
| Un solo equipo corre clúster e IA | Pods reiniciándose en la demo | Límites de memoria y retención corta en Prometheus, Loki y Tempo |
| Backstage consume varios GB | Deja sin memoria al equipo | Catálogo mínimo; apagarlo si falta RAM (la consola del Hub cumple el rol) |
| La GPU de 8 GB la comparten el LLM y los embeddings | La IA tarda o no responde | Modelo de 7B cuantizado; si la IA no responde, el Hub degrada con un aviso (probado) |
| La firma se verifica en el pipeline, no en el clúster | Un despliegue manual podría saltarla | Nadie despliega a mano (principio 3); verificación en clúster como mejora futura |
| La frontera de "no avanzar más de lo visto" | El profesor objeta avances | Adelantar solo el carril de producto; confirmar la regla con el docente |

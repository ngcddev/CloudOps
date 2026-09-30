# Tech Stack — CloudOps Client Hub (Proyecto integrador CloudForge AI)

> Diplomado CloudForge AI 5.0 — Unicomfacauca
> Equipo de 5 (4 Ing. Sistemas + 1 Ing. Industrial)
> Última actualización: 30 sep 2026

## Contexto del proyecto

CloudOps Client Hub es un centro de operación de servicios digitales para agencias web que atienden
varias PyMEs: gestiona solicitudes, cambios, despliegues, monitoreo, incidentes, recuperación, SLA,
calidad y reportes de cada cliente. No es una plataforma de despliegue tipo Vercel — el despliegue es
una capacidad técnica dentro del flujo, no el producto.

**Hardware disponible:** dos PC con 16 GB de RAM y al menos 6 GB de VRAM; el resto de equipos del
grupo son menos potentes y se usan para desarrollo. El stack se ajusta a ese hardware: modelos de IA
de 7–8B en lugar de 14B, y la carga repartida entre dos máquinas (ver "Distribución del hardware").

**Regla del diplomado:** el proyecto avanza módulo a módulo; cada herramienta de plataforma se
implementa cuando el módulo correspondiente ya la cubrió.

## Stack por módulo

Una herramienta de plataforma entra solo cuando el diplomado ya la cubrió ([principio 9](principles.md)).

| Módulo | Fechas | Herramientas que entran |
|---|---|---|
| 1 · Cloud Native, Linux, Git, contenedores | 28 sep – 1 oct | Linux, Git, Docker, docker compose, Nginx, FastAPI + PostgreSQL, React + Vite |
| 2 · Kubernetes, GitOps, Platform Engineering | 2 – 13 oct | k3s (Traefik), Gitea (Git + registro), Argo CD, Backstage |
| 3 · DevSecOps y cadena de suministro | 16 – 24 oct | Gitea Actions, Gitleaks, Trivy, Syft, Cosign, Pod Security Admission |
| 4 · IaC, observabilidad, SRE | 24 oct – 3 nov | OpenTofu/Terraform, Ansible (opcional), Prometheus, Grafana, Alertmanager, Loki, Blackbox Exporter, OpenTelemetry |
| 5 · MLOps, LLMOps, IA local | 3 – 12 nov | Ollama (Qwen2.5 7B o Llama 3.1 8B Q4; respaldo Qwen2.5 3B), AnythingLLM + nomic-embed-text, MLflow |
| 6 · IA local multimodal | 13 – 20 nov | Stability Matrix + ComfyUI (SD 1.5; SDXL Turbo solo si cabe en 6 GB) |
| 7 · Integrador | 24 – 30 nov | Sin herramientas nuevas: integración, ensayo y documentación |

## Stack de producto (fijo desde el módulo 1)

| Capa | Tecnología | Notas |
|---|---|---|
| Backend | Python 3.12 + FastAPI | SQLAlchemy 2, Alembic (migraciones), Pydantic, pytest |
| Base de datos | PostgreSQL 16 | Fechas en UTC (`timestamptz`) |
| Frontend | React + Vite + TypeScript | react-router-dom; CSS propio en blanco y negro, sin librerías de UI |
| Contenedores | Docker, docker compose (desarrollo) | Imágenes multi-stage, usuario no root |
| Dependencias | `pip` + `requirements.txt` / `npm` | |

## Stack de plataforma

| Capa | Herramienta | Notas |
|---|---|---|
| Kubernetes | **k3s** | Nodo único en el PC A, liviano, trae Ingress (Traefik) |
| IaC | **OpenTofu** (compatible con Terraform) | Código HCL genérico; el binario final (`tofu` o `terraform`) se decide al confirmar el profesor |
| Bootstrap de SO (opcional) | Ansible | Solo para instalar k3s en el nodo, no reemplaza IaC |
| Git + CI + registro | **Gitea + Gitea Actions** | Autoalojado, incluye registro de imágenes |
| GitOps | **Argo CD** | Fuente de verdad = repo Git; detecta drift; hace rollback |
| Platform Engineering | **Backstage** | Catálogo mínimo de servicios/clientes; se apaga si falta RAM en el PC A |
| Seguridad (DevSecOps) | **Trivy** (vulnerabilidades), **Gitleaks** (secretos), **Syft** (SBOM), **Cosign/Sigstore** (firma y verificación), **Pod Security Admission** (nativo de Kubernetes) | Cadena de suministro de software sin instalar motores de políticas extra (ver "Políticas de seguridad") |
| Observabilidad | **Prometheus + Grafana + Alertmanager**, **Loki** (logs), **Blackbox Exporter** (uptime), **OpenTelemetry** (instrumentación) | Alertmanager dispara el webhook que abre el incidente |
| Backend (Hub) | **FastAPI + PostgreSQL** | API, usuarios, roles, clientes, tickets, SLA |
| Frontend (Hub) | **React + Vite** | Consola de agencia + portal de cliente, mismas rutas con roles distintos |
| MLOps | **MLflow** (Docker Compose) | Registro de versiones de prompt/modelo y sus evaluaciones; corre en el PC B |
| LLM local | **Ollama** | Modelo: Qwen2.5 7B-Instruct o Llama 3.1 8B (Q4, ~5 GB de VRAM); respaldo Qwen2.5 3B |
| RAG | **AnythingLLM** | Embeddings vía `nomic-embed-text` servido también desde Ollama |
| Multimodal obligatorio | **Stability Matrix + ComfyUI** | Modelo: SD 1.5; SDXL Turbo solo si corre bien en 6 GB — genera la ilustración de la infografía operativa |

## Distribución del hardware

| Equipo | Qué corre | Por qué |
|---|---|---|
| PC A (16 GB) · plataforma | k3s con el Hub, PostgreSQL, Gitea, Argo CD, Prometheus, Grafana, Loki, Alertmanager y los sitios de clientes | Todo lo que debe estar arriba siempre vive en un solo nodo; la GPU no se usa |
| PC B (16 GB, GPU ≥ 6 GB) · IA | Ollama, AnythingLLM, MLflow y ComfyUI | 6 GB de VRAM no alcanzan para el LLM y la generación de imágenes a la vez: se usan por turnos (Ollama con `keep_alive` corto) |
| Equipos menos potentes | Desarrollo local con `docker compose` y runner de Gitea Actions (si tiene RAM suficiente) | Mantienen las compilaciones fuera del PC A |

El Hub (en el PC A) llama a Ollama y AnythingLLM (en el PC B) por la red local. Ambos PC necesitan IP
fija en la red donde se haga la demo.

## Políticas de seguridad (sin herramientas extra)

Se descartó Kyverno: el diplomado no lo incluye explícitamente y es la pieza más costosa del módulo 3.
Lo mismo se cubre así:

1. **Verificación de firma en el pipeline.** Antes de actualizar el tag en el repo GitOps, Gitea
   Actions ejecuta `cosign verify` sobre la imagen. Sin firma válida, el pipeline falla y no hay
   despliegue.
2. **Pod Security Admission** (incluido en Kubernetes) en modo `restricted` en cada namespace de
   cliente, con etiquetas del namespace:
   ```yaml
   metadata:
     labels:
       pod-security.kubernetes.io/enforce: restricted
   ```
   Bloquea contenedores que corren como root, con privilegios o con capacidades peligrosas.
3. **ResourceQuota y LimitRange** por namespace para garantizar límites de CPU/RAM según el plan.
4. **Nadie despliega a mano:** todo cambio entra por Gitea y Argo CD, así la verificación del
   pipeline no se puede saltar en la operación normal.

Limitación conocida: la firma se verifica en el pipeline, no dentro del clúster. Se documenta como
mejora futura (admission controller de verificación de imágenes).

## Sitios de cliente (lo que se despliega)

Dos plantillas estándar de servicio (no se acepta "cualquier repositorio", como haría Vercel):

### Plantilla 1 — Landing estática
```
cliente-landing/
├── src/              → HTML/CSS/JS o Astro
├── Dockerfile        → build multi-stage → Nginx sirviendo /dist (usuario no root)
├── deploy/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── ingress.yaml
```

### Plantilla 2 — Landing + formulario
```
cliente-landing-form/
├── frontend/          → landing estática (Nginx)
├── backend/           → API mínima que recibe el formulario (FastAPI o Node/Express)
├── Dockerfile.frontend
├── Dockerfile.backend
├── deploy/
│   ├── frontend-deployment.yaml
│   ├── backend-deployment.yaml
│   ├── services.yaml
│   └── ingress.yaml    → / al frontend, /api al backend
```

Cliente nuevo = copiar una plantilla, cambiar nombre/dominio/plan. Las imágenes deben correr como
usuario no root para cumplir Pod Security Admission `restricted` (por ejemplo, `nginxinc/nginx-unprivileged`).

## Estructura de Kubernetes

```
Clúster k3s (PC A)
├── namespace: hub                  → el Hub (FastAPI, React, PostgreSQL)
├── namespace: argocd               → Argo CD
├── namespace: monitoring           → Prometheus, Grafana, Alertmanager, Loki
├── namespace: cliente-restaurante  → sitio del restaurante
├── namespace: cliente-ferreteria   → sitio de la ferretería
└── namespace: cliente-consultorio  → sitio del consultorio
```

Cada namespace de cliente incluye:
- **ResourceQuota + LimitRange** — límite de CPU/RAM según el plan (conecta con el trabajo del rol Industrial)
- **NetworkPolicy** — aislamiento entre clientes
- **Pod Security Admission `restricted`** — sin root ni privilegios
- **Ingress** — `restaurante.hub.local`, etc.

El Hub no habla directamente con Kubernetes: se comunica con Gitea (cambios), Argo CD (estado del
despliegue) y Prometheus (métricas). Alertmanager avisa al Hub por webhook cuando algo falla.

## Flujo de despliegue

1. Push a Gitea → dispara Gitea Actions.
2. Pipeline: build de imagen → Trivy (vulnerabilidades) → Gitleaks (secretos) → Syft (SBOM) →
   Cosign (firma) → push al registro → `cosign verify` → actualiza el tag en el repo GitOps.
3. Argo CD detecta el cambio y sincroniza el `Deployment` en el namespace del cliente;
   Pod Security Admission rechaza cualquier Pod que no cumpla el perfil `restricted`.
4. Readiness probe actúa como smoke test antes de recibir tráfico real.
5. Blackbox Exporter monitorea el endpoint público de cada sitio.
6. Si falla → Alertmanager dispara webhook → Hub abre incidente P1 → arranca SLA (15 min
   respuesta / 4 h solución).
7. Revisión de logs (Loki) y cambios recientes → rollback vía `git revert` en el repo GitOps.
8. Argo CD reconcilia a la versión estable → métricas confirman recuperación → Hub cierra el
   incidente y calcula MTTR.
9. Ollama (vía AnythingLLM/RAG, en el PC B) redacta el resumen del incidente y el mensaje al
   cliente — siempre con aprobación humana antes de enviarse.

## Qué audita el sistema por cliente

| Qué se audita | Fuente |
|---|---|
| ¿El sitio está arriba? | Blackbox Exporter → Prometheus |
| Latencia de respuesta | Métricas del Ingress (Traefik) |
| Errores 4xx/5xx | Logs de Nginx vía Loki |
| Formularios recibidos / fallidos | Métrica custom del backend, expuesta con OpenTelemetry |
| Seguridad de la imagen desplegada | Reporte de Trivy y resultado de `cosign verify`, guardados como evidencia |
| Versión activa y quién la desplegó | Historial de Argo CD + commits de Git |

## Pendientes / decisiones abiertas

- [ ] Confirmar con el profesor si el IaC debe entregarse específicamente en Terraform u OpenTofu
      (el código HCL es compatible con ambos, solo cambia el binario usado).
- [ ] Probar en el PC B qué rinde mejor: Qwen2.5 7B o Llama 3.1 8B, y SD 1.5 o SDXL Turbo
      (antes del módulo 5).
- [ ] Tiempos SLA por plan y matriz P1–P4 definitiva.
- [ ] Qué se presenta exactamente en la sustentación del 3 nov.

## Riesgos conocidos

- El PC A queda justo de RAM con todo el clúster: límites de memoria en cada componente, retención
  corta en Prometheus y Loki, y el runner de Gitea Actions fuera de ese equipo.
- 6 GB de VRAM: el LLM y ComfyUI se usan por turnos; los datos semilla incluyen resúmenes ya aprobados
  por si la IA falla en la demo.
- La demo depende de que los dos PC se vean en la red: IP fija y prueba en el salón antes del 30 nov.
- Construir el Hub antes de tener un despliegue GitOps de punta a punta funcionando suele dejarlo
  desconectado de la infraestructura real — desplegar primero, luego construir el Hub encima.
- No sobre-diseñar autenticación: dos roles (agencia y cliente) con usuarios sembrados en la base de
  datos bastan para la demo.

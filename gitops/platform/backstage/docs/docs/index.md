# Plataforma CloudOps Client Hub

Forja Digital opera los sitios web de sus clientes sobre un clúster Kubernetes (k3s). Un cliente pide un cambio, la agencia lo aprueba, el sitio se actualiza por GitOps y, si algo falla, el monitoreo abre el incidente y se vuelve a la versión estable.

## Mapa de herramientas

| Capa | Herramienta | Para qué |
|---|---|---|
| Consola | **Hub** (FastAPI, PostgreSQL, React) | Clientes, planes, tickets, cambios, incidentes, reportes y asistente de IA |
| Código y registro | **Gitea** | Repositorios, `hub-gitops` (la fuente de verdad del clúster) y registro de imágenes |
| Entrega | **Gitea Actions** + puerta de seguridad | Gitleaks, pruebas, Trivy, Syft, Cosign y procedencia SLSA |
| Despliegue | **Argo CD** | Sincroniza Git con el clúster y corrige el *drift* |
| Observabilidad | **Prometheus, Loki, Tempo, Grafana** | SLI/SLO, alertas, registros y trazas |
| IA local | **Ollama** + **MLflow** | Asistente con compuerta y RAG; experimentos y modelo registrado |
| Catálogo | **Backstage** | Servicios, plantillas y esta documentación |

## Principios

- **Git manda:** lo que está en `hub-gitops` es lo que corre. Un cambio a mano en el clúster lo revierte Argo CD.
- **El Hub solo escribe en Gitea.** Nunca habla con Kubernetes.
- **La IA propone, una persona aprueba.** Nada generado llega a un cliente sin revisión.

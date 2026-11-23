# Plan 024 · CloudOps Hub en GCP

> Cómo se construye [la spec](spec.md) con el stack de la [constitución](../../constitution/tech-stack.md). Solo usa herramientas de módulos ya vistos.

## Stack

| Pieza | Herramienta |
|---|---|
| Máquina | Compute Engine `e2-standard-2` (2 vCPU, 8 GB), Ubuntu 24.04 LTS, disco de 50 GB |
| Infraestructura como código | OpenTofu con el proveedor `hashicorp/google` (módulo nuevo `infra/tofu/gcp/`, estado separado del de clientes) |
| Clúster | k3s de un nodo (el mismo que el laboratorio) |
| GitOps | Argo CD + `hub-gitops` (Gitea) como hoy |
| HTTPS | Traefik de k3s + cert-manager con Let's Encrypt sobre `<ip>.sslip.io` |
| Túnel de la IA | Tailscale (recomendado): la VM y el PC de la IA en la misma red privada; `OLLAMA_URL=http://100.x.y.z:11434`. Alternativa: Cloudflare Tunnel con token |
| Respaldo | Los scripts existentes (`gitops/pruebas/respaldo.sh`, `respaldo-plataforma.sh`) hacia un bucket de Cloud Storage |
| Costos | Presupuesto de facturación con alertas; `infra/gcp/apagar.sh` y `encender.sh` |

## Modelo de datos

Sin cambios.

## API / manifiestos / pipelines

| Qué | Detalle |
|---|---|
| `infra/tofu/gcp/` | Red, subred, IP estática, regla de cortafuegos (80, 443; 22 solo desde la IP del equipo), VM con cuenta de servicio mínima, bucket de respaldo, presupuesto |
| Arranque de la VM | Script de inicio que instala k3s y deja listo el nodo; el resto lo trae Argo CD |
| `gitops/` | Overlay `nube` que cambia hosts a `*.sslip.io`, `OLLAMA_URL` y el `ClusterIssuer` de cert-manager; el laboratorio no cambia |
| Ollama | En el PC: escucha solo en la interfaz de Tailscale |

## Pantallas

Sin cambios.

## Contratos con otras specs

- Recibe de 011: patrón de OpenTofu y estado remoto.
- Recibe de 005 y 022: Argo CD y `hub-gitops` como única vía de despliegue.
- Recibe de 012 y 021: el asistente y la voz ya degradan sin Ollama.
- Entrega a 023: evidencias y un anexo del despliegue en la nube.

## Dónde va en el repo

| Qué | Ruta |
|---|---|
| Código de la nube | `infra/tofu/gcp/` |
| Scripts de encendido y apagado | `infra/gcp/` |
| Overlay de la nube | `gitops/overlays/nube/` |
| Pruebas | `infra/pruebas/gcp-*.sh` |
| Runbook | `runbooks/nube-gcp.md` |

## Riesgos

| Riesgo | Respuesta |
|---|---|
| El crédito de prueba se acaba o vence | Presupuesto con alertas; apagar entre fechas; el laboratorio local sigue siendo el plan de respaldo de la sustentación |
| El PC de la IA está apagado o sin red | El Hub degrada; respaldo con qwen2.5:3b en CPU en la VM |
| Let's Encrypt limita certificados para sslip.io | Pedir el certificado con tiempo; certificado de respaldo autofirmado para la demo |
| Claves o tokens en el repo | Todo por `.env` y Secrets; nada en Git (regla del proyecto) |
| Imágenes del registro del laboratorio no alcanzables | Publicarlas en Artifact Registry o en el registro de Gitea de la VM, con la misma firma de hoy |
| La puerta de seguridad depende de Gitea | Gitea corre también en la VM; reconstruir las corridas «ok» con `resembrar-puerta.sh` |
| Tiempo: congelamiento el 26 nov | Si T07 no está verde el 24 nov, se presenta en el laboratorio y la nube queda como evidencia parcial |

## Cómo se verifica

- Pruebas automáticas: humo del Hub y de los 3 sitios contra la dirección pública; prueba de degradación sin Ollama; `tofu plan` sin cambios tras el `apply`.
- Demo: pasos de [spec.md](spec.md#demo-de-cierre).

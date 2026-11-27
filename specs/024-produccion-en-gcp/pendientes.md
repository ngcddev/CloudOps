# Pendientes 024 · Nube GCP (corte del 20 nov 2026)

## Hecho (sin crear nada en GCP)

- Spec, plan y tareas.
- Módulo OpenTofu en `infra/tofu/gcp/`: red, subred, IP estática, cortafuegos (80 y 443 al mundo; 22 y 6443 solo desde tu IP), cuenta de servicio mínima, bucket de respaldo, VM `e2-standard-2` con k3s. `tofu validate` pasa con OpenTofu 1.13.2.
- Scripts `infra/gcp/apagar.sh` y `infra/gcp/encender.sh`.

## Te toca a ti (cuentas, claves y gasto)

1. **Conectar el MCP de Compute Engine** con el botón «Connect» de la tarjeta de conectores (pide tu cuenta de Google). Solo sirve para la VM; la infraestructura va por OpenTofu.
2. **T01:** crear un proyecto exclusivo para el Hub, vincular la facturación de prueba (300 USD) y activar la API de Compute Engine y de Cloud Storage.
3. **T02:** instalar `gcloud` e iniciar sesión (`gcloud auth application-default login`). Si prefieres no instalar nada, se puede correr en el contenedor `google/cloud-sdk`.
4. **T03:** crear el presupuesto con alertas a 10, 25 y 50 USD.
5. Crear `infra/tofu/gcp/terraform.tfvars` desde el `.example` con el ID del proyecto y tu IP pública (`ip_admin`).
6. Crear la cuenta de Tailscale y dar el visto bueno para instalarlo en el PC de la IA y en la VM (T08).

## Me toca a mí cuando lo anterior esté listo

- `tofu plan` y, con tu aprobación, `tofu apply` (T04, T05).
- Gitea, Argo CD y plataforma desde `hub-gitops` (T06).
- Overlay `nube` con sslip.io y cert-manager (T07).
- `OLLAMA_URL` por el túnel y prueba de degradación (T08, T09).
- Registro de imágenes y puerta de seguridad en la nube (T11).
- Respaldo a bucket y prueba de restauración (T12).
- Prueba de apagado y encendido (T13) y recreación con `destroy` y `apply` (T14).
- Runbook y anexo de evidencias (T15, T16).

## Riesgos abiertos

- Congelamiento el 26 nov: si T07 no está verde el 24 nov, se presenta en el laboratorio local.
- Los cortafuegos asumen una IP fija en tu casa o universidad; si cambia, hay que actualizar `ip_admin`.
- Ollama debe quedar en el PC escuchando solo en la interfaz de Tailscale, no en `0.0.0.0`.

# pipelines/ — la puerta de seguridad de los sitios (spec 006)

Cada versión nueva de un sitio de cliente (`v1.1`, `v2`…) pasa seis controles antes de poder publicarse. El Hub
solo deja **aprobar** una versión cuya corrida terminó en «ok» (`POST /api/change-requests/{id}/approve` responde
409 si no). Aquí vive todo lo que corre del lado de Gitea.

```
técnico ── git push (etiqueta vX) ──> repo del sitio en Gitea ──> Gitea Actions ──> runner
   secretos → construcción → vulnerabilidades → SBOM → firma (sube la imagen) → verificación
        │ cada paso: POST /api/pipeline-events (token propio)            │
        └────────────────────────────> Hub: corrida ok | fallo ──────────┘
Hub: aprobar solo con corrida ok · si falla, las solicitudes pendientes de esa versión pasan a «rechazada»
```

| Control | Herramienta (versión fija en `lib.sh`) | Falla si |
|---|---|---|
| `secretos` | Gitleaks | Hay un secreto en los commits nuevos de la versión (antes de construir nada) |
| `construccion` | `docker build` | La imagen no se construye |
| `vulnerabilidades` | Trivy (`CRITICAL`, `--ignore-unfixed`) | Hay una CVE crítica con arreglo disponible |
| `sbom` | Syft (SPDX JSON) | — (evidencia) |
| `firma` | Skopeo (sube) + Cosign (firma el digest) | No se puede subir o firmar |
| `verificacion` | Cosign verify con `cosign.pub` | La firma es inválida o falta |

La puerta revisa **seguridad, no salud**: no arranca la imagen. La `v2` rota de los sitios demo pasa los
controles a propósito (su falla la detecta el monitoreo del módulo 4).

## Archivos

| Archivo | Para qué |
|---|---|
| `puerta.yaml` | Workflow de Gitea Actions; se copia a `.gitea/workflows/` de cada repo de sitio |
| `puerta.sh` | Un paso por llamada (`inicio`, `secretos`, `construir`, `vulnerabilidades`, `sbom`, `firmar`, `verificar`, `fin`) |
| `reportar.sh` | Cuenta cada paso al Hub (`inicio`, `paso`, `fin`) |
| `lib.sh` | Versiones de las herramientas y funciones comunes |
| `cosign.pub` | Clave pública con la que se verifica cada firma (la privada solo existe en los secretos de Gitea) |
| `configurar-gitea.sh` | Organización, claves de Cosign, secretos y variables de Gitea Actions |
| `sembrar-repos-sitios.sh` | Crea los repos de los sitios desde `apps/` y sube sus versiones |
| `runner/` | Runner de Gitea Actions empaquetado (Dockerfile, config y compose) |
| `pruebas/simular-puerta.sh` | Prueba la puerta en una sola máquina, sin Gitea ni runner |

Los scripts viajan dentro de cada repo de sitio (`.gitea/puerta/`); por eso un cambio aquí no llega a los sitios
hasta que se vuelve a sembrar o se copia a mano.

## Puesta en marcha en el clúster

Orden (cada paso es repetible):

1. **Activar Actions en Gitea:** `GITEA__actions__ENABLED=true` ya está en `gitops/platform/gitea/deployment.yaml`;
   aplicar con `kubectl apply -k gitops/platform/gitea`.
2. **Token de la puerta en el Hub:** `bash gitops/hub/crear-secretos.sh` crea el Secret `hub-pipeline` y la API lo
   lee como `PIPELINE_TOKEN`.
3. **Claves, secretos y variables de Gitea:**
   ```bash
   GITEA_ADMIN_USER=forja-admin GITEA_ADMIN_PASSWORD='<contraseña>' bash pipelines/configurar-gitea.sh
   git add pipelines/cosign.pub && git commit -m "ci(006): clave pública de Cosign"
   ```
   Genera el par de Cosign (la privada va directo a los secretos de Gitea, nunca a un archivo) y carga
   `HUB_URL`, `HUB_PIPELINE_TOKEN`, `REGISTRY_USER`, `REGISTRY_PASSWORD`, `COSIGN_PRIVATE_KEY` y `COSIGN_PASSWORD`,
   más las variables `REGISTRY`, `REGISTRY_IP` y `DOCKER_NETWORK`. Por defecto sube imágenes con el usuario
   administrador; para algo más estricto crea un usuario `puerta-bot` con permiso de escritura en paquetes y pásalo
   en `REGISTRY_USER` / `REGISTRY_PASSWORD`.
4. **Runner** en un equipo con Docker **fuera del PC A** (tech-stack): ver abajo.
5. **Repos de los sitios:** `GITEA_ADMIN_USER=… GITEA_ADMIN_PASSWORD=… bash pipelines/sembrar-repos-sitios.sh`
   (con `--sin-etiquetas` no dispara la puerta). Cada versión que sube pasa por la puerta sola.

### Runner

```bash
GITEA_INSTANCE_URL=http://gitea.hub.local \
GITEA_RUNNER_REGISTRATION_TOKEN=<token> \
docker compose -f pipelines/runner/docker-compose.yml up -d --build
```

El token sale de Gitea (Administración del sitio → Actions → Runners → «Crear nuevo runner»). El runner corre los
pasos en su propio contenedor (etiqueta `puerta:host`) y lanza las herramientas como contenedores hermanos con el
Docker del equipo. Por eso la carpeta de trabajo (`/tmp/puerta-trabajo`) se monta con la **misma ruta** dentro y
fuera: el Docker del equipo resuelve los `-v <ruta>:/repo` de los scripts. El equipo necesita ver `gitea.hub.local`
y `hub.local` (entradas de `hosts` o `extra_hosts`). La primera corrida baja las imágenes de las herramientas y la
base de datos de Trivy; para la demo conviene dejarla caliente (corre una versión antes) y, sin internet,
definir `TRIVY_SKIP_DB_UPDATE=1`.

## Probar sin Gitea ni runner

```bash
HUB_URL=http://localhost:8000 HUB_PIPELINE_TOKEN=<PIPELINE_TOKEN del Hub> \
HUB_USUARIO=sofia@forjadigital.test HUB_PASSWORD=<contraseña> \
bash pipelines/pruebas/simular-puerta.sh [limpia|secreto|vulnerable|firma-ajena|todas]
```

Usa un registro local y claves desechables, y comprueba en el Hub lo que quedó de cada corrida. `SITE=consultorio`
prueba el sitio de dos imágenes.

## Límites conocidos

- **Quien puede subir a un repo de sitio también puede cambiar su workflow y sus scripts.** La puerta frena los
  errores y los descuidos, no a alguien con permiso de escritura que quiera saltársela. Mitigación: repos de sitios
  con escritura solo para la agencia, rama `main` protegida y revisión de los cambios en `.gitea/`.
- **La firma se verifica en el pipeline, no dentro del clúster** (ver tech-stack): un despliegue manual podría
  saltarla; por eso nadie despliega a mano (principio 3). Mejora futura: admission controller.
- **El tag `vX` del registro se podría sobrescribir** después de verificado. El Hub guarda el digest verificado
  (`image_digests`); fijar ese digest en `hub-gitops` es una mejora futura.
- El registro de Gitea del laboratorio va por HTTP: `REGISTRY_INSEGURO=1` (por defecto) desactiva TLS en Skopeo y
  usa `--allow-http-registry` en Cosign. Con certificado, ponerlo en `0`.
- Eventos con reportes muy grandes (SBOM de varios MB) viajan en el cuerpo de la petición; la API no los limita
  hoy.

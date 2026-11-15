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

- **El runner corre como root y con el socket de Docker montado.** Es una excepción consciente a la regla de
  «contenedores sin root» (necesita lanzar contenedores hermanos con el Docker del equipo) y equivale a dar root del
  equipo a quien pueda cambiar un workflow. Por eso va en un equipo de desarrollo aparte del PC A, solo para la
  agencia. Sus propios límites son `mem_limit` y `cpus` del compose; las herramientas que lanza no los heredan.
- **Credenciales en la lista de procesos.** La contraseña del registro (`--dest-creds`, `--registry-password`) y el
  token del Hub (`curl -H`) viajan como argumentos mientras corre cada herramienta: alguien con `ps` o
  `docker inspect` en el runner las lee. Mejora futura: archivos de autenticación temporales.
- **Bash 4 o superior** (`mapfile`): vale para el runner (Alpine) y Git Bash; el bash 3.2 de macOS no sirve.
- Los reportes de Gitleaks los escribe un contenedor como root dentro del espacio de trabajo: en un runner sin root,
  la limpieza puede fallar por permisos.
- Reintentar el evento `inicio` tras perder la respuesta puede dejar una corrida huérfana en «en curso»; no afecta a
  la puerta (vale la última) pero ensucia el historial.
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

## Pruebas del sitio y procedencia SLSA

- **Pruebas:** si el repositorio del sitio trae `backend/pytest.ini` (hoy, el consultorio), `puerta.sh construir` corre sus pruebas en un contenedor antes de
  construir; si fallan no se construye nada y el Hub registra el fallo en «construcción» con la salida de pytest.
- **Procedencia:** `puerta.sh firmar` adjunta a cada imagen una atestación SLSA v1 firmada con la misma clave (`cosign attest --type slsaprovenance1`) con el
  repositorio, la etiqueta, el **commit**, las herramientas con su versión y la corrida. `puerta.sh verificar` la comprueba (`cosign verify-attestation`) y
  exige que declare el commit de la versión. No certifica un nivel SLSA: demuestra qué commit produjo qué imagen y que no fue sustituida.
- **Simulación** (`pipelines/pruebas/simular-puerta.sh`, contra el Hub real y un registro local): escenarios `limpia`, `secreto`, `vulnerable`, `firma-ajena`,
  `procedencia` (otro commit) y `pruebas` (con `SITE=consultorio`). Pasan los seis.
- **Hallazgo real (14 nov):** `nginxinc/nginx-unprivileged:1.30-alpine` trae `brotli-libs` con una vulnerabilidad crítica ya corregida en Alpine y la puerta bloqueó
  la versión limpia; los Dockerfile de los sitios nginx llevan ahora `apk upgrade brotli-libs` (con la nota para quitarlo cuando la base lo traiga).
- **Imagen del Hub:** `backend/Dockerfile` tiene dos destinos: `dev` (con pytest y las pruebas, la usa `docker-compose.yml`) y `prod` (la etapa final, sin pruebas).
  `pipelines/pruebas/humo-hub-api.sh` comprueba que la de producción arranque, migre, siembre, corra sin root y no lleve pytest. La CI del Hub está en `.github/workflows/ci.yml`.

## Registro de hallazgos y VEX (spec 018)

La puerta frena las vulnerabilidades **críticas con arreglo** (`--ignore-unfixed`). Lo demás, las **altas** y lo que **no tiene arreglo**, no desaparece: `pipelines/hallazgos.yaml` es el registro de las decisiones
(explotabilidad, tratamiento, justificación y fecha de revisión, como máximo a 6 meses) y `pipelines/hallazgos.py` lo cruza con los reportes de Trivy. `bash pipelines/pruebas/hallazgos.sh` construye las imágenes
del Hub y del sitio de ejemplo, las escanea mostrando también lo que no tiene arreglo y falla si algo es **corregible**, no tiene **decisión** o la tiene **vencida**. Deja la tabla, el JSON y el VEX (OpenVEX) en
`evidencias/hallazgos/`, y el CI los guarda como artefacto. Con los hallazgos reales de hoy: 94 altas (47 por imagen de Python) sin arreglo, todas con regla vigente; el resto se corrigió actualizando paquetes.
El VEX es un documento de salida: Trivy no lo consume porque los productos se identifican por nombre de imagen y no por el digest que Trivy espera.


## SBOM atestado y escenarios de SCA/manifiestos (spec 018)

- **SBOM firmado:** `puerta.sh firmar` adjunta a cada imagen el SBOM SPDX como atestación (`cosign attest --type spdxjson`) y `verificar` la comprueba con la
  clave del Hub (`verify-attestation --type spdxjson`) y exige que traiga componentes.
- **Dependencias del sitio:** `puerta.sh vulnerabilidades` corre `trivy fs` sobre el repositorio del sitio (requirements.txt, package-lock.json…): una
  vulnerabilidad ALTA o CRÍTICA con arreglo publicado frena la puerta. `trivy config` revisa también los manifiestos de Kubernetes que traiga el repositorio.
- **Simulación:** se suman los escenarios `dependencia` (flask 0.12) y `manifiesto` (Deployment con `privileged` y `hostNetwork`); la puerta se detiene en los dos.

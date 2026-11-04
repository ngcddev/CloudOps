# Tareas 011 · Infraestructura como código

> Cada tarea: una acción con verbo · se comprueba en minutos · menos de un día · se integra sola.
> Rama por tarea: `feat/011-tNN-slug`. Poner el nombre de quien la toma entre corchetes.
>
> Fechas: módulo 4 del 24 oct al 3 nov (sustentación). Meta de esta spec: **30 oct**. No depende de la 008
> ni de la 009: se puede trabajar en paralelo desde hoy.

## Cómo repartirlo

| Carril | Tareas | Necesita el clúster | Puede empezar |
|---|---|---|---|
| Base | T01–T04 | Solo T04 | Ya |
| Módulo y clientes | T05–T09 | Sí | Cuando cierre T04 |
| Migración y pruebas | T10–T14 | Sí | Cuando cierre T09 |
| Despliegue en el VPS | T16–T17 | No (usa el VPS) | T16 ya; T17 cuando cierre T16 |

Una sola persona puede llevarlo todo; si son dos, una toma T01–T04 y otra prepara T05–T06 en papel mientras
tanto (las dos escriben en archivos distintos).

## Base

- [x] T01 · Crear `infra/` con `README.md`, `.gitignore` (`state/`, `.kubeconfig`, `*.tfvars`, `*.tfstate*`) y la estructura del plan — **Verifica:** `git status` no muestra `state/` ni `.kubeconfig` tras crearlos vacíos; el README explica qué gestiona y qué no. [ERIC]
- [x] T02 · Escribir `infra/tofu.sh`, que corre `tofu` o `terraform` en contenedor con versión fija, en la red `k3d-hub`, con el `kubeconfig` generado y `gitea.hub.local` resuelto — **Verifica:** `infra/tofu.sh tofu version` imprime 1.13.2 y `infra/tofu.sh terraform version` imprime 1.17.0. [ERIC]
- [x] T03 · Escribir `providers.tf` (kubernetes 3.4.0, gitea 0.8.1) y `variables.tf` (`gitea_token` sensible, `clients`) — **Verifica:** `tofu init` descarga ambos proveedores y `tofu validate` pasa. [ERIC]
- [x] T04 · Escribir `plans.tf` leyendo `seed/plans.json` y validar que cada cliente use un plan que exista — **Verifica:** `tofu plan` con un plan inexistente falla con un mensaje que lo nombra (CA-6, CA-8). [ERIC]

## Módulo y clientes

- [x] T05 · Crear `modules/client-env/overlay.tftpl` que reproduce el `kustomization.yaml` de los clientes existentes — **Verifica:** `terraform console` renderizando el módulo de `ferreteria` da un texto idéntico al de `gitops/clients/ferreteria/kustomization.yaml` salvo el comentario de cabecera. [ERIC]
- [x] T06 · Crear `modules/client-env/main.tf` con `gitea_repository_file` (`ignore_changes = [content]`) y la `Application` con el finalizador, con `depends_on` para el orden de borrado — **Verifica:** `tofu plan` de un cliente de prueba muestra solo esos dos recursos. [ERIC]
- [x] T07 · Escribir `clients.tf` con `for_each` sobre `var.clients` y `clients.auto.tfvars.json.example` — **Verifica:** el ejemplo con un cliente de prueba valida y `plan` lo crea. [ERIC]
- [x] T08 · Escribir `infra/client-new.sh` con las validaciones de nombre, plan y dominio — **Verifica:** nombre repetido, plan inexistente y dominio sin `.hub.local` terminan con un mensaje claro y sin tocar nada (CA-8). [ERIC]
- [x] T09 · Crear el cliente de prueba `prueba` de punta a punta y borrarlo — **Verifica:** su `Application` queda `Synced` y `Healthy`, el namespace tiene la cuota de su plan, y tras `destroy -target` el namespace desaparece (CA-1). [ERIC]

## Migración y pruebas

- [x] T10 · Importar los tres clientes existentes con `tofu import` y dejar `clients.auto.tfvars.json` con ellos — **Verifica:** el `plan` posterior no recrea nada y los sitios siguen respondiendo (CA-7). [ ]
- [x] T11 · Verificar el estado vacío: `apply` dos veces seguidas — **Verifica:** la segunda dice «0 to add, 0 to change, 0 to destroy» (CA-3). [ERIC]
- [x] T12 · Destruir y recrear El Tornillo — **Verifica:** el `plan` final sin diferencias, `Application` `Synced`/`Healthy` y `curl http://ferreteria.hub.local` responde 200 (CA-2). [ERIC]
- [x] T13 · Repetir T11 y T12 con `terraform` — **Verifica:** mismos resultados con el mismo código (CA-5). [ERIC]
- [x] T14 · Escribir `infra/pruebas/crear-cliente.sh` (crear, comprobar cuota y etiquetas contra `seed/plans.json`, destruir) y comprobar con `git grep` que no hay token ni estado en el repo — **Verifica:** el script termina en verde y `git grep -nE "GITEA_TOKEN=|tfstate"` no encuentra valores (CA-4, CA-6). [ERIC]

## Despliegue en el VPS del profesor

> El despliegue permanente va en el VPS que entregó el profesor (Dokploy, Docker Compose, x86_64, compartido con
> otros equipos), no en el clúster k3s del PC A. Estas tareas no crean ni tocan ese clúster: publican el Hub y los
> tres sitios con Compose. Procedimiento operativo: skill `desplegar-cloudops-vps`.

- [x] T16 · Escribir `docker-compose.dokploy.yml` en la raíz para el VPS: Hub (`db`, `api`, `web`) y los tres sitios de clientes en `v1`, sin `ports:` ni volúmenes de desarrollo, con `GITEA_*`, `ARGOCD_*` y `PROMETHEUS_URL` vacíos — **Verifica:** `docker compose -f docker-compose.dokploy.yml config` pasa con un `.env` de prueba, `git grep -n "ports:" docker-compose.dokploy.yml` no encuentra nada y `docker compose -f docker-compose.dokploy.yml up --build` en el PC deja `web`, `api` y los tres sitios respondiendo 200 detrás de un proxy (el VPS tiene ocupados 5432, 5434, 15432, 8080 y 8001). *Hecho el 2 nov 2026: `docker-compose.dokploy.yml` con `restart`, `mem_limit` y healthchecks. Con un `.env` de prueba, `config` pasa y sin variables falla nombrando la que falta; `grep "ports:"` no encuentra nada y ningún contenedor publica puertos del host. Con `up --build --wait` los 7 contenedores quedaron `Healthy`; desde la red del compose, `web`, `restaurante`, `ferreteria` y `consultorio-web` respondieron 200, `/health` de los tres sitios 200 con `v1`, `/api/auth/me` sin sesión 401 del Hub y el inicio de sesión de un usuario sembrado 200 (3 clientes sembrados). Memoria en reposo: api 101 MiB, db 62 MiB, el resto menos de 40 MiB. Falta (T17): «Isolated Deployment» en Dokploy y el despliegue real.* [ngcddev]
- [ ] T17 · Publicar el compose en el VPS por Dokploy (servicio `cloudops` con el repo público, rama `main`, variables en Dokploy y un dominio `sslip.io` por servicio público) y corregir la skill con lo que pase — **Verifica:** la consola y `/health` de los tres sitios responden 200, `/api/auth/me` sin sesión devuelve el 401 del Hub (no el de la `api` de otro equipo de la red compartida), el inicio de sesión con un usuario sembrado funciona, `db` queda `Healthy` y no se modificó ningún servicio de otros equipos. *Desplegado el 2 nov 2026 (proyecto `cloudops`, aislamiento activado, 4 dominios `sslip.io` en HTTP, variables en el Environment del servicio). Build de ~2 min; los 7 contenedores `Healthy`; la consola, `/` y `/health` de los tres sitios dieron 200 (`v1`), `/api/auth/me` sin sesión el 401 del Hub y un inicio de sesión con clave incorrecta 401; los contenedores de otros equipos siguieron arriba y la RAM pasó de 3,07 a 3,13 GiB. Falta: que alguien del equipo inicie sesión con un usuario sembrado en la consola del VPS (CA del inicio de sesión) y marcar la tarea.* [ngcddev]
- [ ] T18 · Conectar el Hub del VPS al clúster del PC A: `docker-compose.dokploy.yml` lee de las variables de Dokploy las URLs y los tokens de Gitea, Argo CD, Prometheus y Alertmanager (vacíos por defecto), y `gitops/pruebas/tuneles-vps.sh` abre túneles hacia Gitea, Argo CD y Prometheus, los prueba y arma esas variables — **Verifica:** sin variables, `docker compose -f docker-compose.dokploy.yml config` deja esas variables vacías como en la T16; con variables llegan al servicio `api`; el script termina con las tres URLs en «OK» y no imprime ningún token; y `HUB=<URL del Hub en el VPS> SITIO=http://restaurante.hub.local bash gitops/pruebas/demo-caso-restaurante.sh` cierra en verde. *Limitación aceptada: el clúster k3s, Argo CD, Gitea y la pila de monitoreo siguen en el PC A (el VPS es compartido, con unos 7,8 GB de RAM y sin acceso al servidor más que por Dokploy; no se midió si cabrían); los túneles son temporales, con una URL nueva en cada corrida, y mientras estén abiertos esos tres servicios son accesibles desde internet.* [ngcddev]

## Cierre

- [ ] T15 · Demo: crear Panadería El Trigo (plan Básico), mostrar Gitea, Argo CD y el namespace, recrear El Tornillo y repetir el comando de creación sin cambios — **Verifica:** todos los criterios de [spec.md](spec.md#criterios-de-aceptación). [ERIC ]

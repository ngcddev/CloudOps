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

Una sola persona puede llevarlo todo; si son dos, una toma T01–T04 y otra prepara T05–T06 en papel mientras
tanto (las dos escriben en archivos distintos).

## Base

- [x] T01 · Crear `infra/` con `README.md`, `.gitignore` (`state/`, `.kubeconfig`, `*.tfvars`, `*.tfstate*`) y la estructura del plan — **Verifica:** `git status` no muestra `state/` ni `.kubeconfig` tras crearlos vacíos; el README explica qué gestiona y qué no. [ERIC]
- [x] T02 · Escribir `infra/tofu.sh`, que corre `tofu` o `terraform` en contenedor con versión fija, en la red `k3d-hub`, con el `kubeconfig` generado y `gitea.hub.local` resuelto — **Verifica:** `infra/tofu.sh tofu version` imprime 1.13.2 y `infra/tofu.sh terraform version` imprime 1.17.0. [ERIC]
- [ ] T03 · Escribir `providers.tf` (kubernetes 3.4.0, gitea 0.8.1) y `variables.tf` (`gitea_token` sensible, `clients`) — **Verifica:** `tofu init` descarga ambos proveedores y `tofu validate` pasa. [ ]
- [ ] T04 · Escribir `plans.tf` leyendo `seed/plans.json` y validar que cada cliente use un plan que exista — **Verifica:** `tofu plan` con un plan inexistente falla con un mensaje que lo nombra (CA-6, CA-8). [ ]

## Módulo y clientes

- [ ] T05 · Crear `modules/client-env/overlay.tftpl` que reproduce el `kustomization.yaml` de los clientes existentes — **Verifica:** `terraform console` renderizando el módulo de `ferreteria` da un texto idéntico al de `gitops/clients/ferreteria/kustomization.yaml` salvo el comentario de cabecera. [ ]
- [ ] T06 · Crear `modules/client-env/main.tf` con `gitea_repository_file` (`ignore_changes = [content]`) y la `Application` con el finalizador, con `depends_on` para el orden de borrado — **Verifica:** `tofu plan` de un cliente de prueba muestra solo esos dos recursos. [ ]
- [ ] T07 · Escribir `clients.tf` con `for_each` sobre `var.clients` y `clients.auto.tfvars.json.example` — **Verifica:** el ejemplo con un cliente de prueba valida y `plan` lo crea. [ ]
- [ ] T08 · Escribir `infra/client-new.sh` con las validaciones de nombre, plan y dominio — **Verifica:** nombre repetido, plan inexistente y dominio sin `.hub.local` terminan con un mensaje claro y sin tocar nada (CA-8). [ ]
- [ ] T09 · Crear el cliente de prueba `prueba` de punta a punta y borrarlo — **Verifica:** su `Application` queda `Synced` y `Healthy`, el namespace tiene la cuota de su plan, y tras `destroy -target` el namespace desaparece (CA-1). [ ]

## Migración y pruebas

- [ ] T10 · Importar los tres clientes existentes con `tofu import` y dejar `clients.auto.tfvars.json` con ellos — **Verifica:** el `plan` posterior no recrea nada y los sitios siguen respondiendo (CA-7). [ ]
- [ ] T11 · Verificar el estado vacío: `apply` dos veces seguidas — **Verifica:** la segunda dice «0 to add, 0 to change, 0 to destroy» (CA-3). [ ]
- [ ] T12 · Destruir y recrear El Tornillo — **Verifica:** el `plan` final sin diferencias, `Application` `Synced`/`Healthy` y `curl http://ferreteria.hub.local` responde 200 (CA-2). [ ]
- [ ] T13 · Repetir T11 y T12 con `terraform` — **Verifica:** mismos resultados con el mismo código (CA-5). [ ]
- [ ] T14 · Escribir `infra/pruebas/crear-cliente.sh` (crear, comprobar cuota y etiquetas contra `seed/plans.json`, destruir) y comprobar con `git grep` que no hay token ni estado en el repo — **Verifica:** el script termina en verde y `git grep -nE "GITEA_TOKEN=|tfstate"` no encuentra valores (CA-4, CA-6). [ ]

## Cierre

- [ ] T15 · Demo: crear Panadería El Trigo (plan Básico), mostrar Gitea, Argo CD y el namespace, recrear El Tornillo y repetir el comando de creación sin cambios — **Verifica:** todos los criterios de [spec.md](spec.md#criterios-de-aceptación). [ ]

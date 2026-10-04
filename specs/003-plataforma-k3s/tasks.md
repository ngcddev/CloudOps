# Tareas 003 · Plataforma multi-cliente en k3s

> Cada tarea: una acción con verbo · se comprueba en minutos · menos de un día · se integra sola.
> Rama por tarea: `feat/003-tNN-slug`. Poner el nombre de quien la toma entre corchetes.
>
> Todo corre en el PC A (nodo único). Los manifiestos viven en `gitops/` (ver el [plan](plan.md#estructura-en-el-repo))
> y aquí se aplican **una sola vez** con `kubectl apply -k` para validar; desde la spec 005 los aplica Argo CD.
> Las cuotas salen de `seed/plans.json` (spec 000): no se inventan valores.

## Clúster y red

- [x] T01 · Instalar k3s de un nodo en el PC A y copiar el `kubeconfig` — **Verifica:** `kubectl get nodes` muestra el nodo `Ready` y `kube-system` tiene Traefik corriendo. [sebastian-debug]
- [x] T02 · Crear `gitops/platform/namespaces.yaml` con `hub`, `argocd`, `monitoring` y `gitea` — **Verifica:** `kubectl get ns` los lista. [sebastian-debug]
- [x] T03 · Apuntar `hub.local` y los subdominios (`restaurante`, `ferreteria`, `consultorio`, `gitea`) al PC A en `/etc/hosts` y documentarlo en `gitops/README.md` — **Verifica:** `curl -i http://restaurante.hub.local` responde el 404 de Traefik (aún sin sitio). [sebastian-debug]

## Registro de imágenes

- [x] T04 · Instalar Gitea en el namespace `gitea` con límites de memoria y volumen persistente, expuesto en `gitea.hub.local` — **Verifica:** abre en el navegador y permite crear la organización `forja-digital`. [sebastian-debug]
- [x] T05 · Configurar `registries.yaml` de k3s para que descargue del registro de Gitea por HTTP — **Verifica:** `crictl pull gitea.hub.local/forja-digital/<imagen>:v1` baja la imagen. [sebastian-debug]
- [x] T06 · Construir y publicar en el registro de Gitea las imágenes `restaurante`, `ferreteria`, `consultorio-web` y `consultorio-api` en `v1` y `v2` — **Verifica:** las 8 aparecen en la sección de paquetes de la organización. [sebastian-debug]

## Plantilla base de cliente (`gitops/clients/_base/`)

- [x] T07 · Escribir `namespace.yaml`, `resourcequota.yaml` y `limitrange.yaml` con las etiquetas de Pod Security `restricted` y los límites por defecto — **Verifica:** `kubectl kustomize gitops/clients/_base` genera los 3 recursos y `kubectl apply --dry-run=server` no da errores. [sebastian-debug]
- [x] T08 · Escribir `networkpolicy.yaml` con `default-deny` de entrada y permiso desde `kube-system` (Traefik) y `monitoring` — **Verifica:** `kubectl describe networkpolicy` muestra las dos reglas de entrada. [sebastian-debug]
- [x] T09 · Escribir `deployment.yaml`, `service.yaml` e `ingress.yaml` con `runAsNonRoot`, `allowPrivilegeEscalation: false`, `capabilities.drop: [ALL]`, `seccompProfile: RuntimeDefault` y probes en `/health` — **Verifica:** `kubectl kustomize` renderiza los 3 y el Deployment pasa `kubectl apply --dry-run=server` contra un namespace `restricted`. [sebastian-debug]

## Los 3 clientes (`gitops/clients/<cliente>/`)

- [x] T10 · Crear el overlay de La Sazón (`cliente-restaurante`, plan Premium 1000m/1Gi, `restaurante.hub.local`) y aplicarlo — **Verifica:** el sitio abre en su dirección y `kubectl describe quota -n cliente-restaurante` muestra 1000m/1Gi. [sebastian-debug]
- [ ] T11 · Crear el overlay de El Tornillo (`cliente-ferreteria`, plan Estándar 500m/512Mi, `ferreteria.hub.local`) y aplicarlo — **Verifica:** el sitio abre en su dirección y la cuota es 500m/512Mi. [ ]
- [ ] T12 · Crear el overlay de Dental Popayán (`cliente-consultorio`, plan Básico 250m/256Mi) con frontend, backend y la ruta `/api` — **Verifica:** el formulario de citas responde en `consultorio.hub.local` y los dos Pods caben en la cuota de 250m/256Mi. [ ]

## Pruebas de aislamiento y seguridad

- [ ] T13 · Probar el aislamiento de red con un Pod `busybox` en `cliente-restaurante` — **Verifica:** `wget` a la ferretería falla por tiempo de espera y a su propio sitio funciona (CA-3). [ ]
- [ ] T14 · Probar que Pod Security rechaza un contenedor con root — **Verifica:** `kubectl run root-test --image=nginx -n cliente-restaurante` es rechazado con el mensaje de política `restricted` (CA-4). [ ]
- [ ] T15 · Probar que un sitio con la verificación de salud fallando no recibe tráfico — **Verifica:** el Pod con la imagen `v2` (500 en `/health`) queda `0/1 Ready` y el Service no lo lista como endpoint (CA-6). [ ]

## El Hub en el clúster (`gitops/hub/`)

- [ ] T16 · Escribir el StatefulSet de PostgreSQL del Hub con volumen persistente y el Secret creado fuera del repo — **Verifica:** el Pod queda `Ready` y `pg_isready` responde; `git grep` no encuentra la contraseña en el repo. [ ]
- [ ] T17 · Publicar las imágenes de `api` y `web` del Hub y escribir sus Deployments, Services e Ingress en `hub.local` — **Verifica:** `http://hub.local` abre la consola con los 3 clientes sembrados. [ ]

## Cierre

- [ ] T18 · Demo: espacios y cuotas por plan, los 3 sitios y el Hub por su dirección, ferretería inalcanzable desde el restaurante y root rechazado — **Verifica:** todos los criterios de [spec.md](spec.md#criterios-de-aceptación). [ ]

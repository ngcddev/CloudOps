# Referencia de Kubernetes para el tutor del módulo 2

Material de estudio del tutor local (spec 017, T05): conceptos de Kubernetes del módulo 2 del diplomado, explicados corto y con el ejemplo de nuestro clúster. Cada sección `##` es un trozo que el tutor puede recuperar.

## Plano de control y nodos

El plano de control (control plane) decide qué debe correr y lo mantiene así: el servidor de API recibe todas las peticiones, etcd guarda el estado deseado, el scheduler elige el nodo de cada Pod y los controladores comparan lo que hay con lo que se pidió y corrigen la diferencia. Los nodos (workers) ejecutan los Pods; en cada uno corren el kubelet, que arranca los contenedores y reporta su salud, y kube-proxy, que enruta el tráfico de los Services. Kubernetes es declarativo: se describe el estado deseado y los controladores lo reconcilian. En nuestro laboratorio k3s corre plano de control y nodo en un solo nodo.

## Pod

El Pod es la unidad mínima que Kubernetes programa: uno o más contenedores que comparten red (una sola IP y un espacio de puertos) y volúmenes. Los Pods son efímeros: si uno muere, no se repara, se reemplaza por otro con otra IP. Por eso casi nunca se crean a mano: los crea un controlador como un Deployment. Los contenedores de un Pod se programan juntos en el mismo nodo.

## Deployment y ReplicaSet

Un Deployment declara cuántas réplicas de un Pod quiere y con qué imagen, y gestiona sus actualizaciones. Por debajo crea un ReplicaSet, que es quien mantiene el número de Pods; al cambiar la imagen, el Deployment crea un ReplicaSet nuevo y retira el viejo. La estrategia RollingUpdate cambia los Pods poco a poco para no cortar el servicio; la estrategia Recreate apaga todos los Pods viejos antes de arrancar los nuevos y deja el servicio sin respuesta unos segundos. Nuestros sitios de clientes usan Recreate para que una versión rota sí tumbe el sitio y se detecte.

## StatefulSet

El StatefulSet es el controlador para aplicaciones con estado, como una base de datos. A diferencia del Deployment, da a cada Pod un nombre estable y ordenado (postgres-0), arranca y detiene los Pods en orden y asigna a cada uno su propio volumen persistente que lo sigue si el Pod se recrea. En nuestro clúster PostgreSQL del Hub corre como StatefulSet.

## DaemonSet

El DaemonSet asegura que corra una copia de un Pod en cada nodo (o en los nodos que cumplan un selector). Se usa para agentes que deben estar en todos los nodos: recolectores de logs, agentes de monitoreo y complementos de red. Cuando se agrega un nodo, el DaemonSet le crea su Pod automáticamente.

## Service

El Service da una dirección estable (IP virtual y nombre DNS) a un conjunto de Pods elegidos por etiquetas, y reparte el tráfico entre los que están Ready. Como los Pods cambian de IP, los clientes hablan con el Service y no con los Pods. El tipo ClusterIP es interno al clúster; NodePort abre un puerto en cada nodo; LoadBalancer pide un balanceador externo. Un Pod que no pasa su readiness probe sale de la lista de destinos del Service.

## Ingress y Gateway API

El Ingress define reglas HTTP para exponer Services al exterior: qué dirección (host) y qué ruta van a qué Service. Un Ingress no hace nada solo: lo cumple un controlador de Ingress, que en k3s es Traefik. La Gateway API es la evolución del Ingress, con roles separados para quien administra el balanceador y quien publica las rutas. En nuestro clúster cada sitio tiene un Ingress con su dirección, por ejemplo ferreteria.hub.local.

## ConfigMap y Secret

El ConfigMap guarda configuración no sensible (variables, archivos) separada de la imagen del contenedor, y se consume como variables de entorno o como archivos montados. El Secret guarda datos sensibles como contraseñas y tokens; por defecto sus valores solo van codificados en base64, no cifrados, así que hay que restringir quién puede leerlos con RBAC y no guardarlos en Git. En nuestro proyecto los Secrets se crean con scripts del clúster y nunca viven en el repositorio.

## Volúmenes, PersistentVolume y StorageClass

Un volumen da almacenamiento a un Pod; un emptyDir vive solo lo que vive el Pod. Para datos que deben sobrevivir se usa un PersistentVolume (PV), que es el almacenamiento real, y un PersistentVolumeClaim (PVC), que es la petición de un Pod por cierto tamaño y modo de acceso. La StorageClass describe cómo se crea ese almacenamiento por demanda (aprovisionamiento dinámico): al crear un PVC, la StorageClass genera el PV. k3s trae la StorageClass local-path, que usa el disco del nodo. El modo ReadWriteOnce permite montar el volumen en lectura y escritura desde un solo nodo.

## Job y CronJob

Un Job ejecuta uno o más Pods hasta que terminan con éxito, para tareas puntuales como una migración o un respaldo. Un CronJob crea Jobs según un calendario con sintaxis cron. En nuestro clúster el respaldo de PostgreSQL y los de Gitea y Argo CD son CronJobs que corren de madrugada.

## Namespaces

Los namespaces dividen un clúster en espacios lógicos de nombres: permiten agrupar recursos, aplicar cuotas, políticas de red y permisos por separado. No son aislamiento de seguridad por sí solos; hay que combinarlos con RBAC y NetworkPolicy. En nuestro clúster cada cliente tiene su namespace (cliente-restaurante, cliente-ferreteria) con su cuota de CPU y memoria.

## RBAC

RBAC (control de acceso basado en roles) decide quién puede hacer qué sobre qué recursos. Un Role define permisos (verbos como get, list, create sobre recursos) dentro de un namespace; un ClusterRole lo hace para todo el clúster. Un RoleBinding o ClusterRoleBinding asigna ese rol a un usuario, grupo o ServiceAccount. La ServiceAccount es la identidad con la que corre un Pod. Se aplica el principio de menor privilegio: dar solo los verbos necesarios.

## Requests y limits

Las requests son los recursos que el scheduler reserva para un contenedor al decidir en qué nodo ponerlo; los limits son el máximo que puede usar. Si un contenedor pasa su límite de memoria, Kubernetes lo termina (OOMKilled); si pasa el de CPU, lo ralentiza. Un ResourceQuota limita el total de recursos de un namespace y un LimitRange da valores por defecto a los contenedores que no declaran los suyos. Un HPA por CPU solo funciona si el Pod declara requests de CPU.

## Probes: liveness, readiness y startup

Las probes son comprobaciones de salud que hace el kubelet. La liveness probe decide si hay que reiniciar el contenedor porque quedó colgado. La readiness probe decide si el Pod puede recibir tráfico: si falla, el Service lo saca de sus destinos pero no lo reinicia. La startup probe da tiempo extra a aplicaciones lentas al arrancar antes de empezar las otras dos. Nuestros sitios usan /health como probe: una versión rota que responde 500 nunca queda Ready.

## Autoscaling

El HorizontalPodAutoscaler (HPA) cambia el número de réplicas de un Deployment según métricas, normalmente el uso de CPU frente a un objetivo, y necesita metrics-server para leerlas. El VerticalPodAutoscaler ajusta requests y limits en lugar de réplicas, y el Cluster Autoscaler agrega o quita nodos. El HPA tiene un mínimo y un máximo de réplicas, y una ventana de estabilización para no reducir réplicas por un pico corto.

## NetworkPolicy

Por defecto todos los Pods de un clúster pueden hablar entre sí. Una NetworkPolicy restringe el tráfico a los Pods que selecciona, por entrada (ingress) o salida (egress), según etiquetas de Pods, de namespaces o rangos de IP. Una política que deniega todo y luego permite lo necesario es el patrón recomendado. Solo funciona si el complemento de red la implementa. En nuestro clúster cada cliente deniega toda entrada salvo Traefik, el monitoreo y sus propios Pods, así un sitio no alcanza al de otro cliente.

## Pod Security Admission

Pod Security Admission aplica por namespace los perfiles de seguridad de Pods: privileged, baseline y restricted. El perfil restricted exige correr sin root, sin escalada de privilegios, sin capacidades de Linux y con perfil seccomp, y rechaza los Pods que no cumplen. Se activa con etiquetas del namespace (enforce, audit y warn). Nuestros namespaces de clientes y el del Hub usan restricted.

## Alta disponibilidad

La alta disponibilidad se logra con varias réplicas repartidas en varios nodos, probes que retiran los Pods enfermos, un PodDisruptionBudget que limita cuántos Pods pueden faltar a la vez durante mantenimientos, y un plano de control con varias réplicas. Un clúster de un solo nodo, como nuestro laboratorio, no es alta disponibilidad: si el nodo cae, cae todo.

## Rollout y rollback

Cada cambio al Deployment crea una revisión; kubectl rollout status sigue el avance y kubectl rollout undo vuelve a la revisión anterior. En GitOps el rollback se hace en Git: se vuelve a poner la versión anterior en el repositorio y el controlador la aplica. En nuestro caso el Hub escribe ese commit de rollback en hub-gitops y Argo CD lo despliega.

## Helm

Helm es el gestor de paquetes de Kubernetes. Un chart empaqueta plantillas de manifiestos con valores configurables (values.yaml); helm template renderiza los manifiestos sin instalar y helm install crea un release en el clúster, versionado para poder volver atrás. Helm sirve para empaquetar y distribuir una aplicación con variantes por valores. En nuestro repositorio el chart sitio-cliente produce los mismos objetos que Kustomize.

## Kustomize

Kustomize personaliza manifiestos YAML sin plantillas: una base común y overlays que la parchean (cambian imagen, réplicas, host o cuota) para cada ambiente o cliente. Viene integrado en kubectl (kubectl kustomize, kubectl apply -k). En nuestro repositorio la base clients/_base la comparten todos los clientes y cada overlay cambia su namespace, su host, su cuota y su imagen.

## GitOps y Argo CD

GitOps usa Git como fuente de verdad del estado deseado: lo que está en el repositorio es lo que debe correr, y un controlador lo sincroniza con el clúster. Argo CD compara continuamente el clúster con Git y marca la aplicación como Synced u OutOfSync. Con selfHeal activo corrige solo el drift, es decir, los cambios hechos a mano en el clúster; con prune borra del clúster lo que ya no está en Git. La configuración se separa del código en su propio repositorio y los cambios se revisan antes de entrar.

## Platform Engineering y Backstage

Platform Engineering construye plataformas internas con caminos estandarizados (golden paths) y autoservicio para que los equipos entreguen sin conocer toda la infraestructura. Backstage es un portal de desarrollador: su catálogo registra componentes y sus dueños, las plantillas del scaffolder crean proyectos nuevos y TechDocs publica documentación como código. En nuestro clúster Backstage lista los sitios de los clientes, ofrece la plantilla Sitio de cliente y publica la documentación de la plataforma.

## Clúster de aprendizaje y clúster de producción

Un clúster de aprendizaje (kind, minikube, k3d) sirve para practicar: un nodo, sin alta disponibilidad, sin garantías de datos. Un clúster de producción exige varios nodos, plano de control replicado, respaldos probados, control de acceso, políticas de red y de seguridad, monitoreo y un plan de actualización. El diplomado busca pasar de hacer que funcione a justificar cómo se despliega, actualiza, monitorea, recupera y protege un servicio.

## Cómo lo hacemos en el CloudOps Client Hub

El Hub no habla con Kubernetes: solo escribe commits en el repositorio hub-gitops y Argo CD aplica los cambios. Cada cliente tiene su namespace con Pod Security restricted, cuota por plan, NetworkPolicy y un overlay de Kustomize sobre una base común. Un ApplicationSet crea la Application de cada cliente nuevo al ver su carpeta. Los cambios pasan por una puerta de seguridad antes de aprobarse, el monitoreo abre un incidente si un sitio falla 30 segundos y el rollback devuelve la versión estable.

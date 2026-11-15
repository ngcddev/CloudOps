# 017 · Cierre del módulo 2 (Kubernetes, GitOps y Platform Engineering)

> **Acciona:** Equipo de Sistemas · **Módulo:** 2 · **Depende de:** 003, 005, 011, 016 · **Estado:** En curso

## Qué y por qué

Al contrastar el repositorio con el temario del módulo 2 del diplomado quedaron brechas concretas. Esta spec las cierra una por una, cada una con su prueba en el clúster.
El módulo pesa el 15 % de la nota y alimenta el 20 % del proyecto (Kubernetes, GitOps e IaC).

## Criterios de aceptación

- [x] CA-1. Una prueba provoca *drift* a propósito (escalar a mano, borrar un recurso) y muestra a Argo CD detectándolo y corrigiéndolo desde Git.
- [x] CA-2. Backstage tiene una plantilla («golden path») para dar de alta un sitio de cliente y la documentación como código (TechDocs) se ve en el portal.
- [x] CA-3. Existe un ambiente `staging` y una versión se promueve de `staging` a producción por un cambio en Git.
- [x] CA-4. Un chart de Helm empaqueta el sitio de un cliente y su `helm template` coincide con lo que produce Kustomize.
- [x] CA-5. Un tutor de IA responde sobre la documentación de Kubernetes y los lineamientos del curso, con la matriz de aciertos, omisiones y alucinaciones.
- [ ] CA-6. Menores: ServiceAccounts y roles por aplicación, un `AppProject` de Argo CD con límites y Alloy como DaemonSet.

## Fuera de alcance

- Kubeflow (opcional en el temario) y un segundo clúster.

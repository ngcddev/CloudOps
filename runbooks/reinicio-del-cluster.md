# Reinicio del clúster tras apagar el equipo

**Síntoma:** al encender el equipo `kubectl` no responde o el nodo `k3d-hub-server-0` reinicia sin parar («failed to find interface with specified node ip»).

## Diagnóstico

El clúster usa la red Docker `172.30.0.0/24` y el nodo debe quedar en `172.30.0.3` (el balanceador, en `.2`). Si otro contenedor de esa red toma la `.3`, k3s muere.
`docker network inspect k3d-hub` muestra qué IP tiene cada contenedor.

## Acción

1. Arrancar Docker Desktop.
2. Parar todo y arrancar **en este orden**, con unos segundos entre cada uno: `k3d-hub-serverlb`, `k3d-hub-server-0`, `estado-remoto`, `runner-runner-1`.
3. Revisar el puerto del balanceador (`docker port k3d-hub-serverlb 6443`) y actualizar el kubeconfig si cambió.
4. Levantar el Hub de desarrollo: `docker compose up -d`.
5. Si el estado de la demo quedó sucio: `bash demo/reiniciar-cluster.sh` (con `GITEA_USER` y `GITEA_PASSWORD`).

## Verificación

`kubectl get nodes` muestra `Ready`, `kubectl get applications -n argocd` todo `Synced` y `Healthy`, y los sitios responden en `/health`.

## Cuándo escalar

El nodo sigue sin arrancar con la IP correcta: guardar `docker logs k3d-hub-server-0` y recrear el clúster con los manifiestos de `gitops/` (todo el estado está en Git).

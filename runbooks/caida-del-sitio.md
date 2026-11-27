# Caída del sitio de un cliente

**Síntoma:** alerta `SitioCaido` (el `/health` no responde 2xx durante 30 s) y un incidente P1 abierto en el Hub.

## Diagnóstico

1. En el Hub, abrir el incidente: muestra la hora real de la caída, el último cambio publicado y los enlaces a los registros en Grafana y al commit en Gitea.
2. Ver el Pod: `kubectl -n cliente-<cliente> get pods` y `kubectl -n cliente-<cliente> describe pod -l app=web`.
3. ¿Hubo una publicación en los últimos minutos? Si sí, es casi seguro la causa: ir a [rollback.md](rollback.md).
4. Si no hubo publicación: `kubectl -n cliente-<cliente> logs deploy/web --tail=50` (Nginx) y revisar el Ingress y la NetworkPolicy (`kubectl -n cliente-<cliente> get ingress,networkpolicy`).

## Acción

- Causa = publicación mala: rollback desde el incidente (botón «Rollback») o ver [rollback.md](rollback.md).
- Pod en `CrashLoopBackOff` sin publicación nueva: `kubectl -n cliente-<cliente> rollout restart deploy/web` y vigilar. Si vuelve a caer, es un problema de la imagen: rollback.
- Un cambio hecho a mano en el clúster: Argo CD lo revierte solo (`selfHeal`); no hace falta tocarlo.

## Verificación

`curl -s http://<cliente>.hub.local/health` devuelve `{"status":"ok",...}`, la alerta se resuelve y el Hub deja el incidente listo para cerrar. Cerrarlo con la nota de qué pasó.

## Cuándo escalar

Más de 15 minutos sin recuperar, o caen varios sitios a la vez (apunta al nodo: ver [reinicio-del-cluster.md](reinicio-del-cluster.md)).

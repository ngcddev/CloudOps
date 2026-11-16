# Contenedor en bucle de reinicios

**Síntoma:** la alerta `ContenedorEnBucle`: un contenedor del Hub, de un cliente o del monitoreo arrancó 3 veces o más en 15 minutos. En `kubectl get pods` el Pod muestra `RESTARTS` subiendo y `CrashLoopBackOff`.

## Diagnóstico

1. La alerta dice el namespace, el Pod y el contenedor. `kubectl -n <namespace> get pods` confirma los reinicios.
2. `kubectl -n <namespace> describe pod <pod>`: en «Last State» el motivo (`OOMKilled`, `Error`) y el código de salida; en «Events», si fallan las sondas (`Liveness probe failed`, `Startup probe failed`).
3. `kubectl -n <namespace> logs <pod> --previous`: lo último que dijo el contenedor antes de morir.
4. ¿Cambió algo justo antes? Una publicación nueva del sitio o del Hub, o una imagen que no coincide con el manifiesto.

## Acción

- **`OOMKilled`:** se queda sin memoria; seguir [saturacion.md](saturacion.md).
- **Falla una sonda:** la imagen no responde donde el manifiesto la espera (por ejemplo, una ruta nueva en `gitops/hub/api.yaml` con una imagen que aún no la tiene). Publicar la imagen correcta o volver el manifiesto a la versión anterior por Git.
- **Error de la aplicación:** corregirlo y publicar una versión nueva, o volver a la anterior: ver [rollback.md](rollback.md) para un sitio de cliente.
- **Arranca y muere por la base o por un Secret que falta:** ver [caida-del-hub.md](caida-del-hub.md).

Nada se arregla a mano en el clúster: Argo CD revierte lo que no esté en Git.

## Verificación

`RESTARTS` deja de subir y el Pod queda `Running` y listo. La alerta se apaga sola cuando pasan 15 minutos sin un tercer arranque.

## Cuándo escalar

El contenedor sigue muriendo con la versión anterior: guardar la salida de `describe` y de `logs --previous` y revisar el manifiesto en `gitops/` contra el último cambio.

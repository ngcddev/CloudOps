# Caída del Hub (API o web)

**Síntoma:** la alerta `HubCaido` (el API o la web del Hub no responden durante un minuto), o `http://hub.local` no carga o la consola muestra errores. La etiqueta `componente` de la alerta dice cuál: `api` o `web`.

## Diagnóstico

1. `kubectl -n hub get pods`: ¿el Pod del componente está `Running` y `1/1`? `CrashLoopBackOff` o `0/1` ya dicen por dónde seguir.
2. El API responde 503 en `/health` cuando no hay base. Mirar también `postgres-0` en la misma lista: si no está listo, el problema es la base y no el API.
3. `kubectl -n hub logs deploy/api --tail=50` (o `deploy/web`): el último error antes de caer.
4. ¿Hubo una publicación del Hub hace poco? `kubectl -n argocd get applications` muestra si `hub` está `Synced` y `Healthy`.
5. El API no se reinicia solo cuando cae la base (su sonda de vida es `/livez`): sale del servicio y vuelve a estar listo cuando la base contesta.

## Acción

- **La base está caída o reiniciando:** esperar a que `postgres-0` vuelva; el API se recupera solo. Si la base no vuelve o está dañada, seguir [respaldo-y-restauracion.md](respaldo-y-restauracion.md).
- **Una publicación del Hub salió mal:** volver a la versión anterior en Git (`gitops/hub/`) y promoverla con `bash gitops/sincronizar-hub-gitops.sh`; Argo CD la aplica. Para el procedimiento general de volver atrás, ver [rollback.md](rollback.md).
- **El equipo se reinició o apagó:** seguir [reinicio-del-cluster.md](reinicio-del-cluster.md).
- **El Pod se queda sin memoria o va al límite:** ver [saturacion.md](saturacion.md).

Nada se arregla a mano en el clúster: Argo CD revierte lo que no esté en Git.

## Verificación

`kubectl -n hub get pods` con todo `Running` y `1/1`; `kubectl -n hub exec deploy/api -- python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/health').status)"` imprime `200`; y la alerta `HubCaido` desaparece de Alertmanager.

## Cuándo escalar

El Pod sigue sin arrancar con la versión anterior publicada, o la base no vuelve ni con el respaldo: guardar `kubectl -n hub describe pod` y los registros del contenedor, y recrear el Hub desde los manifiestos de `gitops/hub/`.

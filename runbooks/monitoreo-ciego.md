# Monitoreo ciego

**Síntoma:** la alerta `MonitoreoCiego` (Blackbox dejó de sondear o no hay objetivos), o la alerta `Watchdog` **no aparece** en Alertmanager. Con el monitoreo ciego `SitioCaido` no se dispara aunque todos los sitios estén caídos, y nadie recibe un aviso de que el aviso falló.

## Diagnóstico

1. `kubectl -n monitoring get pods`: ¿`blackbox`, `prometheus` y `alertmanager` están `Running` y `1/1`?
2. Objetivos de Prometheus: `kubectl -n monitoring port-forward svc/prometheus 9090` y abrir `http://localhost:9090/targets`. Los jobs `sitios` y `hub` deben estar en `UP`.
3. Latido: `kubectl -n monitoring port-forward svc/alertmanager 9093` y abrir `http://localhost:9093`. `Watchdog` debe estar siempre activa; si no está, Prometheus no llega a Alertmanager o no evalúa las reglas.
4. `kubectl -n monitoring describe pod` del que falla: ¿`OOMKilled`? Prometheus, Loki y Alloy ya han reiniciado por memoria.

## Acción

- **Un Pod del monitoreo está caído o reinicia:** ver por qué (registros y `describe`). Si es memoria, subir el límite por Git (ver [saturacion.md](saturacion.md)); si es una publicación mala, volver a la versión anterior por Git.
- **No hay objetivos en `sitios`:** los sitios se descubren por la anotación `hub/probe` de su Service; revisar que siga y que Prometheus tenga permiso para leer los Services.
- **Mientras tanto,** comprobar a mano el `/health` de los sitios: `curl http://restaurante.hub.local/health` (y los demás clientes).

Importante: estas alertas se ven en Alertmanager y en Prometheus, pero **no avisan a nadie**: el laboratorio no tiene un canal externo. El latido de `Watchdog` es una comprobación manual hasta que haya uno (un servicio fuera del clúster que dé la alarma si deja de recibirlo).

## Verificación

Los jobs `sitios` y `hub` en `UP` en `/targets`, `Watchdog` activa en Alertmanager y `MonitoreoCiego` desaparecida.

## Cuándo escalar

Prometheus no arranca (volumen lleno o dañado) o Alertmanager no recibe las alertas con todo en `Running`: guardar los registros y recrear el monitoreo desde `observability/` en Git; el historial de métricas se pierde si se recrea el volumen.
